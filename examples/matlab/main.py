import time
import multiprocessing

import params as prm
from camera import process_camera
from process_motor import process_motors

def main():

    # shared variables
    shared_markers_pos = multiprocessing.Array("d", prm.ny * [0.])

    # shared event
    event_frame = multiprocessing.Event()
    event_measure = multiprocessing.Event()

    # Create processes
    p1 = multiprocessing.Process(target=process_camera, args=(
        shared_markers_pos, event_frame, event_measure))

    p2 = multiprocessing.Process(target=process_motors, args=(
        shared_markers_pos, event_frame, event_measure))


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
