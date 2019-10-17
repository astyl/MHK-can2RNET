import socket
import time
from can2RNET import *

print("connect")
can_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
print("bind")
can_socket.bind(('localhost', 10000))

can_socket.send = lambda x: can_socket.sendto(x)

while True:
    sleep(0.2)
    print("sending joy frame")
    cansend(can_socket, "02000000#1FFF0000")
