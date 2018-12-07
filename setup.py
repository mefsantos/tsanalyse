#!/usr/bin/env python

import os
import sys
import setuptools
import subprocess as sp
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop

LINUX = "linux"
MACOS = "darwin"

requirements_txt = 'requirements.txt'
pytest_requirements_txt = 'pytest_requirements.txt'

project_dir_path = os.path.dirname(os.path.realpath(__file__))
requirements_path = os.path.join(project_dir_path, requirements_txt)

# try:
#     with open(requirements_txt) as f:
#         requirements = f.read().splitlines()
# except IOError as ioe:
# print("%s. Trying %s" % (ioe, requirements_path))
with open(requirements_path) as f:
    requirements = f.read().splitlines()

try:
    command = "pip install -r %s".format(requirements_path)
    sp.check_output(command, shell=True, stderr=sp.STDOUT)
except sp.CalledProcessError as e:
    print(e.output)

# pytest_requirements_path = os.path.join(project_dir_path, pytest_requirements_txt)
# this may be useful for development only
# with open(pytest_requirements_path) as f:
#     requirements.extend(f.read().splitlines())


def friendly(command_subclass):
    """A decorator for classes subclassing one of the setuptools commands.

    It modifies the run() method so that it prints a friendly greeting.
    """
    orig_run = command_subclass.run

    def modified_run(self):
        # since the binary changes when built in linux and mac (and are incompatible) we need to build paq8l each time
        # we install the package
        try:
            command = "g++ {0}/algo/paq8l_src/paq8l.cpp -DUNIX -DNOASM -O2 -Os -s -fomit-frame-pointer " \
                      "-o {0}/algo/paq8l_src/paq8l".format(project_dir_path)
            sp.check_output(command, shell=True, stderr=sp.STDOUT)
        except sp.CalledProcessError as e:
            print(e.output)
        else:
            print("Finished building paq8l")
        # copy the ppmd binary depending on the OS
        if LINUX in sys.platform:
            try:
                command = "cp -f {0}/algo/ppmd_src/ppmd_linux {0}/algo/ppmd_src/ppmd".format(project_dir_path)
                sp.check_output(command, shell=True, stderr=sp.STDOUT)
            except sp.CalledProcessError as e:
                print(e.output)
            else:
                print("Copied Linux ppmd binary file")
        else:
            try:
                command = "cp -f {0}/algo/ppmd_src/ppmd_darwin {0}/algo/ppmd_src/ppmd".format(project_dir_path)
                sp.check_output(command, shell=True, stderr=sp.STDOUT)
            except sp.CalledProcessError as e1:
                print(e1.output)
            else:
                print("Copied Darwin ppmd binary file")

        # now we probably will need to add these paths to the either the user's $PYTHONPATH or $PATH
        orig_run(self)

    command_subclass.run = modified_run
    return command_subclass


@friendly
class CustomDevelopCommand(develop):
    pass


@friendly
class CustomInstallCommand(install):
    pass


setup(name='TSAnalyse',
      version='1.0',
      description='TSAnalyse - A Framework for Time Series Analysis',
      author='Marcelo Santos',
      author_email='marcelo.santos@fc.up.pt',
      url='https://github.com/mefsantos/tsanalyse',
      packages=setuptools.find_packages(),
      python_requires='>=2.7.0',
      install_requires=requirements,
      cmdclass={
          'install': CustomInstallCommand,
      })
