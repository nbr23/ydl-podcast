#!/usr/bin/env python3

from setuptools import setup

setup(name='ydl_podcast',
      version='1.0',
      description='''A simple tool to generate Podcast-like RSS feeds from
      youtube (or other youtube-dl supported services) channels, using
      youtube-dl''',
      author='nbr23',
      author_email='max@23.tf',
      url='https://github.com/nbr23/ydl-podcast',
      license='MIT',
      packages=['ydl_podcast'],
      zip_safe=True,
      install_requires=[
          'youtube_dl',
          'pyyaml'
          ],
      entry_points={
          'console_scripts': [
              "ydl_podcast = ydl_podcast.__main__:main",
              ],
          },
      )
