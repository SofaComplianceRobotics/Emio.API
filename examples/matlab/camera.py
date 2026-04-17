from multiprocessing.sharedctypes import SynchronizedArray
from multiprocessing.synchronize import Event

import cv2 as cv
import numpy as np
from emioapi._depthcamera import DepthCamera

import params as prm


# ------------------------------------------------------------------------------
# Process
# ------------------------------------------------------------------------------
def process_camera(shared_markers_pos: SynchronizedArray,
                   event_frame: Event,
                   event_measure: Event) -> None:
    """Main camera loop: grab frames, track markers, and update shared state.

    Sets ``event_frame`` at each new frame and ``event_measure`` once the
    marker positions are written to ``shared_markers_pos``.
    Stops when the user presses ``q``.

    Args:
        shared_markers_pos: Shared memory array written with marker positions.
        event_frame: Event set at each new camera frame.
        event_measure: Event set once marker data is ready.
    """
    camera = setup_camera()
    pos = np.zeros((prm.ny, 1))

    while True:
        # get frame from camera
        ret = camera.get_frame()
        event_frame.set()
        if ret:
            pos = process_frame(camera, pos)

        with shared_markers_pos.get_lock():
            shared_markers_pos[:] = pos.flatten()
        event_measure.set()

        k = cv.waitKey(1)
        if k == ord('q'):
            camera.quit()
            break

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def setup_camera() -> DepthCamera:
    """Initialise and open the depth camera from ``params``.

    Returns:
        A configured, open DepthCamera instance.
    """
    camera = DepthCamera(
        show_video_feed=True,
        tracking=True,
        compute_point_cloud=False
        )
    camera.set_fps(prm.fps)
    camera.set_depth_min(0)
    camera.set_depth_max(1000)
    camera.open()
    return camera

# -------------------------------------------------------
def process_frame(camera: DepthCamera, last_pos: np.ndarray) -> np.ndarray:
    """Extract marker positions from the current frame.

    Returns ``last_pos`` unchanged if the expected number of markers is not
    detected.

    Args:
        camera: An open, tracking-enabled DepthCamera instance.
        last_pos: Position array returned on detection failure.

    Returns:
        Marker positions as a column vector, shape ``(ny, 1)``.
    """
    camera.process_frame()
    if len(camera.trackers_pos) == prm.nb_markers:
        if prm.side == "top":
            pos = np.array(camera.trackers_pos).reshape(-1, 3).copy()
            pos = pos.astype(np.float64)
            return pos
        elif prm.side == "front":
            p = np.array(camera.trackers_camera).reshape(prm.nb_markers, 3).copy()
            p = p.astype(np.float64)
            p = pixel_to_mm(p, prm.depth)
            p = camera_to_sofa_order(p)
            return p.reshape((-1, 1))
    return last_pos

# -------------------------------------------------------
def pixel_to_mm(points: np.ndarray, depth: float) -> np.ndarray:
    """Project pixel coordinates to millimetres using pinhole intrinsics.

    Args:
        points: Tracker positions in pixels, shape ``(n, 3)``.
        depth: Fixed depth in mm used for the projection.

    Returns:
        Projected points in mm, shape ``(n, 3)``.
    """
    ppx, ppy = 319.475, 240.962
    fx, fy = 382.605, 382.605
    points[:, 0] = ((points[:, 0] - ppx) / fx) * depth
    points[:, 1] = ((points[:, 1] - ppy) / fy) * depth
    points = np.column_stack((points[:, 2], -points[:, 1], points[:, 0]))
    return points.copy()

# -------------------------------------------------------
def camera_to_sofa_order(points: np.ndarray) -> np.ndarray:
    """Reorder markers by ascending y-coordinate (SOFA convention).

    Args:
        points: Marker positions, shape ``(nb_markers, 3)``.

    Returns:
        Reordered positions as a flat array.
    """
    i_sorted_y = sorted(range(prm.nb_markers), key=lambda i: points[i, 1])
    return points[i_sorted_y].flatten()
