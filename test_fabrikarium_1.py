"""

ROS Binding for the RNet Wheelchair.
Currently supports teleoperation and battery readings; hoping to get odometry via wheel encoders.

To figure out 'non-trivial' rnet messages:
candump can0 -L | grep -Ev '02001100#|02000200#|00E#|03C30F0F#|0C140300#|0C140000#|1C0C0000#|14300000#|1C300004#'
"""
import socket
import sys
import os
import array
import threading
import can
import time
import numpy as np
import logging
import threading
from datetime import datetime
from collections import namedtuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])
logger = logging.getLogger()


def dec2hex(dec, hexlen):  # convert dec to hex with leading 0s and no '0x'
    h = hex(int(dec))[2:]
    l = len(h)
    if h[l-1] == "L":
        l -= 1  # strip the 'L' that python int sticks on
    if h[l-2] == "x":
        h = '0'+hex(int(dec))[1:]
    return ('0'*hexlen+h)[l:l+hexlen]


def aid_str(msg):
    if msg.id_type:
        return '{0:08x}'.format(msg.arbitration_id)
    else:
        return '{0:03x}'.format(msg.arbitration_id)


class RNETInterface(object):
    def __init__(self, channel='can0'):
        # data ...
        self._battery = None

        # joystick
        self._can = can.interface._get_class_for_interface("virtual")(channel=channel, bustype='socketcan_ctypes',
                                                                      )  # TODO : configure can_filters to filter joy input
        # battery can.interface.Bus
        self._can2 = can.interface._get_class_for_interface("virtual")(channel=channel, bustype='socketcan_ctypes',
                                                                       can_filters=[{"can_id": 0x1C0C0000, "can_mask": 0x1FFFF0FF, "extended": True}])

        self._battery = 10

        t = threading.Thread(target=self.recv_battery)
        t.daemon = True
        t.start()

    def recv_battery(self):
        while True:
            msg = self._can2.recv()
            self._battery = msg.data[0]

    def set_speed(self, v):
        if 0 <= v <= 0x64:
            return self.send('0a040100#'+dec2hex(v, 2))
        else:
            return False

    def beep(self):
        self.send("181c0100#0260000000000000")

    def sing(self):
        self.send("181C0100#2056080010560858")
        self.send("181C0100#105a205b00000000")

    def get_joy_frame(self):
        msg = self.recvfrom(timeout=0.1)
        if msg is None:
            return None
        return aid_str(msg)

    def disable_joy(self):
        for _ in range(0, 3):
            self.send('0c000000#')

    def send(self, msg_str, *args, **kwargs):
        msg_l = msg_str.split('#')
        rtr = ('#R' in msg_str)
        data = None
        if rtr:
            data = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        else:
            data = bytearray.fromhex(msg_l[1])
        msg = can.Message(
            timestamp=time.time(),
            is_remote_frame=rtr,
            extended_id=len(msg_l[0]) > 4,
            arbitration_id=int(msg_l[0], 16),
            dlc=0 if rtr else len(data),  # TODO : why 0?
            data=data
        )
        self._can.send(msg, *args, **kwargs)
        return True

    def recvfrom(self, *args, **kwargs):
        return self._can.recv(*args, **kwargs)


class RNETNode(object):
    def __init__(self):
        self._joy_frame = None  # '02001100'
        if not self._joy_frame is None:
            self._joy_frame = '{0:08x}'.format(self._joy_frame)
        self._speed = 5  # speed, percentage 0-100
        self._v_scale = 1.0
        self._w_scale = 1.0
        self._min_v = 0.0
        self._min_w = 0.0
        self._cmd_timeout = 0.1  # stops after timeout
        self._rnet = RNETInterface()
        self._cmd_linear = 0.0
        self._cmd_angular = 0.0

    def wait_rnet_joystick_frame(self, dur=0.2):
        frame_id = ''
        start = datetime.now()
        while frame_id[0:3] != '020':  # look for joystick frame ID
            frame_id = self._rnet.get_joy_frame()
            if frame_id is None or (datetime.now() - start).seconds > dur:
                logger.info('... Joy frame wait timed out')
                return False, None
        return True, frame_id

    def step(self):
        if self._rnet._battery is not None:
            logger.info("battery percentage {} %".format(
                (1.0 * self._rnet._battery)))

        cf = self._rnet.recvfrom(timeout=0.1)  # 16)
        if cf is not None:
            cf = aid_str(cf)

        # TODO : calibrate to m/s and scale accordingly
        # currently, v / w are expressed in fractions where 1 = max fw, -1 = max bw
        v = np.clip(self._v_scale * self._cmd_linear,  -1.0, 1.0)
        w = np.clip(self._w_scale * self._cmd_angular, -1.0, 1.0)

        if cf == self._joy_frame:
            # for joy : y=fw, x=turn; 0-256
            cmd_y = 0x100 + int(v * 100) & 0xFF
            cmd_x = 0x100 + int(-w * 100) & 0xFF

            if np.abs(v) > self._min_v or np.abs(w) > self._min_w:
                self._rnet.send(self._joy_frame + '#' +
                                dec2hex(cmd_x, 2) + dec2hex(cmd_y, 2))
            else:
                # below thresh, stop
                self._rnet.send(self._joy_frame + '#' +
                                dec2hex(0, 2) + dec2hex(0, 2))

    def save(self):
        pass

    def run(self):
        # 1 - check R-NET Joystick
        logger.info('Waiting for R-NET Joystick Frame ... ')
        suc, joy_frame = self.wait_rnet_joystick_frame(0.2)
        if suc:
            logger.info('Found R-NET Joystick frame: {}'.format(joy_frame))
            self._joy_frame = joy_frame
        else:
            if self._joy_frame is not None:
                logger.warn(
                    'No R-NET Joystick frame seen within minimum time')
                logger.warn(
                    'Using Supplied Joy Frame : {}'.format(self._joy_frame))
            else:
                logger.error(
                    'No R-NET Joystick frame seen within minimum time')
                return
        # set chair's speed to the lowest setting.
        suc = self._rnet.set_speed(self._speed)
        if not suc:
            logger.warn(
                'RNET Set SpeedRange Failed @ v={}' .format(self._speed))
            return
        logger.info(
            'RNET Set SpeedRange Success @ v={}' .format(self._speed))

        logger.info(
            "You chose to allow the R-Net Joystick - There may be some control issues.")

        while True:
            self.step()
            time.sleep(0.1)


if __name__ == "__main__":
    app = RNETNode()
    app.run()
