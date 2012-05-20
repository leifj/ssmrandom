import socket
import struct
import json
import os
import base64

MCAST_GRP = '224.1.1.1'
RNGD_PIPE = "/var/run/mc-socket"
MCAST_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

if not os.path.exists(RNGD_PIPE):
   os.mkfifo(RNGD_PIPE)

with open(RNGD_PIPE,"w+") as fd:
    print "starting up..."
    while True:
        try:
            msg = json.loads(sock.recv(1024))
            data = base64.b64decode(msg['d'])
            #print "%d bytes" % len(data)
            fd.write(data)
        except Exception: 
            pass
