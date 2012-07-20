import re, os
import cluster.util.system_call as syscall
import cluster.monitoring.pbs.config as config
from cluster.util.stringutil import extract
from cluster.monitoring.pbs.job import Job as PBSJob

class Nodes:

  def get_node_list(self):
    ''' Get a list of all cluster nodes '''
    node_list = list()
    command = '%s' % config.pbsnodes
    (stdout,stderr,rc) = syscall.execute(command)
    if stdout == "":
      raise Exception('failed to get node list. stdout empty for command \'%s\'' % command)
    for line in stdout.split('\n'):
      if not line == '' and not line[0] == ' ' and not line in config.node_blacklist:
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
    command = '%s -c "list node %s"' % (config.qmgr,self._nodename)
    (stdout,stderr,rc) = syscall.execute(command)
    if stdout == "":
      raise Exception('failed to get node information. stdout empty for command \'%s\'' % command)
    self._node_listing = stdout

  def get_phys_mem_gb(self):
    ''' Get physical memory [GB] '''
    if self._phys_mem_gb is None:
      pm = extract(self._node_listing, 'physmem=', 'kb')
      self._phys_mem_gb = float(pm)/(1024*1024)
    return self._phys_mem_gb

  def get_job_ids(self):
    ''' Get ids of the jobs that run on this node '''
    if self._job_ids is None:
      var = extract(self._node_listing, "jobs = ", "status = ")
      if var != "":
        var = re.sub('\s+',' ',var)
        var = re.sub('[0-9]*\/','',var)
        var = re.sub(',','',var)
        var = re.sub('\.cluster\.local','',var)
        self._job_ids = sorted(list(set(var.split())))
      else:
        self._job_ids = []
    return self._job_ids
   
  def get_avail_mem_gb(self): 
    ''' Get available memory that has not been requested by the running jobs [GB] '''
    if self._avail_mem_gb is None:
      req_mem_gb=0.0
      for jobid in self.get_job_ids():
        try:
          job = PBSJob(jobid)
          req_mem_gb = req_mem_gb + job.get_execution_nodes()[self._nodename]['mem']
        except:
          pass
      self._avail_mem_gb = (self.get_phys_mem_gb() - req_mem_gb)
    return self._avail_mem_gb

  def get_cores(self):
    ''' Get number of CPU cores '''
    if self._cores is None:
      self._cores = int(extract(self._node_listing, 'np = ', '\n'))
    return self._cores

  def get_avail_cores(self):
    ''' Get number of cpu cores that have not been requested by the running jobs '''
    if self._avail_cores is None:
      used_cores=0
      var = extract(self._node_listing, 'jobs = ', 'status = ')
      if var != '':
        used_cores = var.count('/')
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

