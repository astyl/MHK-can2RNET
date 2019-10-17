import socket
import time
from can2RNET import *

addressSend = ('192.168.0.100', 6000)
addressRecv = ('192.168.0.100', 5000)


socketWrapper = SocketWrapper(addressRecv, addressSend)


class SendRunner(threading.Thread):
    def run(self):
        while True:
            sleep(0.1)
            print("sending joy frame")
            cansend(socketWrapper, "02000000#1FFF0000")


class RecvRunner(threading.Thread):
    def run(self):
        while True:
            sleep(0.1)
            cf, addr = socketWrapper.recvfrom(16)
            candump_frame = dissect_frame(cf)
            print("frame received:"+candump_frame)


#a = SendRunner()
b = RecvRunner()
# a.run()
b.run()
