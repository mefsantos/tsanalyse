#!/usr/bin/env python

from setuptools import setup

requirements = ""
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
f.close()

setup(name='TSAnalyse',
      version='1.0',
      description='TSAnalyse - A Framework for Time Series Analysis',
      author='Marcelo Santos',
      author_email='marcelo.santos@fc.up.pt',
      url='https://github.com/mefsantos/tsanalyse',
      packages=['.', 'tools'],
      install_requires=requirements
     )

