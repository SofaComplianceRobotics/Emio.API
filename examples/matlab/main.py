import argparse
import time
import multiprocessing

import params as prm
from camera import process_camera
from process_motor import process_motors


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

    args = parse_args()
    ny = 3 * args.nb_markers

    # shared variables
    shared_markers_pos = multiprocessing.Array("d", ny * [0.])

    # shared event
    event_frame = multiprocessing.Event()
    event_measure = multiprocessing.Event()

    # Create processes
    p1 = multiprocessing.Process(target=process_camera, args=(
        shared_markers_pos, event_frame, event_measure, args))

    p2 = multiprocessing.Process(target=process_motors, args=(
        shared_markers_pos, event_frame, event_measure, args))


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


if __name__ == "__main__":
    main()
