from dataclasses import dataclass
import socket
import warnings
import time
from enum import Enum
import multiprocessing
from multiprocessing.sharedctypes import SynchronizedArray
from multiprocessing.synchronize import Event
import numpy as np

from emioapi import EmioMotors, EmioCamera
import emioapi.udp_bridge.udp_bridge_params as prm

#---------------------
#region  UDP
#---------------------
@dataclass
class UDPBridgeConfig:
    # FPS and Marker Settings
    fps: float
    nb_markers: int
    side: str  # "top" or "front"
    sort: str  # "y" or "z", only for front camera

    # UDP settings
    remote_ip: str
    remote_port: int
    local_port: int
    bind_port: int
    recv_timeout: float

    def __post_init__(self):
        self.fps = prm.fps
        self.nb_markers = prm.nb_markers
        self.side = prm.side
        self.sort = prm.sort
        self.remote_ip = prm.remote_ip
        self.remote_port = prm.remote_port
        self.local_port = prm.local_port
        self.bind_port = prm.bind_port
        # Camera settings
        self.depth = prm.depth
        self.plane_d = prm.plane_d
        self.plane_n = prm.plane_n
        self.front2top_offset = prm.front2top_offset
        ## ny and nu should not be changed
        self.ny = 3 * self.nb_markers # number of measurements
        self.nu = 4 # number of actuators

    
class CommStatus(Enum):
    """Status returned by :meth:`UDPBridge.send_and_receive`.

    Attributes:
        OK: Reply received, sequence numbers match (one-tick delay).
        OK_NO_DELAY: Reply received with no delay (seq matches exactly).
        DESYNC: Sequence mismatch detected; bridge is flushing the buffer.
        TIMEOUT: No reply received within ``recv_timeout``.
        RECONNECTED: Bridge lost sync and successfully re-handshaked.
    """
    OK           = "OK"
    OK_NO_DELAY  = "OK_NO_DELAY"
    DESYNC       = "DESYNC"
    TIMEOUT      = "TIMEOUT"
    RECONNECTED  = "RECONNECTED"


class UDPBridge:
    """UDP bridge between Python and a Remote host (e.g. Simulink) for real-time control.

    Python is the clock master: it sends a vector of ``send_size`` doubles at
    each tick (prepended with a sequence number) and blocks until Remote host
    replies with a vector of ``recv_size`` doubles (also prepended with a
    sequence number).

    Wire format (both directions)::

        [ seq (float64) | data[0] | data[1] | ... ]
        total bytes = (1 + send_size) * 8   (Python -> Remote host)
        total bytes = (1 + recv_size) * 8   (Remote host -> Python)

    Not thread-safe: ``send_and_receive`` must be called from a single thread.

    Typical usage::

        with UDPBridge(send_size=3, recv_size=2) as bridge:
            bridge.handshake()
            while True:
                reply, status = bridge.send_and_receive(my_data)

    Args:
        send_size: Number of data doubles sent to UDP each tick.
        recv_size: Number of data doubles expected from UDP each tick.
        remote_ip: IP address of the UDP host.
        remote_port: UDP port Remote host listens on (Python -> Remote host).
        local_port: UDP port Python listens on (Remote host -> Python).
        bind_port: Local port used for sending.
        recv_timeout: Socket timeout in seconds while waiting for a reply.
    """

    MAX_RECONNECT_ATTEMPTS = 3
    _MAX_DESYNC_COUNT      = 5

    def __init__(
        self,
        send_size: int,
        recv_size: int,
        remote_ip: str    = "127.0.0.1",
        remote_port: int  = 25000,
        local_port: int    = 25001,
        bind_port: int      = 9090,
        recv_timeout: float = 0.1,
    ):
        self.send_size      = send_size
        self.recv_size      = recv_size
        self.remote_addr  = (remote_ip, remote_port)
        self.recv_timeout   = recv_timeout

        self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_send.bind(("0.0.0.0", bind_port))

        self._sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_recv.bind(("0.0.0.0", local_port))

        self._seq           = 0
        self._last_reply    = np.zeros((recv_size, 1))
        self._timeout_count = 0
        self._desync_count  = 0

    # --------------------------------------------------------------------------
    # Context manager
    # --------------------------------------------------------------------------

    def __enter__(self) -> "UDPBridge":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def handshake(self, handshake_timeout: float = 0.05) -> None:
        """Block until Remote host acknowledges the connection.

        Sends ``seq=-1`` with a zero payload of ``send_size`` doubles so the
        wire size is identical to the main loop. Resets the sequence counter
        on success.

        Args:
            handshake_timeout: Per-attempt socket timeout in seconds.
        """
        print("  -> Start the Remote host now (waiting for handshake...)")

        payload    = np.zeros(1 + self.send_size, dtype=np.float64)
        payload[0] = -1.0

        self._sock_recv.settimeout(handshake_timeout)

        while True:
            self._sock_send.sendto(self._pack(payload), self.remote_addr)
            try:
                self._sock_recv.recvfrom((self.recv_size + 1) * 8)
                print("  Handshake OK - ready!\n")
                break
            except socket.timeout:
                pass

        self._seq           = 0
        self._timeout_count = 0
        self._desync_count  = 0
        self._last_reply    = np.zeros((self.recv_size, 1))
        self._sock_recv.settimeout(self.recv_timeout)

    def send_and_receive(self, data: np.ndarray) -> tuple[np.ndarray, CommStatus]:
        """Send a data vector and return the reply from Remote host.

        ``data`` is silently padded with zeros or truncated to match
        ``send_size`` if needed (a warning is emitted).

        On consecutive timeouts (>= ``MAX_RECONNECT_ATTEMPTS``) or persistent
        desyncs (>= ``_MAX_DESYNC_COUNT``), a new handshake is triggered
        automatically.

        Args:
            data: Vector of doubles, ideally shape ``(send_size,)`` or
                ``(send_size, 1)``.

        Returns:
            A tuple ``(reply, status)`` where ``reply`` has shape
            ``(recv_size, 1)`` and ``status`` is one of:
            :class:`CommStatus`.

        Raises:
            RuntimeError: If the packet received from Remote host has an
                unexpected size (mismatch between ``recv_size`` and the
                Remote host UDP Send block configuration).
        """
        data    = self._coerce_send_data(np.asarray(data, dtype=np.float64).flatten())
        seq     = self._seq
        payload = np.concatenate([[float(seq)], data])
        self._sock_send.sendto(self._pack(payload), self.remote_addr)

        try:
            raw, _ = self._sock_recv.recvfrom((self.recv_size + 1) * 8)

            expected = (self.recv_size + 1) * 8
            if len(raw) != expected:
                raise RuntimeError(
                    f"Unexpected packet size from Remote host: got {len(raw)} bytes, "
                    f"expected {expected}. "
                    f"Check that recv_size={self.recv_size} matches your "
                    f"Remote host UDP Send block."
                )

            response            = self._unpack(raw, self.recv_size + 1)
            seq_back            = int(response[0, 0])
            reply               = response[1:]
            self._last_reply    = reply
            self._timeout_count = 0
            status              = self._sync_status(seq_back, seq)

            if status == CommStatus.DESYNC:
                self._desync_count += 1
                self._flush_recv_buffer()
                if self._desync_count >= self._MAX_DESYNC_COUNT:
                    print(f"\n  {self._MAX_DESYNC_COUNT} consecutive desyncs "
                          f"- restarting handshake...")
                    self.handshake()
                    return self._last_reply, CommStatus.RECONNECTED
            else:
                self._desync_count = 0

        except socket.timeout:
            reply = self._last_reply
            self._timeout_count += 1
            status = CommStatus.TIMEOUT

            if self._timeout_count >= self.MAX_RECONNECT_ATTEMPTS:
                print(f"\n  {self.MAX_RECONNECT_ATTEMPTS} consecutive timeouts "
                      f"- restarting handshake...")
                self.handshake()
                return self._last_reply, CommStatus.RECONNECTED

        self._seq += 1
        return reply, status

    def close(self) -> None:
        """Release UDP sockets."""
        self._sock_send.close()
        self._sock_recv.close()

    @property
    def seq(self) -> int:
        """Current sequence counter."""
        return self._seq

    # --------------------------------------------------------------------------
    # Private helpers
    # --------------------------------------------------------------------------

    def _coerce_send_data(self, data: np.ndarray) -> np.ndarray:
        """Pad or truncate ``data`` to ``send_size``, warning if needed."""
        n = len(data)
        if n == self.send_size:
            return data
        if n < self.send_size:
            warnings.warn(
                f"send_and_receive: data has {n} value(s), expected "
                f"{self.send_size}. Padding with zeros.",
                stacklevel=3,
            )
            return np.pad(data, (0, self.send_size - n))
        warnings.warn(
            f"send_and_receive: data has {n} value(s), expected "
            f"{self.send_size}. Truncating to first {self.send_size}.",
            stacklevel=3,
        )
        return data[: self.send_size]

    def _flush_recv_buffer(self) -> None:
        """Drain any stale packets so the next read is up to date."""
        self._sock_recv.settimeout(0)
        try:
            while True:
                self._sock_recv.recvfrom((self.recv_size + 1) * 8)
        except (socket.timeout, BlockingIOError):
            pass
        finally:
            self._sock_recv.settimeout(self.recv_timeout)

    @staticmethod
    def _pack(arr: np.ndarray) -> bytes:
        return arr.astype(np.float64).flatten().tobytes()

    @staticmethod
    def _unpack(data: bytes, n: int) -> np.ndarray:
        return np.frombuffer(data, dtype=np.float64).reshape(n, 1)

    @staticmethod
    def _sync_status(seq_back: int, seq: int) -> CommStatus:
        if seq_back == seq - 1:
            return CommStatus.OK
        if seq_back == seq:
            return CommStatus.OK_NO_DELAY
        return CommStatus.DESYNC
    
#---------------------
#region  Motors
#---------------------

def process_motors(shared_markers_pos: SynchronizedArray,
                   event_frame: Event,
                   event_measure: Event,
                   config: UDPBridgeConfig) -> None:
    """Motor control loop bridging the remote controller and the physical motors.

    Waits for frame and measure events, reads motor positions and marker data,
    then exchanges them with the remote host to get the next command. Runs until
    interrupted by a KeyboardInterrupt (Ctrl-C).

    Args:
        shared_markers_pos: Shared memory array holding marker positions.
        event_frame: Event set by the camera process at each new frame.
        event_measure: Event set when marker measurement is ready.
    """
    motors = setup_motors()

    measure = np.zeros((config.ny, 1))
    command = np.zeros((config.nu, 1))

    with UDPBridge(
        send_size     = config.ny + config.nu,
        recv_size     = config.nu,
        remote_ip   = config.remote_ip,
        remote_port = config.remote_port,
        local_port   = config.local_port,
        bind_port     = config.bind_port,
        recv_timeout  = config.recv_timeout
    ) as bridge:
        bridge.handshake()
        t           = time.perf_counter()
        dt_expected = 1.0 / config.fps

        while True:
            # ------------------------------------------------------------------
            # Wait for new frame and measure events
            # ------------------------------------------------------------------
            event_frame.wait()
            event_frame.clear()

            dt_actual = time.perf_counter() - t
            t         = time.perf_counter()
            if abs(dt_actual - dt_expected) > 0.1 * dt_expected:
                warnings.warn(
                    f"[{bridge.seq:04d}] Timing drift: "
                    f"dt={dt_actual * 1000:.1f}ms, "
                    f"expected={dt_expected * 1000:.1f}ms",
                    stacklevel=2,
                )

            # ------------------------------------------------------------------
            # Read motors position and send command
            # ------------------------------------------------------------------
            motors_pos = get_motors_position(motors)
            send_motors_command(motors, command)

            event_measure.wait()
            event_measure.clear()

            # ------------------------------------------------------------------
            # Read shared marker data
            # ------------------------------------------------------------------
            with shared_markers_pos.get_lock():
                measure[:, 0] = shared_markers_pos[:]

            # ------------------------------------------------------------------
            # Remote host communication — compute next command
            # ------------------------------------------------------------------
            data            = np.vstack((measure, motors_pos))
            command, status = bridge.send_and_receive(data)
            if status not in (CommStatus.OK, CommStatus.OK_NO_DELAY):
                print(f"[{bridge.seq}] {status.value}")

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def setup_motors() -> EmioMotors:
    """Open and return an EmioMotors instance, retrying until successful.

    Returns:
        An open EmioMotors instance.
    """
    motors = EmioMotors()
    while not motors.open():
        print("Waiting for motors to open...")
        time.sleep(1)
    print("Motors opened successfully.")
    return motors


def send_motors_command(motors: EmioMotors, command: np.ndarray) -> None:
    """Send a command vector to the motors.

    Args:
        motors: An open EmioMotors instance.
        command: Command vector, any shape — will be flattened.
    """
    command = command.flatten()
    motors.angles = command.tolist()


def get_motors_position(motors: EmioMotors) -> np.ndarray:
    """Read current motor angles.

    Args:
        motors: An open EmioMotors instance.

    Returns:
        Motor positions as a column vector, shape ``(n_motors, 1)``.
    """
    motors_pos = np.array(motors.angles)
    return motors_pos.reshape((-1, 1))

#---------------------
#region  Camera
#---------------------
def process_camera(shared_markers_pos: SynchronizedArray,
                   event_frame: Event,
                   event_measure: Event,
                   config: UDPBridgeConfig) -> None:
    """Main camera loop: grab frames, track markers, and update shared state.

    Sets ``event_frame`` at each new frame and ``event_measure`` once the
    marker positions are written to ``shared_markers_pos``.
    Stops when the user presses ``q``.

    Args:
        shared_markers_pos: Shared memory array written with marker positions.
        event_frame: Event set at each new camera frame.
        event_measure: Event set once marker data is ready.
    """
    camera = setup_camera(config)
    pos = np.zeros((config.ny, 1))

    while True:
        if camera.is_running:
            ret = camera.get_frame()
            event_frame.set()
            if ret:
                pos = process_frame(camera, pos, config)

            with shared_markers_pos.get_lock():
                shared_markers_pos[:] = pos.flatten()
            event_measure.set()
        else:
            print("Camera is not running.")
            time.sleep(1)
            continue

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def setup_camera(config: UDPBridgeConfig) -> EmioCamera:
    """Initialise and open the depth camera from ``params``.

    Returns:
        A configured, open DepthCamera instance.
    """
    camera = EmioCamera(
        show=True,
        track_markers=True,
        compute_point_cloud=False
        )
    camera.fps = config.fps
    camera.depth_min = 0
    camera.depth_max = 1000
    camera.open()
    return camera

# -------------------------------------------------------
def process_frame(camera: EmioCamera, last_pos: np.ndarray, config: UDPBridgeConfig) -> np.ndarray:
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
    if len(camera.trackers_pos) == config.nb_markers:
        if config.side == "top":
            pos = np.array(camera.trackers_pos).reshape(config.nb_markers, 3).copy()
            pos = pos.astype(np.float64)
            return pos

        elif config.side == "front":
            p = np.array(camera.trackers_pos_image).reshape(config.nb_markers, 3).copy()
            p = p.astype(np.float64)
            p = pixel_to_mm(p, config.depth, config)
            p = camera_to_sofa_order(p, config)
            return p.reshape((-1, 1))

        elif config.side == "plan":
            trackers_projected = []
            for pixel_pos in camera.trackers_pos_image:
                result = camera._camera.position_estimator.camera_image_to_simulation_plane_intersection(
                    pixel_pos[0],pixel_pos[1],config.plane_n, config.plane_d)
                trackers_projected.append(result)
            p = np.array(trackers_projected).reshape(config.nb_markers, 3).copy()
            p = p.astype(np.float64)
            p = camera_to_sofa_order(p, config)
            return p.reshape((-1, 1))

    return last_pos

# -------------------------------------------------------
def pixel_to_mm(points: np.ndarray, depth: float, config:UDPBridgeConfig) -> np.ndarray:
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
    points += config.front2top_offset
    points = np.column_stack((points[:, 2], -points[:, 1], points[:, 0]))
    return points.copy()

# -------------------------------------------------------
def camera_to_sofa_order(points: np.ndarray, config: UDPBridgeConfig) -> np.ndarray:
    """Reorder markers by ascending y-coordinate (SOFA convention).

    Args:
        points: Marker positions, shape ``(nb_markers, 3)``.

    Returns:
        Reordered positions as a flat array.
    """
    if config.sort == "z":
        i_sorted_z = sorted(range(config.nb_markers), key=lambda i: points[i, 2])
        return points[i_sorted_z].flatten()
    else:  # sort by y
        i_sorted_y = sorted(range(config.nb_markers), key=lambda i: points[i, 1])
        return points[i_sorted_y].flatten()
    

#---------------------
#region  Start UDP bridge
#---------------------
def startUDPbridge(config: UDPBridgeConfig):

    # shared variables
    shared_markers_pos = multiprocessing.Array("d", config.ny * [0.])

    # shared event
    event_frame = multiprocessing.Event()
    event_measure = multiprocessing.Event()

    # Create processes
    p1 = multiprocessing.Process(target=process_camera, args=(
        shared_markers_pos, event_frame, event_measure, config))

    p2 = multiprocessing.Process(target=process_motors, args=(
        shared_markers_pos, event_frame, event_measure, config))


    p1.start()
    p2.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        p1.terminate()
        p2.terminate()

        p1.join()
        p2.join()
