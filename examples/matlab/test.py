import argparse
import time
import warnings

import numpy as np
import params as prm
from udp_bridge import UDPBridge


def parse_args():
    p = argparse.ArgumentParser(description="UDP Bridge - Motor control")
    p.add_argument("--fps",          default=prm.fps,          type=int)
    p.add_argument("--nb_markers",   default=prm.nb_markers,   type=int)
    p.add_argument("--side",         default=prm.side,         type=str,
                   choices=["top", "front", "plan"])
    p.add_argument("--sort",         default=prm.sort,         type=str,
                   choices=["y", "z"])
    p.add_argument("--remote_ip",    default=prm.remote_ip,    type=str)
    p.add_argument("--remote_port",  default=prm.remote_port,  type=int)
    p.add_argument("--local_port",   default=prm.local_port,   type=int)
    p.add_argument("--bind_port",    default=prm.bind_port,    type=int)
    p.add_argument("--recv_timeout", default=prm.recv_timeout, type=float)

    return p.parse_args()


def main():
    """Standalone test loop for the remote bridge without a physical robot.

    Replaces camera and motor data with random vectors, so the bridge can be
    validated against a remote model without any hardware connected.
    """
    args = parse_args()
    ny = 3 * args.nb_markers
    measure = np.zeros((ny, 1))
    command = np.zeros((prm.nu, 1))

    with UDPBridge(
        send_size     = ny + prm.nu,
        recv_size     = prm.nu,
        remote_ip   = args.remote_ip,
        remote_port = args.remote_port,
        local_port   = args.local_port,
        bind_port     = args.bind_port,
        recv_timeout  = args.recv_timeout,
    ) as bridge:
        bridge.handshake()
        t           = time.perf_counter()
        dt_expected = 1.0 / args.fps

        while True:
            # ------------------------------------------------------------------
            # Pace the loop to match args.fps
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
            measure    = np.random.rand(ny, 1)

            # ------------------------------------------------------------------
            # Remote host communication — compute next command
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
