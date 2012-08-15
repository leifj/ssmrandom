#!/usr/bin/env python
from logging.handlers import SysLogHandler

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

VERSION = "0.1"
PROTOCOL_VERSION = "1.0"

SSM_GROUP = '232.0.1.100'
SSM_PORT = '49999'
ENTROPY_DEVICE='/dev/urandom'
RNGD_PIPE = "/var/run/ssm-rng-pipe"
BUFSZ= "4096"
MSGSZ = "1024"
LOGLEVEL = "WARNING"
MCTTL = "32"

def _setup_logging(opts):
    loglevel = getattr(logging, opts['-L'].upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logger = logging.getLogger(__name__)
    handler = SysLogHandler(facility=SysLogHandler.LOG_AUTH)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler()
    logger.setLevel(loglevel)

if sys.argv[1] == 'recv':
    opts, args = getopt.getopt(sys.argv[2:], 'g:i:p:o:L:s:')
    opts = dict(opts)
    opts.setdefault('-i','0.0.0.0')
    opts.setdefault('-p',SSM_PORT)
    opts.setdefault('-o',RNGD_PIPE)
    opts.setdefault('-g',SSM_GROUP)
    opts.setdefault('-L',LOGLEVEL)
    opts.setdefault('-s',BUFSZ)
    _setup_logging(opts)

    imr = (socket.inet_pton(socket.AF_INET, opts['-g']) +
           socket.inet_pton(socket.AF_INET, opts['-i']) +
           socket.inet_pton(socket.AF_INET, args[0]))

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_IP, socket.IP_ADD_SOURCE_MEMBERSHIP, imr)
    s.bind((opts['-g'], int(opts['-p'])))

    if not os.path.exists(opts['-o']):
        os.mkfifo(opts['-o'])

    bufsz = int(opts['-s'])
    with open(opts['-o'],"w+") as fd:
        logging.debug("entropy SSM receiver v%s starting..." % VERSION)
        while True:
            try:
                msg = json.loads(s.recv(bufsz))
                data = base64.b64decode(msg['d'])
                logging.debug(msg)
                logging.info("received %d bytes" % len(data))
                fd.write(data)
            except Exception,ex:
                logging.warning(ex)
                pass
            finally:
                z = random.randint(1,20)
                logging.debug("sleeping %d seconds..." % z)
                time.sleep(z)

elif sys.argv[1] == 'send' or sys.argv[1] == 'rawsend':
    opts, args = getopt.getopt(sys.argv[2:], 't:s:g:p:r:L:s:')
    opts = dict(opts)
    opts.setdefault('-p',SSM_PORT)
    opts.setdefault('-g',SSM_GROUP)
    opts.setdefault('-r',ENTROPY_DEVICE)
    opts.setdefault('-L',LOGLEVEL)
    opts.setdefault('-t',MCTTL)
    opts.setdefault('-s',MSGSZ)

    _setup_logging(opts)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if '-t' in opts:
        s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, chr(int(opts['-t'])))
    if '-s' in opts:
        s.bind((opts['-s'], 0))
    s.connect((opts['-g'], int(opts['-p'])))
    bufsz = int(opts['-s'])
    with open(opts['-r']) as fd:
        logging.info("entropy SSM transmitter v%s starting..." % VERSION)
        while True:
            try:
                d = fd.read(bufsz)
                if sys.argv[1] == 'send':
                   e = base64.b64encode(d)
                   msg = {'v': PROTOCOL_VERSION,'s':opts['-r'],'d': e}
                   s.send(json.dumps(msg))
                else: # rawsend
                   s.send(d)
                logging.debug("sent %d bytes" % len(d))
            except Exception,ex:
                logging.warning(ex)
                pass
else:
    raise ValueError("send, rawsend or recv...")
