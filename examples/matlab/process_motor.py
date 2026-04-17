import time
import warnings
from multiprocessing.sharedctypes import SynchronizedArray
from multiprocessing.synchronize import Event

import numpy as np
from emioapi import EmioMotors

import params as prm
from simulink_bridge import SimulinkBridge

# ------------------------------------------------------------------------------
# Process
# ------------------------------------------------------------------------------

def process_motors(shared_markers_pos: SynchronizedArray,
                   event_frame: Event,
                   event_measure: Event) -> None:
    """Motor control loop bridging Simulink and the physical motors.

    Waits for frame and measure events, reads motor positions and marker data,
    then exchanges them with Simulink to get the next command. Runs until
    interrupted by a KeyboardInterrupt (Ctrl-C).

    Args:
        shared_markers_pos: Shared memory array holding marker positions.
        event_frame: Event set by the camera process at each new frame.
        event_measure: Event set when marker measurement is ready.
    """
    motors = setup_motors()

    measure = np.zeros((prm.ny, 1))
    command = np.zeros((prm.nu, 1))

    with SimulinkBridge(
        send_size     = prm.ny + prm.nu,
        recv_size     = prm.nu,
        simulink_ip   = prm.simulink_ip,
        simulink_port = prm.simulink_port,
        python_port   = prm.python_port,
        bind_port     = prm.bind_port,
        recv_timeout  = prm.recv_timeout,
    ) as bridge:
        bridge.handshake()
        t           = time.perf_counter()
        dt_expected = 1.0 / prm.fps

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
            # Simulink communication — compute next command
            # ------------------------------------------------------------------
            data            = np.vstack((measure, motors_pos))
            command, status = bridge.send_and_receive(data)

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
