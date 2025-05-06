#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from dynamixel_sdk import *
import emioapi.emiomotorsparameters as MotorsParametersTemplate
import logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

class MotorGroup:

    def __init__(self, parameters: MotorsParametersTemplate) -> None:

        self.parameters = parameters
        self.connected = True

        logger.info("Using %s on %s" % (self.parameters.MY_DXL, self.parameters.DEVICENAME))
        self.packetHandler = PacketHandler(self.parameters.PROTOCOL_VERSION)
        self.portHandler = PortHandler(self.parameters.DEVICENAME)
        self.groupSyncWritePosition = GroupSyncWrite(self.portHandler, self.packetHandler,
                                                     self.parameters.ADDR_GOAL_POSITION,
                                                     self.parameters.LEN_GOAL_POSITION)
        self.groupSyncWriteVelocity = GroupSyncWrite(self.portHandler, self.packetHandler,
                                                     self.parameters.ADDR_GOAL_VELOCITY,
                                                     self.parameters.LEN_GOAL_POSITION)
        self.groupSyncWriteVelocityProfile = GroupSyncWrite(self.portHandler, self.packetHandler,
                                                            self.parameters.ADDR_VELOCITY_PROFILE,
                                                            self.parameters.LEN_GOAL_POSITION)
        self.groupSyncReadPosition = GroupSyncRead(self.portHandler, self.packetHandler,
                                                   self.parameters.ADDR_PRESENT_POSITION,
                                                   self.parameters.LEN_PRESENT_POSITION)
        self.groupSyncReadGoalVelocity = GroupSyncRead(self.portHandler, self.packetHandler,
                                                        self.parameters.ADDR_GOAL_VELOCITY,
                                                        1)
        self.groupSyncReadVelocity = GroupSyncRead(self.portHandler, self.packetHandler,
                                                       self.parameters.ADDR_PRESENT_VELOCITY,
                                                       self.parameters.LEN_PRESENT_VELOCITY)
        self.groupSyncReadMoving = GroupSyncRead(self.portHandler, self.packetHandler,
                                                   self.parameters.ADDR_MOVING,
                                                   1)
        self.groupSyncReadMovingStatus = GroupSyncRead(self.portHandler, self.packetHandler,
                                                   self.parameters.ADDR_MOVING_STATUS,
                                                   1)
        self.groupSyncReadVelocityTrajectory = GroupSyncRead(self.portHandler, self.packetHandler,
                                                   self.parameters.ADDR_VELOCITY_TRAJECTORY,
                                                   self.parameters.LEN_VELOCITY_TRAJECTORY)
        self.groupSyncReadPositionTrajectory = GroupSyncRead(self.portHandler, self.packetHandler,
                                                   self.parameters.ADDR_POSITION_TRAJECTORY,
                                                   self.parameters.LEN_POSITION_TRAJECTORY)
        
        for DXL_ID in self.parameters.DXL_IDs:
            self.groupSyncReadPosition.addParam(DXL_ID)
            self.groupSyncReadGoalVelocity.addParam(DXL_ID)
            self.groupSyncReadVelocity.addParam(DXL_ID)
            self.groupSyncReadMoving.addParam(DXL_ID)
            self.groupSyncReadMovingStatus.addParam(DXL_ID)
            self.groupSyncReadVelocityTrajectory.addParam(DXL_ID)
            self.groupSyncReadPositionTrajectory.addParam(DXL_ID)

    
    def readMotorsData(self, groupSyncRead:GroupSyncRead):
        """Read data from the motor.

        Args:
            DXL_ID (int): The ID of the motor.
            addr (int): The address to read from.
            length (int): The length of the data to read.

        Returns:
            int: The value read from the motor.
        """
        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result != COMM_SUCCESS:
            return None
        result = list()

        for DXL_ID in self.parameters.DXL_IDs:
            dxl_getdata_result = groupSyncRead.isAvailable(DXL_ID, groupSyncRead.start_address, groupSyncRead.data_length)
            if dxl_getdata_result != True:
                return None
            result.append(groupSyncRead.getData(DXL_ID, groupSyncRead.start_address, groupSyncRead.data_length))

        return result


    def setOperatingMode(self, mode):
        """Set the operating mode of the motors.
        Args:
            mode (int): The operating mode to set.
                0: Current Control Mode
                1: Velocity Control Mode
                3: (Default) Position Control Mode
                4: Extended Position Control Mode
                5: Current-bqsed Position Control Mode
                16: PWM Control Mode

                See https://emanual.robotis.com/docs/en/dxl/x/xc330-t288/#operating-mode for more details.
        """
        if not self.connected:
            return

        for DXL_ID in self.parameters.DXL_IDs:
            value = self.packetHandler.read1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_OPERATING_MODE)
            if value != mode:
                logger.info("Motor mode changed to mode %s (%s,%s)" % (mode, self.parameters.DEVICENAME, DXL_ID))
                self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_OPERATING_MODE, mode)


    def setInVelocityMode(self):
        self.setOperatingMode(self.parameters.VELOCITY_MODE)


    def setInExtendedPositionMode(self):
        self.setOperatingMode(self.parameters.EXT_POSITION_MODE)


    def setInPositionMode(self):
        self.setOperatingMode(self.parameters.POSITION_MODE)


    def __writeMotorsData(self, group: GroupSyncWrite, values):
        """Helper function to write data to the motors.
        Args:
            group (GroupSyncWrite): The group sync write object.
            values (list of numbers): The values to write to the motors.
        """
        group.clearParam()
        for index, DXL_ID in enumerate(self.parameters.DXL_IDs):
            group.addParam(DXL_ID, _valToArray(values[index]))
        group.txPacket()


    def setGoalVelocity(self, speeds):
        """Set the goal velocity 

        Args:
            speeds (list of numbers): unit depends on motor type
        """
        self.__writeMotorsData(self.groupSyncWriteVelocity, speeds)


    def setGoalPosition(self, positions):
        """Set the goal position

        Args:
            positions (list of numbers): unit = 1 pulse
        """
        self.__writeMotorsData(self.groupSyncWritePosition, positions)


    def setVelocityProfile(self, max_vel):
        """Set the maximum velocities in position mode

        Args:
            positions (list of numbers): unit depends on the motor type
        """
        self.__writeMotorsData(self.groupSyncWriteVelocityProfile, max_vel)


    def getCurrentPosition(self) -> list:
        """Get the current position of the motors
        Returns:
            list of numbers: unit = 1 pulse
        """
        return self.readMotorsData(self.groupSyncReadPosition)
    

    def getGoalVelocity(self) -> list:
        """Get the goal velocity of the motors
        Returns:
            list of velocities: unit is rev/min
        """
        return self.readMotorsData(self.groupSyncReadGoalVelocity)
    

    def getCurrentVelocity(self) -> list:
        """Get the current velocity of the motors
        Returns:
            list of velocities: unit is rev/min
        """
        return self.readMotorsData(self.groupSyncReadVelocity)
    

    def isMoving(self) -> list:
        """Check if the motors are moving
        Returns:
            list of booleans: True if the motor is moving, False otherwise
        """
        return self.readMotorsData(self.groupSyncReadMoving)
    

    def getMovingStatus(self) -> list:
        """Get the moving status of the motors
        Returns:
            list of booleans: True if the motor is moving, False otherwise
        """
        return self.readMotorsData(self.groupSyncReadMovingStatus)
    

    def getVelocityTrajectory(self) -> list:
        """Get the velocity trajectory of the motors
        Returns:
            list of velocities: unit is rev/min
        """
        return self.readMotorsData(self.groupSyncReadVelocityTrajectory)
    

    def getPositionTrajectory(self) -> list:
        """Get the position trajectory of the motors
        Returns:
            list of positions: unit = 1 pulse
        """
        return self.readMotorsData(self.groupSyncReadPositionTrajectory)

    def open(self) -> None:
        """Open the port and set the baud rate.
        Raises:
            Exception: If the port cannot be opened or the baud rate cannot be set.
        """
        try:
            self.portHandler.openPort()
            self.portHandler.setBaudRate(self.parameters.BAUDRATE)
        except Exception as e:
            logger.error("[ERROR][MotorGroup]", str(e))
            self.connected = False


    def enableTorque(self):
        """Enable the torque of the motors."""
        if not self.connected:
            return

        for DXL_ID in self.parameters.DXL_IDs:
            self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_TORQUE_ENABLE,
                                              self.parameters.TORQUE_ENABLE)

    def close(self) -> None:
        """Close the port and disable the torque of the motors."""
        try:
            for DXL_ID in self.parameters.DXL_IDs:
                self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_TORQUE_ENABLE,
                                                  self.parameters.TORQUE_DISABLE)
            self.portHandler.closePort()
        except Exception as e:
            logger.error("[ERROR][MotorGroup]", str(e))
            pass


def _valToArray( val):
    """Convert a 32-bit integer to a list of 4 bytes.
    Args:
        val (int): The 32-bit integer to convert.
    Returns:
        list of bytes: The list of 4 bytes representing the integer.
    """
    return [DXL_LOBYTE(DXL_LOWORD(val)), DXL_HIBYTE(DXL_LOWORD(val)), DXL_LOBYTE(DXL_HIWORD(val)),
            DXL_HIBYTE(DXL_HIWORD(val))]