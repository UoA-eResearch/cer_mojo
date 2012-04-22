import re, os, time, datetime
import cluster.util.system_call as syscall
import cluster.monitoring.loadleveler.config as config
import cluster.util.timeutil as timeutil
from cluster.util.stringutil import extract
from cluster.util.stringutil import strip_lines
from cluster.util.stringutil import strip_multiple_ws

class Job:

  _jobid = None
  _llq_output = None
  _stripped_llq_output = None

  def __init__(self, jobid):
    if jobid is None or jobid.strip() == '':
      raise Exception('jobid must not be empty')
    self._jobid = jobid 

    # get information about the job
    command = '%s -l %s' % (config.llq, self._jobid)
    (stdout,stderr,rc) = syscall.execute(command)
    if "There is currently no job status to report" in stdout:
      raise Exception("job %s doesn't exist" % self._jobid) 
    if stdout == "":
      raise Exception('failed to get job information. stdout empty for command \'%s\'' % command)
    self._llq_output = stdout
    self._stripped_llq_output = strip_lines(stdout)

  def get_status(self):
    ''' Get job status '''
    return extract(self._llq_output, 'Status:', '\n')

  def get_id(self):
    ''' Get job id '''
    return self._jobid

  def get_queue(self):
    ''' Get queue '''
    return extract(self._llq_output, 'Class:', '\n')

  def get_user(self):
    ''' Get user '''
    return extract(self._llq_output, 'Owner:', '\n')

  def get_req_cores(self):
    ''' Get number of requested cpu cores'''
    cores = extract(self._llq_output, 'Total Tasks     :', '\n')
    if cores == '':
      return 1
    else:
      return int(cores)

  def get_queued_time(self):
    ''' Get queued time '''
    t = extract(self._llq_output, 'Queue Date:', '\n')
    # format: Mon 12 Mar 2012 09:52:43 PM NZDT
    # new format: Mon Mar 12 18:52:43 2012
    try:
      t = time.strptime(t, '%a %d %b %Y %I:%M:%S %p %Z')
    except:
      t = time.strptime(t, '%a %b %d %H:%M:%S %Y')
    t = time.strftime('%Y/%m/%d %H:%M:%S',t)
    return t

  def get_start_time(self):
    ''' Get start time '''
    start_time = None
    if self.get_status() == 'Running':
      t = extract(self._llq_output, 'Dispatch Time:', '\n')
      # format: Mon 12 Mar 2012 09:52:43 PM NZDT
      # new format: Mon Mar 12 18:52:43 2012
      try:
        t = time.strptime(t, '%a %d %b %Y %I:%M:%S %p %Z')
      except:
        t = time.strptime(t, '%a %b %d %H:%M:%S %Y')
      start_time = time.strftime('%Y/%m/%d %H:%M:%S',t)
    return start_time

  def get_req_walltime(self):
    ''' Get requested walltime '''
    t = extract(self._llq_output, 'Wall Clk Hard Limit: ', ' ')
    return t

  def get_used_walltime(self):
    ''' Get remaining walltime [s] '''
    start_time = self.get_start_time();
    if start_time is None:
      return timeutil.create_duration_string(0)
    else:
      start_time = timeutil.to_unix_timestamp(self.get_start_time(),'%Y/%m/%d %H:%M:%S')
      now = int(time.time())
      diff = now - start_time
      return timeutil.create_duration_string(diff)

  def get_req_mem_gb(self):
    ''' Get requested memory '''
    exp = '(Per Task)'
    mem = extract(self._llq_output, 'Node Resources:','\n')
    if mem != '':
      exp = '(Per Node)'
    else:
      mem = extract(self._llq_output, '   Resources:','\n')
    mem = extract(mem, 'ConsumableMemory(', ') ')
    val = float(mem[0:-2])
    unit = mem[-2:len(mem)]
    if unit.lower() == 'mb':
      val = float(val)/1024
    elif unit.lower() == 'kb':
      val = float(val)/(1024*1024)
    return '%.3f %s' % (val,exp)
    
  def get_req_vmem_gb(self):
    ''' Get requested virtual memory '''
    exp = '(Per Task)'
    mem = extract(self._llq_output, 'Node Resources:','\n')
    if mem != '':
      exp = '(Per Node)'
    else:
      mem = extract(self._llq_output, '   Resources:','\n')
    mem = extract(mem, 'ConsumableVirtualMemory(', ')')
    val = float(mem[0:-2])
    unit = mem[-2:len(mem)]
    if unit.lower() == 'mb':
      val = float(val)/1024
    elif unit.lower() == 'kb':
      val = float(val)/(1024*1024)
    return '%.3f %s' % (val,exp)

  def get_used_mem_gb(self):
    ''' Get used memory '''
    return 'N/A'

  def get_execution_nodes(self):
    ''' Get name of nodes that are involved in running this job '''
    hosts = {}
    ah = extract(self._llq_output, 'Allocated Host:','\n')
    if '' == ah:
      ah = extract(self._llq_output, 'Allocated Hosts :','Master Task')
      ah = ah.replace('+','').replace('::','')
      ah = strip_multiple_ws(ah).strip()
      machines = ah.split()
      tmp = extract(self._stripped_llq_output, 'Task\n----', '----------------')
      for machine in machines:
        m = {}
        m['cores'] = str(tmp.count(machine))
        hosts[machine] = m
        mem = self.get_req_mem_gb()
        if '(Per Node)' in mem:
          m['mem'] = mem.replace('(Per Node)','')
        elif '(Per Task)' in mem:
          m['mem'] = str(tmp.count(machine) * float(mem.replace('(Per Task)','')))
    else:
      machine = {}
      machine['cores'] = self.get_req_cores()
      machine['mem'] = self.get_req_mem_gb().replace('(Per Node)','')
      hosts[ah] = machine
    return hosts

  def get_scheduler_command_details(self):
    ''' Get raw output of the loadleveler commands being used to gather job information '''
    tmp = {}
    tmp['%s -l %s' % (config.llq,self._jobid)] = self._llq_output
    return tmp

  def get_info(self):
    ''' Get all information about the job '''
    job={}
    job['id'] = self._jobid
    job['status'] = self.get_status()
    job['queue'] = self.get_queue()
    job['user'] = self.get_user()
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

