
Introduction
------------

This is an experiment with using source specific multicast to distribute 
high-quality entropy to consumers. The package contains a single script which 
can act as both a sender and receiver.

Installation
------------

# pip install ssmrandom

In order for this to work your network and hosts must be able to support 
SSM which in turn requires IGMP v3. For modern Linux and Windows this is
enabled by default. For some network equipment (eg juniper) you must enable
IGMP v3 explicitly (v2 is the default).


Quick Start
-----------

On the entropy producer (using the default multicast group and port):

    # ssmrandom send -r /dev/urandom -t 32 -g 232.0.1.100 -p 49999 -L info 

On the entropy consumer(s):

    # ssmrandom recv -o /var/run/rnd-pipe -g 232.0.1.100 -p 49999 <ip-of-producer>

    # rngd --rng-device=/var/run/rnd-pipe --rng-driver=stream --fill-watermark=90% --feed-interval=1


The idiots entropy distribution protocol (IEDP):
------------------------------------------------

Messages are JSON objects with 3 keys:

- v (version): the protocol version - '1.0' for this version
- s (source): identifies the source of the random data, eg the name of a hw device
- d (data): base64-encoded random data

Example

    {'s': '/dev/qrandom0','v':'1.0','d': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}

For security this can be signed, which is the reason for having framing at all.

Security issues
---------------

Collecting and adding external data to your entropy pool is a tricky issue. Adding
multicast to the mix makes it quite hard to analyze. This experiment is trying to 
investigate the properties of a system for distributing entropy in an efficient and
way. A couple of issues that are being investigated:

- how much entropy do you have to consume in order to pick a random sample
from the multicast feed?
- how expensive would it be to validate signatures on each json mesage?
- how good is rngtools at picking up bad entropy?
