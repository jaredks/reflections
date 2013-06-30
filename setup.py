#!/usr/bin/env python
from distutils.core import setup
import reflections

setup(name='reflections',
      version=reflections.__version__,
      description='dict subclasses for bidirectional key, value access',
      author='Jared Suttles',
      url='https://github.com/jaredks/reflections',
      packages=['reflections'],
      package_data={'': ['LICENSE']},
      long_description=open('README.md').read(),
      license=open('LICENSE').read()
      )
