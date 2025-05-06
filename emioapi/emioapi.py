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
import emioapi.motorgroup as MotorGroup
import emioapi.emiomotorsparameters as EmioParameters

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ["emioapi"]


class __emioapi:
    """Class to control emio motors."""
    def __init__(self):
        """Initialize the EMIO API class with motor group and conversion factors."""
        self._mg = MotorGroup.MotorGroup(EmioParameters)
        self.length_to_rad = 1.0 / 20.0  # 1/radius of the pulley
        self.rad_to_pulse = 4096 / (2 * 3.1416)  # the resolution of the Dynamixel xm430 w210
        self.length_to_pulse = self.length_to_rad * self.rad_to_pulse
        self.pulse_center = 2048

        self._max_vel = 1000  # *0.01 rev/min
        self._goal_velocity = [0] * len(EmioParameters.DXL_IDs)
        self._goal_position = [0] * len(EmioParameters.DXL_IDs)


    def length_to_pulse(self, displacement: list):
        """Convert length (mm) to pulse using the conversion factor `lengthToPulse`. """
        return [int(item * self.length_to_pulse) for item in displacement]


    def pulseToLength(self, pulse: list):
        """Convert pulse to length (mm) using the conversion factor `lengthToPulse`."""
        return [float(item) / self.length_to_pulse for item in pulse]


    def pulseToRad(self, pulse: list):
        """Convert pulse to radians using the conversion factor `radToPulse`."""
        return [float(item) / self.rad_to_pulse for item in pulse]


    def pulseToDeg(self, pulse: list):
        """Convert pulse to degrees using the conversion factor `radToPulse`."""
        return [float(item) / self.rad_to_pulse * 180.0 / 3.1416 for item in pulse]


    def openAndConfig(self):
        """Open the connection to the motors, configure it for position mode and enable torque sensing."""
        if EmioParameters.DEVICENAME is None:
            return

        self._mg.open()
        self._mg.setInPositionMode()
        self._mg.enableTorque()

        logger.info(f"Motor group opened and configured. Device name: {EmioParameters.DEVICENAME}")


    def close(self):
        """Close the connection to the motors."""
        self._mg.close()


    def printStatus(self):
        """Print the current position of the motors."""
        logger.info(f"Current position of the motors in pulses: {self._mg.getCurrentPosition()}")


    ### Properties ###
    #### Read and Write properties ####
    @property
    def relativePos(self, init_pos: list, rel_pos: list):
        """Calculate the new position of the motors based on the initial position and relative position in pulses."""
        new_pos = []
        for i in range(len(init_pos)):
            new_pos.append(init_pos[i] + rel_pos[i])
        return new_pos


    @property
    def angles(self):
        """Get the current angles of the motors in radians."""
        return self.pulseToRad(self._mg.getCurrentPosition())

    @angles.setter
    def angles(self, angles):
        """Set the goal angles of the motors in radians."""
        self._goal_position = angles
        self._mg.setGoalPosition([int(self.pulse_center - self.rad_to_pulse * a) for a in angles])
        logging.info(f"Set goal position in pulses: {[int(self.pulse_center - self.rad_to_pulse * a) for a in angles]}")


    @property
    def goal_velocity(self):
        """Get the current velocity (rev/min) of the motors."""
        return self._goal_velocity

    @goal_velocity.setter
    def goal_velocity(self, velocities):
        """Set the goal velocity (rev/min) of the motors."""
        self._goal_velocity = velocities
        self._mg.setGoalVelocity(velocities)

    @property
    def max_velocity(self):
        """Get the current velocity (rev/min) profile of the motors."""
        return self._max_vel
    
    @max_velocity.setter
    def max_velocity(self, max_vel):
        """Set the maximum velocities (rev/min) in position mode."""
        self._max_vel = max_vel
        self._mg.setVelocityProfile(max_vel)

    #### Read-only properties ####
    @property
    def moving(self):
        """Check if the motors are moving."""
        return self._mg.isMoving()
    
    @property
    def moving_status(self):
        """Get the moving status of the motors.
        Returns:
         A Byte encoding different informations on the moving status like whether the desired position has been reached or not, if the profile is in progress or not, the kind of Profile used...
        See here https://emanual.robotis.com/docs/en/dxl/x/xc330-t288/#moving-status for more details."""
        return self._mg.getMovingStatus()
    
    @property
    def velocity(self):
        """Get the current velocity (rev/min) of the motors."""
        return self._mg.getCurrentVelocity()
    
    @property
    def velocity_trajectory(self):
        """Get the velocity (rev/min) trajectory of the motors."""
        return self._mg.getVelocityTrajectory()
    
    @property
    def position_trajectory(self):
        """Get the position (pulse) trajectory of the motors."""
        return self._mg.getPositionTrajectory()
    

emioapi = __emioapi()