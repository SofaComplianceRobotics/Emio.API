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
    It is essentially divided into two objects:
    - The `motors` object (`EmioMotors` class), which is used to control the motors.
    - The `camera` object (`EmioCamera` class), which is used to control the camera.

    The EmioAPI class is the main class that combines both classes and provides a simple interface to control the emio device.
    It also provides static utility methods to list the emio devices connected to the computer.
    
    Motors:
        > The motors are controlled in position mode. The class is thread-safe and can be used in a multi-threaded environment.
        > All the data sent to the motors are list of *4 values* for the *4 motors* of the emio device. The order in the list corresponds to the motor ID's in the emio device.
        > Motor 0 is the first motor in the list, motor 1 is the second motor, etc.
        > You can open a connection directly to the motors using the `open` method of the `motors` object.
        > 
        > :::warning 
        > 
        > Emio motors are clamped between 0 and PI radians (0 and 180 degrees). If you input a value outside this range, the motor will not move.
        > 
        > :::

    Camera:
        > The camera is controlled in a separate process. The camera is used to track objects and compute the point cloud.
        > The camera parameters are stored in a config file. If the config file is not found, default values are used.
        > The camera can be configured to show the frames, track objects, and compute the point cloud.
        > You can open a connection directly to the camera using the `open` method of the `camera` object.
    
    """
    _emio_list = {}  # Dict of all emio devices connected to the computer
    motors: EmioMotors = None  # The emio motors object
    camera: EmioCamera = None  # The emio camera object
    camera_parameters: dict = None  # The camera parameters object

    def __init__(self, camera_parameters=None):
        self._lock = Lock()
        self.camera_parameters = camera_parameters
        self.motors = EmioMotors()
        self.camera = EmioCamera(self, parameter=camera_parameters)


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
            logger.info(f"Connected to emio motors: {self.motors.device_name}")

            if self.camera.open():
                logger.info(f"Connected to emio camera")
                return True
        return False
    

    def disconnect(self):
        """Close the connection to motors and camera."""
        logger.debug("Closing the connection to the motors and camera.")
        with self._lock:
            self.motors.close()
            logger.debug("Motors connection closed.")

            self.camera.close()
            logger.debug("Camera closed.")

            EmioAPI._emio_list.pop(self.motors.device_name, None)
            logger.info(f"Disconnected from emio device: {self.motors.device_name}")


    def printStatus(self):
        """
        Print the status of the Emio device.
        """
        with self._lock:
            if self.motors.is_connected:
                logger.info(f"Connected to Emio device: {self.motors.device_name}")
        