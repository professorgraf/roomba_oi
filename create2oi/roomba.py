
import serial
import time
from enum import Enum


# Roomba modes enumeration
class RoombaConstants(Enum):
    SAFE = 131
    FULL = 2
    PASSIVE = None
    LIGHT_BUMPER_LEFT = 0
    LIGHT_BUMPER_FRONTLEFT = 1
    LIGHT_BUMPER_CENTERLEFT = 2
    LIGHT_BUMPER_CENTERRIGHT = 3
    LIGHT_BUMPER_FRONTRIGHT = 4
    LIGHT_BUMPER_RIGHT = 5
    NOT_CHARGING = 0
    RECONDITIONING_CHARGING = 1
    FULL_CHARGING = 2
    TRICKLE_CHARGING = 3
    CHARGING_WAITING = 4
    CHARGING_FAULT_CONDITION = 5


class RoombaSensors:
    def __init__(self):
        self.bump_left = False
        self.bump_right = False
        self.wheeldrop_left = False
        self.wheeldrop_right = False
        self.wall = False
        self.dirt_detect = 0
        self.light_bumper_signal = [0, 0, 0, 0, 0, 0]     # from left to right (bumper signals)

    def set_bumps_and_wheel_drops(self, value):
        self.bump_right = (value & 1) == 1
        self.bump_left = (value & 2) == 2
        self.wheeldrop_left = (value & 8) == 8
        self.wheeldrop_right = (value & 4) == 4

class RoombaBattery:
    def __init__(self):
        self.charging_state = RoombaConstants.NOT_CHARGING.value
        self.voltage = 0
        self.current = 0
        self.temperature = 0
        self.charge = 0
        self.capacity = 0



class Roomba:
    def __init__(self, port="/dev/cu.usbserial-AC01OAX0"):
        self.info = ""
        self.sensors = RoombaSensors()
        self.battery = RoombaBattery()
        self.started = False
        self.serial = serial.Serial(port, baudrate=115200, timeout=0.5)

    def reset(self):
        self.serial.write(bytes([7]))
        time.sleep(4)
        b = self.serial.read()
        while b:
            if b != bytes([0xFC]):
                self.info += str(b.decode('ascii'))
            b = self.serial.read()
        b = self.serial.read()
        while b:
            if b != bytes([0xFC]):
                self.info += str(b.decode('ascii'))
            b = self.serial.read()

    def start(self, mode=RoombaConstants.SAFE):
        if mode is None:
            self.serial.write(bytes([128]))
        else:
            self.serial.write(bytes([128, mode.value]))
        time.sleep(.1)
        while self.serial.read():
            pass
        self.started = True

    def stop_roomba_oi(self):
        self.serial.write(bytes([173]))
        time.sleep(.1)
        self.started = False

    def seekdock(self):
        if self.started:
            self.serial.write(bytes([143]))
        time.sleep(.1)

    def powerdown(self):
        if self.started:
            self.serial.write(bytes([133]))
        time.sleep(.1)
        self.started = False

    def drive(self, speed, radius=0x8000):
        if not self.started:
            self.start()
        v_lowbyte = speed & 0xFF
        v_highbyte = (speed & 0xFF00 ) >> 8
        r_lowbyte = radius & 0xFF
        r_highbyte = (radius >> 8 ) & 0xFF
        self.serial.write(bytes([137, v_highbyte, v_lowbyte, r_highbyte, r_lowbyte ]))
        time.sleep(.1)

    def drivedirect(self, speedR, speedL):
        if not self.started:
            self.start()
        l_lowbyte = speedL & 0xFF
        l_highbyte = (speedL & 0xFF00 ) >> 8
        r_lowbyte = speedR & 0xFF
        r_highbyte = (speedR >> 8 ) & 0xFF
        self.serial.write(bytes([145, r_highbyte, r_lowbyte, l_highbyte, l_lowbyte]))
        time.sleep(.1)

    def stop(self):
        self.drive(0, 0)

    def readsensordata(self, packetID):
        if not self.started:
            self.start()
        self.serial.write(bytes([142, packetID]))
        bytelist = bytes()
        b = self.serial.read()
        while b:
            bytelist += b
            b = self.serial.read()
        return bytelist

    def readenvironmentalsensors(self):
        bytelist = self.readsensordata(1)
        self.sensors.set_bumps_and_wheel_drops(bytelist[0])
        self.sensors.wall = bytelist[1] == 1
        self.sensors.dirt_detect = bytelist[8] == 1

    def readbatterystate(self):
        bl = self.readsensordata(3)
        self.battery.charging_state = bl[0]
        self.battery.voltage = int.from_bytes(bl[1:3], byteorder="big", signed=False)
        self.battery.current = int.from_bytes(bl[3:5], byteorder="big", signed=False)
        self.battery.temperature = bl[6]
        self.battery.charge = int.from_bytes(bl[7:9], byteorder="big", signed=False)
        self.battery.capacity = int.from_bytes(bl[9:11], byteorder="big", signed=False)

    def readlightbumpers(self):
        bytelist = self.readsensordata(106)

        for i in range(0, 6):
            self.sensors.light_bumper_signal[i] = int.from_bytes(bytelist[i*2:i*2+2], byteorder="big", signed=False)
