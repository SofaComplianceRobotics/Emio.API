from dataclasses import field
from threading import Lock
from math import pi

from dynamixelmotorsapi import DynamixelMotors

import emioapi._motorgroup as motorgroup
import emioapi._emiomotorsparameters as emioparameters
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

    # _initialized: bool = False
    # _length_to_rad: float = 1.0 / 20.0  # 1/radius of the pulley
    # _rad_to_pulse: int = 4096 / (2 * pi)  # the resolution of the Dynamixel xm430 w210
    # _length_to_pulse: int = _length_to_rad * _rad_to_pulse
    # _pulse_center: int = 2048
    # _max_vel: float = 1000  # *0.01 rev/min
    # _goal_velocity: list = field(default_factory=lambda: [0] * len(emioparameters.DXL_IDs))
    # _goal_position: list = field(default_factory=lambda: [0] * len(emioparameters.DXL_IDs))
    # _mg: motorgroup.MotorGroup = None
    # _device_index: int = None



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
