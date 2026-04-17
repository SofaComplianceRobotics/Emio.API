import time
import warnings

import numpy as np

import params as prm
from simulink_bridge import SimulinkBridge


def main():
    """Standalone test loop for the Simulink bridge without a physical robot.

    Replaces camera and motor data with random vectors, so the bridge can be
    validated against a Simulink model without any hardware connected.
    """
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
            # Pace the loop to match prm.fps
            # ------------------------------------------------------------------
            while time.perf_counter() - t < dt_expected:
                time.sleep(0.001)

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
            # Simulated measurements (random stand-in for camera + motors)
            # ------------------------------------------------------------------
            motors_pos = np.random.rand(prm.nu, 1)
            measure    = np.random.rand(prm.ny, 1)

            # ------------------------------------------------------------------
            # Simulink communication — compute next command
            # ------------------------------------------------------------------
            data = np.vstack((measure, motors_pos))
            command, status = bridge.send_and_receive(data)
            print(
                f"[{bridge.seq - 1:04d}] {status.value:12s} | "
                f"dt={dt_actual * 1000:.1f}ms | "
                f"y={measure.flatten().round(3)} | "
                f"u={command.flatten().round(3)}"
            )


if __name__ == "__main__":
    main()
