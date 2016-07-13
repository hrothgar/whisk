#!/usr/bin/python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name = 'Whisk',
      version = '1.0',
      description = 'A lightweight engine for making beautiful documents.',
      author = 'Hrothgar',
      author_email = 'hrothgarrrr@gmail.com',
      url = 'http://github.com/hrothgar/whisk',
      license = 'GPL v2',
      packages = find_packages(),
      entry_points = {
        'console_scripts': [
          'whisk = whisk.whisk:main',
        ]
      },
      package_data = {
          # '': ['*.txt']
      }
)
