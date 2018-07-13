# #!/usr/bin/env python

# from setuptools import setup

requirements = ""
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
# f.close()

# # setup(name='TSAnalyse',
# #       version='1.0',
# #       description='TSAnalyse - A Framework for Time Series Analysis',
# #       author='Marcelo Santos',
# #       author_email='marcelo.santos@fc.up.pt',
# #       url='https://github.com/mefsantos/tsanalyse',
# #       packages=['.', 'tools'],
# #       install_requires=requirements
# #      )


setup(name='TSAnalyse',
      version='1.0',
      description='TSAnalyse - A Framework for Time Series Analysis',
      author='Marcelo Santos',
      author_email='marcelo.santos@fc.up.pt',
      url='https://github.com/mefsantos/tsanalyse',
      packages=['tools'],
      install_requires=requirements
     )



# from distutils.core import setup

# setup(name='TSAnalyse',
#       maintainer='Marcelo Santos',
#       maintainer_email='marcelo.santos@fc.up.pt',
#       url='https://github.com/mefsantos/tsanalyse',
#       version='1.0',
#       py_modules=['TSAnalyseDirect','TSAnalyseMultiScale','TSAnalyseFileBlocks'],
#       )
