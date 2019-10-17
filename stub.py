import socket
import time
from can2RNET import *

addressSend = ('localhost', 10000)
addressRecv = ('localhost', 10001)


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
            print("receiving frame", candump_frame)


a = SendRunner()
b = RecvRunner()
a.run()
b.run()
