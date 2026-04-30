from multiprocessing.sharedctypes import SynchronizedArray
from multiprocessing.synchronize import Event

import cv2 as cv
import numpy as np
from emioapi.emiocamera import EmioCamera

import params as prm


# ------------------------------------------------------------------------------
# Process
# ------------------------------------------------------------------------------
def process_camera(shared_markers_pos: SynchronizedArray,
                   event_frame: Event,
                   event_measure: Event,
                   args) -> None:
    """Main camera loop: grab frames, track markers, and update shared state.

    Sets ``event_frame`` at each new frame and ``event_measure`` once the
    marker positions are written to ``shared_markers_pos``.
    Stops when the user presses ``q``.

    Args:
        shared_markers_pos: Shared memory array written with marker positions.
        event_frame: Event set at each new camera frame.
        event_measure: Event set once marker data is ready.
        args: Parsed command-line arguments, used for camera configuration
    """
    ny = 3 * args.nb_markers
    camera = setup_camera(args.fps)
    pos = np.zeros((ny, 1))

    while True:
        # get frame from camera
        ret = camera.get_frame()
        event_frame.set()
        if ret:
            pos = process_frame(camera, pos, args.nb_markers, args.side, args.sort)

        with shared_markers_pos.get_lock():
            shared_markers_pos[:] = pos.flatten()
        event_measure.set()

        k = cv.waitKey(1)
        if k == ord('q'):
            camera.close()
            break

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def setup_camera(fps) -> EmioCamera:
    """Initialise and open the depth camera.

    Args:
        fps: Desired camera framerate in frames per second.

    Returns:
        A configured, open DepthCamera instance.
    """
    camera = EmioCamera(
        show=True,
        track_markers=True,
        compute_point_cloud=False
        )
    camera.fps = fps
    camera.depth_min = 0
    camera.depth_max = 1000
    camera.open()
    return camera

# -------------------------------------------------------
def process_frame(camera: EmioCamera, 
                  last_pos: np.ndarray, 
                  nb_markers: int, 
                  side: str, 
                  sort: str) -> np.ndarray:
    """Extract marker positions from the current frame.

    Returns ``last_pos`` unchanged if the expected number of markers is not
    detected.

    Args:
        camera: An open, tracking-enabled DepthCamera instance.
        last_pos: Position array returned on detection failure.
        nb_markers: Expected number of markers to track.
        side: Camera side, one of "top", "front", or "plan".
        sort: Sorting method for front camera, "y" or "z".

    Returns:
        Marker positions as a column vector, shape ``(ny, 1)``.
    """
    camera.process_frame()
    if len(camera.trackers_pos) == nb_markers:
        if side == "top":
            pos = np.array(camera.trackers_pos).reshape(nb_markers, 3).copy()
            pos = pos.astype(np.float64)
            return pos

        elif side == "front":
            p = np.array(camera.trackers_pos_image).reshape(nb_markers, 3).copy()
            p = p.astype(np.float64)
            p = pixel_to_mm(p, prm.depth)
            p = camera_to_sofa_order(p, nb_markers, sort)
            return p.reshape((-1, 1))

        elif side == "plan":
            trackers_projected = []
            for pixel_pos in camera.trackers_pos_image:
                result = camera._camera.position_estimator.camera_image_to_simulation_plane_intersection(
                    pixel_pos[0],pixel_pos[1],prm.plane_n, prm.plane_d)
                trackers_projected.append(result)
            p = np.array(trackers_projected).reshape(nb_markers, 3).copy()
            p = p.astype(np.float64)
            p = camera_to_sofa_order(p, nb_markers, sort)
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
    points += prm.front2top_offset
    points = np.column_stack((points[:, 2], -points[:, 1], points[:, 0]))
    return points.copy()

# -------------------------------------------------------
def camera_to_sofa_order(points: np.ndarray, 
                         nb_markers: int, 
                         sort: str) -> np.ndarray:
    """Reorder markers by ascending coordinate.

        Args:
            points: Marker positions, shape ``(nb_markers, 3)``.
            nb_markers: Number of markers.
            sort: Axis to sort by, "y" or "z".

        Returns:
            Reordered positions as a flat array.
        """
    if sort == "z":
        i_sorted_z = sorted(range(nb_markers), key=lambda i: points[i, 2])
        return points[i_sorted_z].flatten()
    else:  # sort by y
        i_sorted_y = sorted(range(nb_markers), key=lambda i: points[i, 1])
        return points[i_sorted_y].flatten()
