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
import motorgroup as MotorGroup
import emiomotorsparameters as EmioParameters

__all__ = ["emioapi"]


class __emioapi:
    """Class to control emio motors."""
    def __init__(self):
        """Initialize the EMIO API class with motor group and conversion factors."""
        self.mg = MotorGroup.MotorGroup(EmioParameters)
        self.length_to_rad = 1.0 / 20.0  # 1/radius of the pulley
        self.rad_to_pulse = 4096 / (2 * 3.1416)  # the resolution of the Dynamixel xm430 w210
        self.length_to_pulse = self.length_to_rad * self.rad_to_pulse
        self.pulse_center = 2048

        self._max_vel = 1000  # *0.01 rev/min
        self._goal_velocity = [0] * len(EmioParameters.DXL_IDs)
        self._goal_position = [0] * len(EmioParameters.DXL_IDs)


    def length_to_pulse(self, displacement: list):
        """Convert length to pulse using the conversion factor `lengthToPulse`. """
        return [int(item * self.length_to_pulse) for item in displacement]


    def pulseToLength(self, pulse: list):
        """Convert pulse to length using the conversion factor `lengthToPulse`."""
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

        self.mg.open()
        self.mg.setInPositionMode()
        self.mg.enableTorque()


    def close(self):
        """Close the connection to the motors."""
        self.mg.close()


    def printStatus(self):
        logging.info(self.mg.getCurrentPosition())


    ### Properties ###
    #### Read and Write properties ####
    @property
    def relativePos(self, init_pos: list, rel_pos: list):
        new_pos = []
        for i in range(len(init_pos)):
            new_pos.append(init_pos[i] + rel_pos[i])
        return new_pos


    @property
    def angle(self):
        """Get the current angles of the motors in radians."""
        return self.pulseToRad(self.mg.getCurrentPosition())

    @angle.setter
    def angle(self, angles):
        """Set the goal angles of the motors in radians."""
        self._goal_position = angles
        self.mg.setGoalPosition([int(self.pulse_center - self.rad_to_pulse * a) for a in angles])


    @property
    def goal_velocity(self):
        """Get the current velocity of the motors."""
        return self._goal_velocity

    @goal_velocity.setter
    def goal_velocity(self, velocities):
        """Set the goal velocity of the motors."""
        self._goal_velocity = velocities
        self.mg.setGoalVelocity(velocities)

    @property
    def max_velocity(self):
        """Get the current velocity profile of the motors."""
        return self._max_vel
    
    @max_velocity.setter
    def max_velocity(self, max_vel):
        """Set the maximum velocities in position mode."""
        self._max_vel = max_vel
        self.mg.setVelocityProfile(max_vel)

    #### Read-only properties ####
    @property
    def moving(self):
        """Check if the motors are moving."""
        return self.mg.isMoving()
    
    @property
    def moving_status(self):
        """Get the moving status of the motors."""
        return self.mg.getMovingStatus()
    
    @property
    def velocity(self):
        """Get the current velocity of the motors."""
        return self.mg.getCurrentVelocity()
    
    @property
    def velocity_trajectory(self):
        """Get the velocity trajectory of the motors."""
        return self.mg.getVelocityTrajectory()
    
    @property
    def position_trajectory(self):
        """Get the position trajectory of the motors."""
        return self.mg.getPositionTrajectory()
    

emioapi = __emioapi()