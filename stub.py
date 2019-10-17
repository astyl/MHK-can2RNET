import socket
import time
from can2RNET import *

addressSend = ('localhost', 10000)
addressRecv = ('localhost', 10001)


class SocketWrapper:
    def __init__(self):
        self.udp_socket_send = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_socket_recv = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_socket_recv.bind(addressRecv)

    def send(self, msg):
        self.udp_socket_send.sendto(msg, addressSend)

    def recvfrom(self, size):
        return self.udp_socket_recv.recvfrom(size)


socketWrapper = SocketWrapper()


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
b = SendRunner()
a.run()
b.run()
