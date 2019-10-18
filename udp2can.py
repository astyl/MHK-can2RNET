import socket

# wrapper to forward can frames
# over a custom udp protocol


class CustomCANOverUDPSock:
    def __init__(self, addressRecv, addressSend):
        self.addressRecv = addressRecv
        self.addressSend = addressSend
        # send
        self.udp_socket_send = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # recv
        self.udp_socket_recv = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_socket_recv.bind(self.addressRecv)

    def send(self, msg):
        self.udp_socket_send.sendto(msg, self.addressSend)

    def recvfrom(self, size):
        msg, addr = self.udp_socket_recv.recvfrom(size)
        return msg, addr


def getUDP2CANSock():
    addressSend = ('localhost', 6000)
    addressRecv = ('localhost', 10001)
    return CustomCANOverUDPSock(addressRecv, addressSend)


def getUDP2CANSockBis():
    addressSend = ('localhost', 10001)
    addressRecv = ('localhost', 6000)
    return CustomCANOverUDPSock(addressRecv, addressSend)


if __name__ == "__main__":
    import can2RNET
    import common
    from time import sleep
    import struct
    import threading

    udp2canSock = getUDP2CANSock()
    udp2canSockBis = getUDP2CANSockBis()

    msgA_tosend = common.FRAME_JSM_INDUCE_ERROR

    global msgA_received

    def fn_msgA_torecv():
        cf, addr = udp2canSockBis.recvfrom(16)
        global msgA_received
        msgA_received = can2RNET.dissect_frame(cf)

    def fn_msgA_tosend():
        can2RNET.cansend(udp2canSock, msgA_tosend)

    t1 = threading.Timer(1.0, fn_msgA_torecv)
    t2 = threading.Timer(1.2, fn_msgA_tosend)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert(msgA_tosend == msgA_received)
