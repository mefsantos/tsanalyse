# #!/usr/bin/env python

import setuptools
from setuptools import setup

requirements = ""
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# setup(name='TSAnalyse',
#       maintainer='Marcelo Santos',
#       maintainer_email='marcelo.santos@fc.up.pt',
#       url='https://github.com/mefsantos/tsanalyse',
#       version='1.0',
#       py_modules=['TSAnalyseDirect','TSAnalyseMultiScale','TSAnalyseFileBlocks'],
#       )


setup(name='TSAnalyse',
      version='1.0',
      description='TSAnalyse - A Framework for Time Series Analysis',
      author='Marcelo Santos',
      author_email='marcelo.santos@fc.up.pt',
      url='https://github.com/mefsantos/tsanalyse',
      packages=setuptools.find_packages(),
#      dependency_links=['https://github.com/JohannesBuchner/paq/tree/master/paq8l'],
      install_requires=requirements
      )

