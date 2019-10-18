import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])
logger = logging.getLogger()


ID_JSM_INDUCE_ERROR = '0c000000'
FRAME_JSM_INDUCE_ERROR = ID_JSM_INDUCE_ERROR + '#'
ID_JOY_CONTROL = '0c020000'  # may differ according to your setup


def dec2hex(dec, hexlen):  # convert dec to hex with leading 0s and no '0x'
    h = hex(int(dec))[2:]
    l = len(h)
    if h[l-1] == "L":
        l -= 1  # strip the 'L' that python int sticks on
    if h[l-2] == "x":
        h = '0'+hex(int(dec))[1:]
    return ('0'*hexlen+h)[l:l+hexlen]


def createJoyFrame(joystick_x, joystick_y):
    joyframe = ID_JOY_CONTROL+'#' + \
        dec2hex(joystick_x, 2)+dec2hex(joystick_y, 2)
    return joyframe
