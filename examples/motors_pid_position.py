import numpy as np
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/..')
from emioapi import EmioMotors


def main():

    # open motors
    motors = EmioMotors()
    while not motors.open():
        print("Waiting for motors to open...")
        time.sleep(1)
    print("Motors opened successfully.")

    # initial and target angles
    init_angles = np.array([0.0, 0, 0.0, 0])
    target_angles = init_angles + np.array([0.1, 0, 0, 0])
    motors.angles = init_angles
    time.sleep(1)

    # set first set of gains
    motors.position_p_gain = [800, 800, 800, 800]
    motors.position_i_gain = [0, 0, 0, 0]
    motors.position_d_gain = [0, 0, 0, 0]
    print("Set first PID gains.")
    time.sleep(1)

    p_gains = motors.position_p_gain
    i_gains = motors.position_i_gain
    d_gains = motors.position_d_gain
    print(f"Current position P gains: {p_gains}")
    print(f"current position i gains: {i_gains}")
    print(f"Current position D gains: {d_gains}")

    # move to target and record response
    measures = [motors.angles]
    motors.angles = target_angles
    times = [time.time()]
    t0 = time.time()
    while time.time() - t0 < 0.3:
        measures.append(motors.angles)
        times.append(time.time())
    time.sleep(1)
    nb_steps1 = len(measures)


    motors.angles = init_angles

    motors.position_p_gain = [15800, 800, 15800, 800]
    motors.position_i_gain = [0, 0, 0, 0]
    motors.position_d_gain = [0, 0, 0, 0]
    print("Set second PID gains.")
    time.sleep(1)

    p_gains = motors.position_p_gain
    i_gains = motors.position_i_gain
    d_gains = motors.position_d_gain
    print(f"Updated position P gains: {p_gains}")
    print(f"Updated position I gains: {i_gains}")
    print(f"Updated position D gains: {d_gains}")

    # move to target and record response
    measures.append(motors.angles)
    motors.angles = target_angles
    times.append(time.time())
    t0 = time.time()
    while time.time() - t0 < 0.3:
        measures.append(motors.angles)
        times.append(time.time())
    time.sleep(1)

    motors.close()
    print("Motors closed.")


if __name__ == "__main__":
    main()
