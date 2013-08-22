#!/usr/bin/env python

from distutils.core import setup

setup(name='cluster_monitoring',
      version='1.0',
      description='Python Cluster Monitoring Utilities',
      author='Martin Feller',
      author_email='m.feller@auckland.ac.nz',
      packages=['clustertest', 'clustertest.util', 'clustertest.monitoring', 'clustertest.monitoring.loadleveler', 'clustertest.monitoring.loadleveler_affinity'],
)
