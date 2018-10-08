# #!/usr/bin/env python

import setuptools
from setuptools import setup
import subprocess as sp
import sys

LINUX = "linux"
MACOS = "darwin"

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# this may be useful for development only
# with open('pytest_requirements.txt') as f:
#     requirements.extend(f.read().splitlines())

# since the binary changes when built in linux and mac (and are incompatible) we need to build paq8l each time
# we install the package
try:
    sp.check_output('g++ algo/paq8l_src/paq8l.cpp -DUNIX -DNOASM -O2 -Os -s -fomit-frame-pointer -o algo/paq8l_src/paq8l',
                    shell=True,
                    stderr=sp.STDOUT)
except sp.CalledProcessError as e:
    print(e.output)

# copy the ppmd binary depending on the OS

if LINUX in sys.platform:
    try:
        sp.check_output('cp -f algo/ppmd_src/ppmd_linux algo/ppmd_src/ppmd', shell=True, stderr=sp.STDOUT)
    except sp.CalledProcessError as e:
        print(e.output)
else:
    try:
        sp.check_output('cp -f algo/ppmd_src/ppmd_darwin algo/ppmd_src/ppmd', shell=True, stderr=sp.STDOUT)
    except sp.CalledProcessError as e1:
        print(e1.output)

setup(name='TSAnalyse',
      version='1.0',
      description='TSAnalyse - A Framework for Time Series Analysis',
      author='Marcelo Santos',
      author_email='marcelo.santos@fc.up.pt',
      url='https://github.com/mefsantos/tsanalyse',
      packages=setuptools.find_packages(),
      python_requires='>=2.7.0',
      install_requires=requirements
      )

