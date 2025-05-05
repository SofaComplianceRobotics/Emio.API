#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from dynamixel_sdk import *
import emiomotorsparameters as MotorsParametersTemplate


class MotorGroup:

    def __init__(self, parameters: MotorsParametersTemplate) -> None:

        self.parameters = parameters
        self.connected = True

        print("Using %s on %s" % (self.parameters.MY_DXL, self.parameters.DEVICENAME))
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
        if not self.connected:
            return

        for DXL_ID in self.parameters.DXL_IDs:
            value = self.packetHandler.read1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_OPERATING_MODE)
            if value != mode:
                print("Motor mode changed to mode %s (%s,%s)" % (mode, self.parameters.DEVICENAME, DXL_ID))
                self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_OPERATING_MODE, mode)

    def setInVelocityMode(self):
        self.setOperatingMode(self.parameters.VELOCITY_MODE)

    def setInExtendedPositionMode(self):
        self.setOperatingMode(self.parameters.EXT_POSITION_MODE)

    def setInPositionMode(self):
        self.setOperatingMode(self.parameters.POSITION_MODE)

    def writeMotorsData(self, group: GroupSyncWrite, values):
        group.clearParam()
        for index, DXL_ID in enumerate(self.parameters.DXL_IDs):
            group.addParam(DXL_ID, valToArray(values[index]))
        group.txPacket()

    def setGoalVelocity(self, speeds):
        """Set the goal velocity 

        Args:
            speeds (list of numbers): unit depends on motor type
        """
        self.writeMotorsData(self.groupSyncWriteVelocity, speeds)

    def setGoalPosition(self, positions):
        """Set the goal position

        Args:
            positions (list of numbers): unit = 1 pulse
        """
        self.writeMotorsData(self.groupSyncWritePosition, positions)

    def setVelocityProfile(self, max_vel):
        """Set the maximum velocities in position mode

        Args:
            positions (list of numbers): unit depends on the motor type
        """
        self.writeMotorsData(self.groupSyncWriteVelocityProfile, max_vel)

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
        try:
            self.portHandler.openPort()
            self.portHandler.setBaudRate(self.parameters.BAUDRATE)
        except Exception as e:
            print("[ERROR][MotorGroup]", str(e))
            self.connected = False


    def enableTorque(self):
        if not self.connected:
            return

        for DXL_ID in self.parameters.DXL_IDs:
            self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_TORQUE_ENABLE,
                                              self.parameters.TORQUE_ENABLE)

    def close(self) -> None:
        try:
            for DXL_ID in self.parameters.DXL_IDs:
                self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, self.parameters.ADDR_TORQUE_ENABLE,
                                                  self.parameters.TORQUE_DISABLE)
            self.portHandler.closePort()
        except:
            pass


def valToArray(val):
    return [DXL_LOBYTE(DXL_LOWORD(val)), DXL_HIBYTE(DXL_LOWORD(val)), DXL_LOBYTE(DXL_HIWORD(val)),
            DXL_HIBYTE(DXL_HIWORD(val))]


def main_speed(Belt: MotorGroup) -> None:
    Belt.open()
    Belt.setInVelocityMode()
    Belt.enableTorque()
    Belt.setGoalVelocity((20, 20))
    print(Belt.getCurrentPosition())
    time.sleep(1)
    Belt.setGoalVelocity((0, 0))
    time.sleep(1)
    Belt.close()
    return


def main_position(Belt: MotorGroup) -> None:
    Belt.open()
    Belt.setInExtendedPositionMode()
    Belt.enableTorque()
    Belt.setVelocityProfile((20, 20))
    print(Belt.getCurrentPosition())
    Belt.setGoalPosition((588, 2772))
    time.sleep(1)
    print(Belt.getCurrentPosition())
    # Belt.setGoalVelocity((0,0))
    time.sleep(1)
    Belt.close()
    return


if __name__ == "__main__":

    Belt = MotorGroup(MotorsParametersTemplate)

    try:
        main_position(Belt)
        main_speed(Belt)
        main_position(Belt)
    except:
        print("Cannot connect to motors")
    finally:
        Belt.close()
