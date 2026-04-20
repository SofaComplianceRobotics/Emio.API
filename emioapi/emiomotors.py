from dataclasses import field
from threading import Lock
from math import pi

from dynamixelmotorsapi import DynamixelMotors
from emioapi._logging_config import logger

class EmioMotors(DynamixelMotors):
    """
    Class to control emio motors.
    The class is designed to be used with the emio device.
    The motors are controlled in position mode. The class is thread-safe and can be used in a multi-threaded environment.

    Example:
        ```python
        from emioapi import EmioMotors

        # Create an instance of EmioMotors
        motors = EmioMotors()

        # Open connection to the motors (optionally specify device name)
        if motors.open():
            # Print current angles in radians
            print("Current angles (rad):", motors.angles)

            # Set new goal angles (example values)
            motors.angles = [0.5, 1.0, -0.5, 1.0]

            # Print status
            motors.printStatus()

            # Close connection when done
            motors.close()
        else:
            print("Failed to connect to motors.")
        ```

    """


    #####################
    ###### METHODS ######
    #####################

    def __init__(self):
        super().__init__([{
            "id": [0, 1, 2, 3],
            "model": "XM430-W210",
            "pulley_radius": 20,
            "pulse_center": 2048,
            "max_vel": 1000,
            "baud_rate": 1000000
        }])
