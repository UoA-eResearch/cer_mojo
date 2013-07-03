import re
import clustertest.util.system_call as syscall
import clustertest.monitoring.loadleveler_affinity.config as config
from clustertest.monitoring.loadleveler_affinity.job import Job
from clustertest.util.stringutil import extract

class Nodes:

  def __init__(self):
    pass
  
  def get_node_list(self, llstatus_output=''):
    ''' Get a list of all cluster nodes '''
    node_list = list()
    if llstatus_output == '':
      command = config.llstatus + ' -f %n'
      (stdout,stderr,rc) = syscall.execute(command)
      if stdout == "":
        raise Exception('failed to get node list. stdout empty for command \'%s\'' % command)
      llstatus_output = stdout
      
    for line in llstatus_output.split('\n')[1:]:
      line = line.strip()
      if not line == '' and not line[0] == ' ':
        if len(line.split()) > 1:
          continue
        if not line in config.node_blacklist:
          node_list.append(line)
    return sorted(node_list)

class Node:

  _nodename = None
  _node_listing = None
  _phys_mem_gb = None
  _avail_mem_gb = None
  _cores = None
  _avail_cores = None
  _job_ids = None

  def __init__(self, nodename):
    if nodename is None or nodename.strip() == '':
      raise Exception('nodename must not be empty')
    self._nodename = nodename

    # get information about the node
    command = config.llstatus + ' -r %cpu %m '  + self._nodename
    (stdout,stderr,rc) = syscall.execute(command)
    if stdout == "":
      raise Exception('failed to get node information. stdout empty for command \'%s\'' % command)
    (cores, phys_mem_gb) = stdout.split('!')
    self._cores = int(cores)
    self._phys_mem_gb = float(phys_mem_gb)/1024

  def get_phys_mem_gb(self):
    ''' Get physical memory [GB] '''
    return self._phys_mem_gb

  def get_job_ids(self):
    ''' Get ids of the jobs that run on this node '''
    job_ids = set()
    command = '%s -l' % config.llq
    (stdout,stderr,rc) = syscall.execute(command)
    ll_jobs = re.split('===== Job Step .* =====',stdout)
    for ll_job in ll_jobs:
      if len(ll_job) > 0:
        jobid = extract(ll_job, 'Job Step Id:', '\n')
        status = extract(ll_job, 'Status:', '\n')
        if status == "Running":
          node = extract(ll_job, 'Allocated Host:', '\n')
          if node != '': 
            if node == self._nodename:
              job_ids.add(jobid)
          else:
            nodes = extract(ll_job, 'Allocated Hosts :', 'Master Task')
            if self._nodename in nodes:
              job_ids.add(jobid)
    return sorted(list(job_ids))

  def get_avail_mem_gb(self): 
    ''' Get available memory that has not been requested by the running jobs [GB] '''
    if self._avail_mem_gb is None:
      req_mem_gb=0.0
      for jobid in self.get_job_ids():
        try:
          job = Job(jobid)
          req_mem_gb = req_mem_gb + float(job.get_execution_nodes()[self._nodename]['mem'])
        except:
          pass
      self._avail_mem_gb = (self.get_phys_mem_gb() - req_mem_gb)
    return self._avail_mem_gb

  def get_cores(self):
    ''' Get number of CPU cores '''
    return self._cores

  def get_avail_cores(self):
    ''' Get number of cpu cores that have not been requested by the running jobs '''
    if self._avail_cores is None:
      used_cores=0
      for jobid in self.get_job_ids():
        job = Job(jobid)
        nodes = job.get_execution_nodes()
        if self._nodename in nodes:
          used_cores += int(nodes[self._nodename]['cores'])
      self._avail_cores = (self.get_cores() - used_cores)
    return self._avail_cores
        
  def get_info(self):
    ''' Get all information about the node '''
    node={}
    node['name'] = self._nodename
    node['job_ids'] = self.get_job_ids()
    node['phys_mem_gb'] = self.get_phys_mem_gb()
    node['avail_mem_gb'] = self.get_avail_mem_gb()
    node['cores'] = self.get_cores()
    node['avail_cores'] = self.get_avail_cores()
    return node

