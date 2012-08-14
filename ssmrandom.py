#!/usr/bin/env python
__author__ = 'leifj'

import socket
import json
import os
import base64
import logging
import getopt
import sys
import random
import time

if not hasattr(socket, 'IP_MULTICAST_TTL'):
    setattr(socket, 'IP_MULTICAST_TTL', 33)
if not hasattr(socket, 'IP_ADD_SOURCE_MEMBERSHIP'):
    setattr(socket, 'IP_ADD_SOURCE_MEMBERSHIP', 39)

SSM_GROUP = '232.0.1.100'
SSM_PORT = '49999'
ENTROPY_DEVICE='/dev/urandom'
RNGD_PIPE = "/var/run/mc-socket"

if sys.argv[1] == 'recv':
    opts, args = getopt.getopt(sys.argv[2:], 'g:i:p:o:L:')
    opts = dict(opts)
    opts.setdefault('-i', '0.0.0.0')
    opts.setdefault('-p', SSM_PORT)
    opts.setdefault('-o', RNGD_PIPE)
    opts.setdefault('-g', SSM_GROUP)
    opts.setdefault('-L',"WARNING")
    loglevel = getattr(logging, opts['-L'].upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=loglevel)

    imr = (socket.inet_pton(socket.AF_INET, opts['-g']) +
           socket.inet_pton(socket.AF_INET, opts['-i']) +
           socket.inet_pton(socket.AF_INET, args[0]))

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_IP, socket.IP_ADD_SOURCE_MEMBERSHIP, imr)
    s.bind((opts['-g'], int(opts['-p'])))

    if not os.path.exists(RNGD_PIPE):
        os.mkfifo(RNGD_PIPE)

    with open(RNGD_PIPE,"w+") as fd:
        logging.debug("Starting...")
        while True:
            try:
                print "."
                msg = json.loads(s.recv(4096))
                data = base64.b64decode(msg['d'])
                logging.debug(msg)
                logging.info("received %d bytes" % len(data))
                fd.write(data)
                z = random.randint(1,20)
                logging.debug("sleeping %d seconds..." % z)
                time.sleep(z)
            except Exception,ex:
                logging.warning(ex)
                pass

elif sys.argv[1] == 'send' or sys.argv[1] == 'rawsend':
    opts, args = getopt.getopt(sys.argv[2:], 't:s:g:p:r:L:')
    opts = dict(opts)
    opts.setdefault('-p',SSM_PORT)
    opts.setdefault('-g',SSM_GROUP)
    opts.setdefault('-r',ENTROPY_DEVICE)
    opts.setdefault('-L',"WARNING")

    loglevel = getattr(logging, opts['-L'].upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=loglevel)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if '-t' in opts:
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, chr(int(opts['-t'])))
    if '-s' in opts:
        s.bind((opts['-s'], 0))
    s.connect((opts['-g'], int(opts['-p'])))
    with open(opts['-r']) as fd:
        while True:
            try:
                d = fd.read(1024)
                if sys.argv[1] == 'send':
                   e = base64.b64encode(d)
                   msg = {'s':opts['-r'],'p':'test','d': e}
                   s.send(json.dumps(msg))
                else:
                   s.send(d)
                logging.debug("sent %d bytes" % len(d))
		#time.sleep(1)
            except Exception,ex:
                logging.warning(ex)
                pass
else:
    raise ValueError("send or recv...")
