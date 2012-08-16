#!/usr/bin/env python

from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


PROJECT = u'ssmrandom'
VERSION = '0.2'
URL = 'http://blogs.mnt.se'
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
    long_description=README + '\n\n' + NEWS,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license='BSD',
    namespace_packages=[],
    packages=find_packages('src'),
    package_dir = {'': 'src'},
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
