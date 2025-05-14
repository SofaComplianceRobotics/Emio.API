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

from threading import Lock

from emioapi.emiomotors import *
from emioapi.emiocamera import EmioCamera


FORMAT = "[%(levelname)s]\t[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EmioAPI:
    """
    Class to control emio motors. 
    The class is designed to be used with the emio device.
    The motors are controlled in position mode. The class is thread-safe and can be used in a multi-threaded environment.
    All the data sent to the motors are list of *4 values* for the *4 motors* of the emio device. The order in the list corresponds to the motor ID's in the emio device.
    Motor 0 is the first motor in the list, motor 1 is the second motor, etc.
    
    :::warning 

    Emio motors are clamped between 0 and PI radians (0 and 180 degrees). If you input a value outside this range, the motor will not move.

    :::
    
    """
    _emio_list = {}  # Dict of all emio devices connected to the computer
    motors = None  # The emio motors object
    camera = None  # The emio camera object

    def __init__(self):
        self._lock = Lock()
        self.motors = EmioMotors()
        self.camera = EmioCamera()


    @staticmethod
    def listEmioDevices() -> list:
        """
        List all the emio devices connected to the computer.
        
        Returns:
            A list of device names (the ports).
        """
        return MotorGroup.listEmioDevices()
    
    
    @staticmethod
    def listUnusedEmioDevices() -> list:
        """
        List all the emio devices that are not currently used by any instance of EmioAPI in this process.
        
        Returns:
            A list of device names (the ports).
        """
        return [device for device in EmioAPI.listEmioDevices() if device not in EmioAPI._emio_list]
    
    
    @staticmethod
    def listUsedEmioDevices() -> list:
        """
        List all the emio devices that are currently used by an instance of EmioAPI in this process.
        
        Returns:
            A list of device names (the ports).
        """
        return [device for device in EmioAPI._emio_list.keys()]
    
    
    def connectToEmioDevice(self, device_name: str=None) -> bool:
        """
        Connect to the emio device with the given name.
        
        Args:
            device_name: The name of the device to connect to. If None, the first device found that is not used in this process will be the chosen one.

        Returns:
            True if the connection is successful, False otherwise.
        """
        if device_name is None:
            device_name = EmioAPI.listUnusedEmioDevices()[0] if EmioAPI.listUnusedEmioDevices() else None

        if self.motors.open(device_name):
            EmioAPI._emio_list[self.motors.device_name] = self
            logger.info(f"Connected to emio device: {self.motors.device_name}")
            return True
        return False
    

    def disconnect(self):
        """Close the connection to all"""
        logger.debug("Closing the connection to the motors.")
        with self._lock:
            self.motors.close()
            logger.info("Connection closed.")
            EmioAPI._emio_list.pop(self.motors.device_name, None)


    def printStatus(self):
        """
        Print the status of the Emio device.
        """
        with self._lock:
            if self.motors.is_connected:
                logger.info(f"Connected to Emio device: {self.motors.device_name}")
        