#!/usr/bin/env python

# Bootstrap installation of Distribute
import distribute_setup
distribute_setup.use_setuptools()

import os

from setuptools import setup

README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


PROJECT = u'ssmrandom'
VERSION = '0.2'
URL = ''
AUTHOR = u'Leif Johansson'
AUTHOR_EMAIL = u'leifj@sunet.se'
DESC = "Entropy distribution using SSM (source-specific multicast)"

def read_file(file_name):
    file_path = os.path.join(
        os.path.dirname(__file__),
        file_name
        )
    return open(file_path).read()

setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    long_description=long_description=README.rst + '\n\n' + NEWS
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license='BSD',
    namespace_packages=[],
    packages=[u'ssmrandom'],
    package_dir = {'': os.path.dirname(__file__)},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'python-daemon',
        'lockfile'
    ],
    entry_points = {
        'console_scripts':
            ['ssmrandom=ssmrandom:main']
    },
    classifiers=[
    	# see http://pypi.python.org/pypi?:action=list_classifiers
        # -*- Classifiers -*- 
        'License :: OSI Approved',
        'License :: OSI Approved :: BSD License',
        "Programming Language :: Python",
    ],
)
