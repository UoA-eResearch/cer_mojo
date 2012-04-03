import os
import imp
import cluster
from cluster import config

_mod_path = os.path.dirname(cluster.__file__) + os.sep + 'monitoring' + os.sep + '%s' + os.sep + '%s.pyc'
_default_scheduler = config.default_scheduler.lower()

def create_node_instance(node_name, scheduler=_default_scheduler):
  ''' Create an instance of class Nodes. The correct package is picked based on the specifid scheduler '''
  mod_name='node' 
  mod_path = _mod_path % (scheduler, mod_name)
  py_mod = imp.load_compiled(mod_name,mod_path)
  return py_mod.Node(node_name) 

def create_nodes_instance(scheduler=_default_scheduler):
  ''' Create an instance of class Node. The correct package is picked based on the specifid scheduler '''
  mod_name='node'
  mod_path = _mod_path % (scheduler, mod_name)
  py_mod = imp.load_compiled(mod_name,mod_path)
  return py_mod.Nodes()

def create_job_instance(job_id, scheduler=_default_scheduler):
  ''' Create an instance of class Job. The correct package is picked based on the specifid scheduler '''
  mod_name='job'
  mod_path = _mod_path % (scheduler, mod_name)
  py_mod = imp.load_compiled(mod_name, mod_path)
  return py_mod.Job(job_id)

def create_queue_instance(scheduler=_default_scheduler):
  ''' Create an instance of class Queue. The correct package is picked based on the specifid scheduler '''
  mod_name='queue'
  mod_path = _mod_path % (scheduler, mod_name)
  py_mod = imp.load_compiled(mod_name, mod_path)
  return py_mod.Queue()

