import socket

# wrapper to forward can frames
# over a custom udp protocol


class CustomCANOverUDPSock:
    def __init__(self):
        IP = '192.168.0.95'
        self.addressSend = (IP, 6000)
        self.addressRecv = (IP, 5000)
        # send
        self.udp_socket_send = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_socket_send.bind(('192.168.0.100', 5000))
        # recv
       # self.udp_socket_recv = socket.socket(
       #     family=socket.AF_INET, type=socket.SOCK_DGRAM)
       # self.udp_socket_recv.bind(self.addressRecv)

    def send(self, msg):
        import can2RNET
        import common
        import struct
        frame = can2RNET.dissect_frame(msg)
        frameId = frame.split("#")[0]
        newframe = ""

        if frameId == common.ID_JSM_INDUCE_ERROR:
            newframe = struct.pack("III", 2, 0, 0)
        elif frameId == common.ID_JOY_CONTROL:
            data = frame.split("#")[1]
            x = int(data[:2],16)
            y = int(data[2:4],16)
            newframe = struct.pack("IBBBBI", 1,0,0,y,x,0)

        self.udp_socket_send.sendto(newframe, self.addressSend)

    def recvfrom(self, size):
        msg, addr = self.udp_socket_recv.recvfrom(size)
        return msg, addr


def getUDP2CANSock():
    return CustomCANOverUDPSock()


def test():
    import can2RNET
    import common
    from time import sleep
    import struct
    import threading

    udp2canSock = getUDP2CANSock()

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


if __name__ == "__main__":
    import common
    import can2RNET

    cansocket = getUDP2CANSock()
    #can2RNET.cansend(cansocket, common.FRAME_JSM_INDUCE_ERROR)
    jf = common.createJoyFrame( -12, -29 )
    can2RNET.cansend(cansocket, jf )
    
    
