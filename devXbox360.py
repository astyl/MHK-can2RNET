# Translate USB joystick x/y axis to Rnet cmd

# joystick based on: https://www.kernel.org/doc/Documentation/input/joystick-api.txt

import os
import array
import threading
from fcntl import ioctl
import struct
from time import time, sleep
from common import logger


class DevXbox360(threading.Thread):
    axis_map = []
    button_map = []
    xthreshold = 8 * 0x10000 / 128
    ythreshold = 8 * 0x10000 / 128

    joystick_x = 0
    joystick_y = 0

    # We'll store the states here.
    axis_states = {}
    button_states = {}

    # These constants were borrowed from linux/input.h
    axis_names = {
        0x00: 'x',
        0x01: 'y',
        0x02: 'z',
        0x03: 'rx',
        0x04: 'ry',
        0x05: 'rz',
        0x06: 'trottle',
        0x07: 'rudder',
        0x08: 'wheel',
        0x09: 'gas',
        0x0a: 'brake',
        0x10: 'hat0x',
        0x11: 'hat0y',
        0x12: 'hat1x',
        0x13: 'hat1y',
        0x14: 'hat2x',
        0x15: 'hat2y',
        0x16: 'hat3x',
        0x17: 'hat3y',
        0x18: 'pressure',
        0x19: 'distance',
        0x1a: 'tilt_x',
        0x1b: 'tilt_y',
        0x1c: 'tool_width',
        0x20: 'volume',
        0x28: 'misc',
    }

    button_names = {
        0x120: 'trigger',
        0x121: 'thumb',
        0x122: 'thumb2',
        0x123: 'top',
        0x124: 'top2',
        0x125: 'pinkie',
        0x126: 'base',
        0x127: 'base2',
        0x128: 'base3',
        0x129: 'base4',
        0x12a: 'base5',
        0x12b: 'base6',
        0x12f: 'dead',
        0x130: 'a',
        0x131: 'b',
        0x132: 'c',
        0x133: 'x',
        0x134: 'y',
        0x135: 'z',
        0x136: 'tl',
        0x137: 'tr',
        0x138: 'tl2',
        0x139: 'tr2',
        0x13a: 'select',
        0x13b: 'start',
        0x13c: 'mode',
        0x13d: 'thumbl',
        0x13e: 'thumbr',

        0x220: 'dpad_up',
        0x221: 'dpad_down',
        0x222: 'dpad_left',
        0x223: 'dpad_right',

        # XBox 360 controller uses these codes.
        0x2c0: 'dpad_left',
        0x2c1: 'dpad_right',
        0x2c2: 'dpad_up',
        0x2c3: 'dpad_down',
    }

    # jsId : joystick device id
    def __init__(self, jsId=0):
        threading.Thread.__init__(self, name="XBox360")

        # Iterate over the joystick devices.
        logger.info('Available devices:')

        for fn in os.listdir('/dev/input'):
            if fn.startswith('js'):
                logger.info('  /dev/input/%s' % (fn))

        # Open the joystick device.
        try:
            fn = '/dev/input/js%d' % jsId
            logger.info('Opening %s...' % fn)
            self.jsdev = open(fn, 'rb')

            logger.info('Using USB joystick @ ' +
                        str(self.jsdev).split("'")[1])

        except IOError as e:
            logger.error('No joystick at ' + fn)
            raise e

        # Get the device name.
        # buf = bytearray(63)
        buf = bytearray([0] * 64)
        # JSIOCGNAME(len)
        ioctl(self.jsdev, 0x80006a13 + (0x10000 * len(buf)), buf)
        js_name = buf

        logger.info('Device name: %s' % js_name)

        # Get number of axes and buttons.
        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016a11, buf)  # JSIOCGAXES
        num_axes = buf[0]

        buf = array.array('B', [0])
        ioctl(self.jsdev, 0x80016a12, buf)  # JSIOCGBUTTONS
        num_buttons = buf[0]

        # Get the axis map.
        buf = array.array('B', [0] * 0x40)
        ioctl(self.jsdev, 0x80406a32, buf)  # JSIOCGAXMAP

        for axis in buf[:num_axes]:
            axis_name = self.axis_names.get(axis, 'unknown(0x%02x)' % axis)
            self.axis_map.append(axis_name)
            self.axis_states[axis_name] = 0.0

        # Get the button map.
        buf = array.array('H', [0] * 200)
        ioctl(self.jsdev, 0x80406a34, buf)  # JSIOCGBTNMAP

        for btn in buf[:num_buttons]:
            btn_name = self.button_names.get(btn, 'unknown(0x%03x)' % btn)
            self.button_map.append(btn_name)
            self.button_states[btn_name] = 0

        logger.info('%d axes found: %s' % (num_axes, ', '.join(self.axis_map)))
        logger.info('%d buttons found: %s' %
                    (num_buttons, ', '.join(self.button_map)))
        self.joystick_x = 0
        self.joystick_y = 0
        self.stopRun = False

    def run(self):
        while not self.stopRun:
            try:
                evbuf = self.jsdev.read(8)
                jtime, jvalue, jtype, jnumber = struct.unpack('IhBB', evbuf)

                if jtype & 0x02:
                    axis = self.axis_map[jnumber]
                    if (axis == 'x'):
                        if abs(jvalue) > self.xthreshold:
                            self.joystick_x = 0x100 + \
                                int(jvalue * 100 / 128) >> 8 & 0xFF
                        else:
                            self.joystick_x = 0
                    elif (axis == 'y'):
                        if abs(jvalue) > self.ythreshold:
                            self.joystick_y = 0x100 - \
                                int(jvalue * 100 / 128) >> 8 & 0xFF
                        else:
                            self.joystick_y = 0

            except Exception as e:
                logger.error("Error reading USB: joystick")
                self.joystick_x = 0
                self.joystick_y = 0
                self.stopRun = True
                raise e

    def waitJoystickCentered(self):
        logger.info('waiting for joystick to be centered')
        while (self.joystick_x != 0 or self.joystick_y != 0):
            logger.info('joystick not centered')


class Watcher(threading.Thread):
    def __init__(self, devXbox360):
        threading.Thread.__init__(self)
        self.devXbox360 = devXbox360
        self.stopRun = False

    def run(self):
        started_time = time()
        while not self.stopRun:
            sleep(0.1)
            logger.info("{time} \tX: {joyX} \tY: {joyY}".format(
                time=round(time()-started_time, 2),
                joyX=self.devXbox360.joystick_x,
                joyY=self.devXbox360.joystick_y))


if __name__ == "__main__":
    devXbox360 = DevXbox360()
    watcher = Watcher(devXbox360)

    devXbox360.start()
    watcher.start()
