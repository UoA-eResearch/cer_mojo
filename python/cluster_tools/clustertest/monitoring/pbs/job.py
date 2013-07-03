import re, os, time
import clustertest.util.system_call as syscall
import clustertest.monitoring.pbs.config as config
from clustertest.util.stringutil import extract

class Job:

  _jobid = None
  _qstat_output = None
  _checkjob_output = None

  def __init__(self, jobid):
    if jobid is None or jobid.strip() == '':
      raise Exception('jobid must not be empty')
    self._jobid = jobid 

    # get information about the job
    command = '%s -f %s' % (config.qstat, self._jobid)
    (stdout,stderr,rc) = syscall.execute(command)
    if stdout == "":
      raise Exception('failed to get job information. stdout empty for command \'%s\'' % command)
    self._qstat_output = stdout

    command = '%s %s' % (config.checkjob, self._jobid)
    (stdout,stderr,rc) = syscall.execute(command)
    if stdout == "":
      raise Exception('failed to get job information. stdout empty for command \'%s\'' % command)
    self._checkjob_output = stdout

  def get_status(self):
    ''' Get job status '''
    status = extract(self._qstat_output, 'job_state =', '\n')
    if status == 'R':
      status = 'Running'
    elif status == 'Q':
      status = 'Queued'
    elif status == 'B':
      status == 'Blocked'
    return status

  def get_id(self):
    ''' Get job id '''
    return self._jobid

  def get_queue(self):
    ''' Get queue '''
    return extract(self._checkjob_output, 'class:', 'qos:')

  def get_user(self):
    ''' Get user '''
    return extract(self._checkjob_output, 'user:', 'group:')

  def get_job_directory(self):
    ''' Get job directory '''
    output_path = extract(self._qstat_output, 'Output_Path = ', '\n')
    if ":" in output_path:
      output_path = extract(output_path, ':')
    return os.path.dirname(output_path)

  def get_req_cores(self):
    ''' Get number of requested cpu cores'''
    return int(extract(self._checkjob_output, 'TaskCount:', 'Partition:'))

  def get_queued_time(self):
    ''' Get queued time '''
    t = extract(self._qstat_output, 'qtime = ', '\n')
    # format: Wed Mar 7 15:29:07 2012
    t = time.strptime(t, '%a %b %d %H:%M:%S %Y')
    t = time.strftime('%Y/%m/%d %H:%M:%S',t)  
    return t

  def get_start_time(self):
    ''' Get start time '''
    start_time = None
    if self.get_status() == 'Running':
        # format: Wed Mar 7 15:29:07 2012
        t = extract(self._qstat_output, 'start_time = ', '\n')
        t = time.strptime(t, '%a %b %d %H:%M:%S %Y')
        start_time = time.strftime('%Y/%m/%d %H:%M:%S',t) 
    return start_time

  def get_req_walltime(self):
    ''' Get requested walltime '''
    return extract(self._qstat_output, 'Resource_List.walltime =', '\n')

  def get_used_walltime(self):
    ''' Get remaining walltime [s] '''
    return extract(self._qstat_output, 'resources_used.walltime =', '\n')

  def get_req_mem_gb(self):
    ''' Get requested memory
        TODO: use qmgr to get default queue memory if qstat doesn't show any memory for the job
    '''
    tmp = extract(self._qstat_output, 'Resource_List.mem = ', '\n')
    if tmp == '':
      value = 0.0
    else:
      unit = tmp[-2:]
      value = tmp[:-2]
      if unit != "mb" and unit != "kb" and unit != "gb":
        raise Exception('Unknown unit for memory value: "%s"' % tmp)
      if unit == 'mb':
        value = float(value) / 1024
      if unit == 'kb':
        value = float(value) / (1024*1024)  
    return value

  def get_req_vmem_gb(self):
    ''' Get requested virtual memory '''
    tmp = extract(self._qstat_output, 'Resource_List.vmem = ', '\n')
    if tmp == '':
      value = 0.0
    else:
      unit = tmp[-2:]
      value = tmp[:-2]
      if unit != "mb" and unit != "kb" and unit != "gb":
        raise 'Unknown unit for virtual memory value: "%s"' % tmp
      if unit == 'mb':
        value = float(value) / 1024
      if unit == 'kb':
        value = float(value) / (1024*1024)
    return value

  def get_used_mem_gb(self):
    ''' Get used memory ''' 
    tmp = extract(self._qstat_output, 'resources_used.mem =', '\n')
    if tmp == '':
      value = 0.0
    else:
      unit = tmp[-2:]
      value = tmp[:-2]
      if unit != "mb" and unit != "kb" and unit != "gb":
        raise 'Unknown unit for used memory value: "%s"' % tmp
      if unit == 'mb':
        value = float(value) / 1024
      if unit == 'kb':
        value = float(value) / (1024*1024)
    return value

  def get_execution_nodes(self):
    ''' Get name of nodes that are involved in running this job '''
    result = {}
    if self.get_status() == 'Running':
      tmp = extract(self._checkjob_output, 'Allocated Nodes:', 'IWD:')
      tmp = re.sub('\r', ' ', tmp)
      tmp = re.sub('\n', ' ', tmp)
      tmp = re.sub('\[', '', tmp)
      tmp = re.sub('\]', ' ', tmp)
      tmp = tmp.strip()
      tmp = re.sub('\s+', ' ', tmp)
      nodes = tmp.split(' ')
      for node in nodes:
          (name, cores) = node.split(':') 
          result[name] = {}
          result[name]['cores'] = int(cores)
          result[name]['mem'] = (self.get_req_mem_gb() / self.get_req_cores()) * float(cores)
    return result

  def get_scheduler_command_details(self):
    ''' Get raw output of the PBS/Maui commands being used to gather job information '''
    tmp = {}
    tmp['%s -f %s' % (config.qstat,self._jobid)] = self._qstat_output 
    tmp['%s %s' % (config.checkjob,self._jobid)] = self._checkjob_output 
    return tmp
 
  def get_info(self):
    ''' Get all information about the job '''
    job={}
    job['id'] = self._jobid
    job['status'] = self.get_status()
    job['queue'] = self.get_queue()
    job['user'] = self.get_user()
    job['job_directory'] = self.get_job_directory()
    job['req_cores'] = self.get_req_cores()
    job['req_walltime'] = self.get_req_walltime()
    job['req_mem_gb'] = self.get_req_mem_gb()
    job['req_vmem_gb'] = self.get_req_vmem_gb()
    job['used_mem_gb'] = self.get_used_mem_gb()
    job['queued_time'] = self.get_queued_time()
    job['start_time'] = self.get_start_time()
    job['execution_nodes'] = self.get_execution_nodes()
    job['used_walltime'] = self.get_used_walltime()
    job['scheduler_command_details'] = self.get_scheduler_command_details()
    return job

