import os
import sys
import unittest
from cluster.monitoring.loadleveler_affinity.job import Job as Job
from .config import testjobs

class JobTests(unittest.TestCase):

  basepath = '%s%s%s%s' % (os.path.dirname(__file__), os.sep, 'data', os.sep)
  
  def test_get_user(self):
      jobfile = '%s%s' % (self.basepath, 'serial_singlethreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_user(), 'ymoh699')

  def test_get_job_directory(self):
      jobfile = '%s%s' % (self.basepath, 'serial_singlethreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_job_directory(), '/home/ymoh699')

  def test_get_req_cores_serialjob(self):
      jobfile = '%s%s' % (self.basepath, 'serial_singlethreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_req_cores(), 1)

  def test_get_req_cores_multithreadedjob(self):
      jobfile = '%s%s' % (self.basepath, 'serial_multithreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_req_cores(), 4)
      self.assertEqual(job.get_req_mem_gb(), {'split_mode': 'task', 'value': '4.000'})

  def test_get_req_cores_mpijob(self):
      jobfile = '%s%s' % (self.basepath, 'parallel_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_req_cores(), 15)

  def test_get_execution_nodes_serialjob(self):
      jobfile = '%s%s' % (self.basepath, 'serial_singlethreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_execution_nodes(), 'compute-a1-063-p')

  def test_get_execution_nodes_multithreadedjob(self):
      jobfile = '%s%s' % (self.basepath, 'serial_multithreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_execution_nodes(), 'compute-c1-009-p')


    
  def test_get_req_mem_gb_serialjob(self):
      jobfile = '%s%s' % (self.basepath, 'serial_singlethreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_req_mem_gb(), {'split_mode': 'task', 'value': '20.000'})

  def test_get_starttime(self):
      jobfile = '%s%s' % (self.basepath, 'serial_singlethreaded_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_start_time(), '2013/08/18 08:14:14')

  def test_parallel_01(self):
      jobfile = '%s%s' % (self.basepath, 'parallel_01.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_user(), 'mfel395')
      self.assertEqual(job.get_job_directory(), '/home/mfel395/jobs/mpi')
      self.assertEqual(job.get_req_cores(), 15)
      self.assertEqual(job.get_req_mem_gb(), {'split_mode': 'task', 'value': '15.000'})
    
  def test_parallel_03(self):
      jobfile = '%s%s' % (self.basepath, 'parallel_03.data')
      job = Job(llq_output = open(jobfile, 'r').read())
      self.assertEqual(job.get_user(), 'swas118')
      self.assertEqual(job.get_job_directory(), '/home/swas118/gpfs1m/velo/dtCheck/2')
      self.assertEqual(job.get_req_cores(), 40)
      self.assertEqual(job.get_req_mem_gb(), {'split_mode': 'task', 'value': '3.000'})
      self.assertEqual(job.get_req_mem_gb(node='compute-c1-002-p'), {'split_mode': 'task', 'value': '30.000'})
    
    
