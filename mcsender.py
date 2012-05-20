import socket
import base64
import json
import time

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

with open("/dev/urandom") as fd:
    while True: 
        d = fd.read(512)
        e = base64.b64encode(d)
        msg = {'s':'urandom','p':'test','d': e}
        sock.sendto(json.dumps(msg),(MCAST_GRP, MCAST_PORT))
        print msg
        time.sleep(1)
