#!/usr/bin/env python
"""
Usage: ssmrandom {recv|send|rawsend} [options]+ [host IP(only for recv)]
       Common options:
        -h  print this message
        -v  print version information
        -g SSM multicast group (in 232.0.0.0/8)
        -i local bind address
        -p port
        -f stay in the foreground (and log to stderr)

        recv options:
        -s buffer size
        -o ouput PIPE

        send and rawsend options:

        -t TTL
        -s number of bytes of entropy payload
        -r input entropy device


ssmramdom can be operated in either send or receive mode. In send mode it will
read data from the input entropy device and will transmit it framed (except when
using rawsend) as JSON objects on a multicast group in SSM address space. In
receive mode ssmrandom will receive a random sample (using random sleep intervals
between 1 and 20 seconds) of such SSM messages and will write the entropy
payload to a PIPE where it can be consumed by rngd from the rng-tools package.

BUGS: only ipv4 is supported

NOTE that you may need to enable igmpv3 on your network for SSM to work.
"""
from logging import StreamHandler

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
from logging.handlers import SysLogHandler
import daemon
import lockfile

if not hasattr(socket, 'IP_MULTICAST_TTL'):
    setattr(socket, 'IP_MULTICAST_TTL', 33)
if not hasattr(socket, 'IP_ADD_SOURCE_MEMBERSHIP'):
    setattr(socket, 'IP_ADD_SOURCE_MEMBERSHIP', 39)

VERSION = "0.2"
PROTOCOL_VERSION = "1.0"

SSM_GROUP = '232.0.1.100'
SSM_PORT = '49999'
ENTROPY_DEVICE='/dev/urandom'
RNGD_PIPE = "/var/run/ssm-rng-pipe"
BUFSZ= "4096"
MSGSZ = "1024"
LOGLEVEL = "WARNING"
MCTTL = "32"
PIDFILE = '/var/run/ssmrandom.pid'

def _setup_logging(level,foreground=False):
    loglevel = getattr(logging, level.upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    if foreground:
        handler = StreamHandler()
    else:
        handler = SysLogHandler(address='/dev/log',facility=SysLogHandler.LOG_DAEMON)
    pid = os.getpid()
    formatter = logging.Formatter('ssmrandom['+str(pid)+'] %(message)s')
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(loglevel)

def usage():
    print __doc__

def _sender(s,group,port,bufsz,src,level,foreground):
    _setup_logging(level,foreground)
    with open(src) as fd:
        logging.info("entropy SSM transmitter v%s starting..." % VERSION)
        while True:
            try:
                logging.debug("about to read from %s" % src)
                d = fd.read(bufsz)
                if sys.argv[1] == 'send':
                    e = base64.b64encode(d)
                    msg = {'v': PROTOCOL_VERSION, 's': src, 'd': e}
                    s.send(json.dumps(msg))
                else: # rawsend
                    s.send(d)
                logging.debug("sending %d bytes of entropy to SSM:@%s:%d" % (len(d), group, port))
            except KeyboardInterrupt,ex:
                raise ex
            except Exception, ex:
                logging.warning(ex)
                pass

def _receiver(s,group, host, port,bufsz,dst,level,foreground):
    _setup_logging(level,foreground)
    with open(dst, "w+") as fd:
        logging.info("entropy SSM receiver v%s starting..." % VERSION)
        while True:
            try:
                msg = json.loads(s.recv(bufsz))
                data = base64.b64decode(msg['d'])
                logging.debug(msg)
                logging.info("sending %d bytes of entropy from SSM:%s@%s:%d upstream" % (len(data), host, group, port))
                fd.write(data)
                z = random.randint(1, 20)
                logging.debug("sleeping for %d seconds..." % z)
                time.sleep(z)
            except KeyboardInterrupt,ex:
                raise ex
            except Exception, ex:
                logging.warning(ex)
                time.sleep(1)
                pass

def main():
    try:
        _main()
    except KeyboardInterrupt:
        sys.exit()

def _main():
    opts = {}
    args = []
    flags = None

    if len(sys.argv) < 2:
        usage()
        sys.exit(2)

    if sys.argv[1] in ('recv'):
        flags = 'fh:L:vg:i:p:o:s:'
    elif sys.argv[1] in ('send','rawsend'):
        flags = 'fh:L:vt:s:g:p:r:s:'
    else:
        usage()
        sys.exit()

    try:
        opts, args = getopt.getopt(sys.argv[2:], flags)
        opts = dict(opts)
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    if '-h' in opts:
        usage()
        sys.exit()

    if '-v' in opts:
        print "ssmrandom version %s (c) NORDUnet A/S 2012" % VERSION
        sys.exit()

    opts.setdefault('-i','0.0.0.0')
    opts.setdefault('-p',SSM_PORT)
    opts.setdefault('-o',RNGD_PIPE)
    opts.setdefault('-g',SSM_GROUP)
    opts.setdefault('-L',LOGLEVEL)
    opts.setdefault('-r',ENTROPY_DEVICE)
    opts.setdefault('-L',LOGLEVEL)
    opts.setdefault('-t',MCTTL)

    if sys.argv[1] == 'recv':
        group = opts['-g']
        port = int(opts['-p'])
        opts.setdefault('-s',BUFSZ)
        if len(args) < 1:
            usage()
            sys.exit(2)

        host = args[0]
        dst = opts['-o']

        imr = (socket.inet_pton(socket.AF_INET, group) +
               socket.inet_pton(socket.AF_INET, opts['-i']) +
               socket.inet_pton(socket.AF_INET, host))

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_IP, socket.IP_ADD_SOURCE_MEMBERSHIP, imr)
        s.bind((group,port))

        if not os.path.exists(dst):
            os.mkfifo(dst)

        if not '-f' in opts:
            context = daemon.DaemonContext(working_directory='/tmp',files_preserve=[s])
            with context as ctx:
                _receiver(s,group,host,port,int(opts['-s']),dst,opts['-L'],False)
        else:
            _receiver(s,group,host,port,int(opts['-s']),dst,opts['-L'],True)

    elif sys.argv[1] == 'send' or sys.argv[1] == 'rawsend':
        opts.setdefault('-s',MSGSZ)
        group = opts['-g']
        port = int(opts['-p'])
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        if '-t' in opts:
            s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, chr(int(opts['-t'])))
        if '-i' in opts:
            s.bind((opts['-i'], 0))
        s.connect((group,port))

        if not '-f' in opts:
            context = daemon.DaemonContext(working_directory='/tmp',files_preserve=[s])
            with context as ctx:
                _sender(s,group,port,int(opts['-s']),opts['-r'],opts['-L'],False)
        else:
            _sender(s,group,port,int(opts['-s']),opts['-r'],opts['-L'],True)

if __name__ == '__main__':
    main()
