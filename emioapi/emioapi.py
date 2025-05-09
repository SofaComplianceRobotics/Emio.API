#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Example on how to control the angles of 3 motors (Dynamixel PM42-010-S260-R) 
# The motors should be connected to /dev/ttyUSB0 with a baudrate of 4000000 and have the id's (1,2,3)
#
# To change the configuration, either change the 
#
# The spec of the motors : https://emanual.robotis.com/docs/en/dxl/x/xm430-w210/

import time
import logging
from dataclasses import field
import emioapi._motorgroup as MotorGroup
import emioapi._emiomotorsparameters as EmioParameters
from threading import Lock


FORMAT = "[%(levelname)s]\t[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

class EmioAPI:
    """
    Singleton class to control emio motors.
    
    :::warning 
    
    Emio motors are clamped between 0 and PI radians (0 and 180 degrees). If you input a value outside this range, the motor will not move.

    :::
    
    """
    _initialized: bool = False
    _length_to_rad: float = 1.0 / 20.0  # 1/radius of the pulley
    _rad_to_pulse: int = 4096 / (2 * 3.1416)  # the resolution of the Dynamixel xm430 w210
    _length_to_pulse: int = _length_to_rad * _rad_to_pulse
    _pulse_center: int = 2048
    _max_vel: float = 1000  # *0.01 rev/min
    _goal_velocity: list = field(default_factory=lambda: [0] * len(EmioParameters.DXL_IDs))
    _goal_position: list = field(default_factory=lambda: [0] * len(EmioParameters.DXL_IDs))
    _mg: MotorGroup.MotorGroup = None

    def __new__(cls):
        """Ensure that only one instance of the class is created."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmioAPI, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._lock = Lock()
        if not self._initialized:
            self._mg = MotorGroup.MotorGroup(EmioParameters)
            self._initialized = True


    def _length_to_pulse(self, displacement: list):
        """
        Convert length (mm) to pulse using the conversion factor `lengthToPulse`. 
        
        Args:
            displacement: list of length values in mm for each motor.

        Returns:
            A list of pulse values for each motor.
        """
        return [int(item * self._length_to_pulse) for item in displacement]


    def pulseToLength(self, pulse: list):
        """
        Convert pulse to length (mm) using the conversion factor `lengthToPulse`.
        
        Args:
            pulse: list of pulse integer values for each motor.

        Returns:
            A list of length values in mm for each motor.
        """
        return [float(item) / self._length_to_pulse for item in pulse]


    def pulseToRad(self, pulse: list):
        """
        Convert pulse to radians using the conversion factor `radToPulse`.

        Args:
            pulse: list of pulse integer values for each motor.

        Returns:
            A list of angles in radians for each motor.

        """
        return [float(item) / self._rad_to_pulse for item in pulse]


    def pulseToDeg(self, pulse: list):
        """
        Convert pulse to degrees using the conversion factor `radToPulse`.

        Args:
            pulse: list of pulse values for each motor.

        Returns:
            A list of angles in degrees for each motor.
        """
        return [float(item) / self._rad_to_pulse * 180.0 / 3.1416 for item in pulse]


    def openAndConfig(self) -> bool:
        """Open the connection to the motors, configure it for position mode and enable torque sensing."""
        logger.info("Opening and configuring the motor group.")
        with self._lock:
            try:
                self._mg.updateDeviceName()

                if self._mg.deviceName is None:
                    logger.error("Device name is None. Please check the connection.")
                    return False
                
                self._mg.open()
                self._mg.clearPort()
                self._mg.setInPositionMode()
                self._mg.enableTorque()

                logger.info(f"Motor group opened and configured. Device name: {self._mg.deviceName}")
                return True
            except Exception as e:
                logger.error(f"Failed to open and configure the motor group: {e}")
                return False


    def close(self):
        """Close the connection to the motors."""
        logger.info("Closing the connection to the motors.")
        with self._lock:
            self._mg.close()
            logger.info("Connection closed.")


    def printStatus(self):
        """Print the current position of the motors."""
        with self._lock:
            logger.info(f"Current position of the motors in pulses: {self._mg.getCurrentPosition()}")


    ### Properties ###
    #### Read and Write properties ####
    @property
    def relativePos(self, init_pos: list, rel_pos: list):
        """
        Calculate the new position of the motors based on the initial position and relative position in pulses.
        
        Args:
            init_pos: list of initial pulse values for each motor.
            rel_pos: list of relative pulse values for each motor.

        Returns:
            A list of new pulse values for each motor.
        """
        new_pos = []
        for i in range(len(init_pos)):
            new_pos.append(init_pos[i] + rel_pos[i])
        return new_pos


    @property
    def angles(self):
        """Get the current angles of the motors in radians."""
        with self._lock:
            return self.pulseToRad(self._mg.getCurrentPosition())

    @angles.setter
    def angles(self, angles):
        """Set the goal angles of the motors in radians."""
        with self._lock:
            self._goal_position = angles
            self._mg.setGoalPosition([int(self._pulse_center - self._rad_to_pulse * a) for a in angles])


    @property
    def goal_velocity(self):
        """Get the current velocity (rev/min) of the motors."""
        return self._goal_velocity

    @goal_velocity.setter
    def goal_velocity(self, velocities):
        """Set the goal velocity (rev/min) of the motors."""
        self._goal_velocity = velocities
        with self._lock:
            self._mg.setGoalVelocity(velocities)

    @property
    def max_velocity(self):
        """Get the current velocity (rev/min) profile of the motors."""
        return self._max_vel
    
    @max_velocity.setter
    def max_velocity(self, max_vel):
        """Set the maximum velocities (rev/min) in position mode.
        Arguments:
            max_vel: list of maximum velocities for each motor in rev/min.
        """
        self._max_vel = max_vel
        with self._lock:
            self._mg.setVelocityProfile(max_vel)

    #### Read-only properties ####
    @property
    def is_connected(self):
        """Check if the motors are connected."""
        with self._lock:
            return self._mg.isConnected

    @property
    def moving(self):
        """Check if the motors are moving."""
        with self._lock:
            return self._mg.isMoving()
    
    @property
    def moving_status(self):
        """Get the moving status of the motors.
        Returns:
         A Byte encoding different informations on the moving status like whether the desired position has been reached or not, if the profile is in progress or not, the kind of Profile used...
        See here https://emanual.robotis.com/docs/en/dxl/x/xc330-t288/#moving-status for more details."""
        with self._lock:
            return self._mg.getMovingStatus()
    
    @property
    def velocity(self):
        """Get the current velocity (rev/min) of the motors."""
        with self._lock:
            return self._mg.getCurrentVelocity()
    
    @property
    def velocity_trajectory(self):
        """Get the velocity (rev/min) trajectory of the motors."""
        with self._lock:
            return self._mg.getVelocityTrajectory()
    
    @property
    def position_trajectory(self):
        """Get the position (pulse) trajectory of the motors."""
        with self._lock:
            return self._mg.getPositionTrajectory()
    

emio = EmioAPI()