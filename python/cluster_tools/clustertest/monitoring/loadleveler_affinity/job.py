import time
import clustertest.util.system_call as syscall
import clustertest.monitoring.loadleveler_affinity.config as config
import clustertest.config as clusterconfig
import clustertest.util.timeutil as timeutil
from clustertest.util.stringutil import extract
from clustertest.util.stringutil import strip_lines

class Job:

  _jobid = None
  _llq_output = None
  _stripped_llq_output = None

  def __init__(self, jobid=None, llq_output=None):
    if (jobid is None or jobid.strip() is '') and (llq_output is None or llq_output.strip() is ''):
      raise Exception('jobid must not be empty')

    if llq_output is None or llq_output is '':
      # get information about the job using the scheduler command
      self._jobid = jobid 
      command = '%s -l %s' % (config.llq, self._jobid)
      (stdout,stderr,rc) = syscall.execute('%s %s' % (clusterconfig.scheduler_command_prefix, command))
      if "There is currently no job status to report" in stdout:
        raise Exception("job %s doesn't exist" % self._jobid) 
      if stdout == "":
        raise Exception('failed to get job information. stdout empty for command \'%s\'' % command)
      self._llq_output = stdout
      self._stripped_llq_output = strip_lines(stdout)
    else:
      self._jobid = extract(llq_output, 'Job Step Id:', '\n')
      self._llq_output = llq_output
      self._stripped_llq_output = strip_lines(llq_output)
    
  def __calculate_cores(self, cores_string):
    cores = 1
    if "-" in cores_string:
      range_array = cores_string.split("-")
      if len(range_array) == 2:
        try:
          cores = int(range_array[1]) - int(range_array[0]) + 1
        except:
          raise Exception("got cores string: %s" % cores_string)
      else:
        raise Exception("Unexpected error while calculating the requested number of CPU cores")
    return cores

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

  def get_job_directory(self):
    ''' Get job directory '''
    return extract(self._llq_output, 'Initial Working Dir:', '\n')

  def get_req_cores(self, node=''):
    ''' Get number of requested cpu cores. 
        If a node is passed as parameter, only return the cores for the given node 
    '''
    cores = 0
    if 'Task\n----' in self._stripped_llq_output:
      # job is MPI job
      task = extract(self._stripped_llq_output, 'Task\n----', '------------------------------' )
      task_instances = task.split('Task Instance:')[1:]
      for task_instance in task_instances:
        if node is '' or '%s%s'%(node,':') in task_instance:
          if '<' in task_instance:
            cores_string = extract(task_instance, '<', '>')
            if " " in cores_string:
              # multiple cores specified, like < 7 9-10 >
              core_ranges = cores_string.split(' ')
              for core_range in core_ranges:
                cores += self.__calculate_cores(core_range)
            else:
              # only one core, or core-range specified, like < 7 > or < 6-9 >
              cores += self.__calculate_cores(cores_string)
          else:
            cores += 1
    else: 
      # serial job
      allocated_host = extract(self._stripped_llq_output, 'Allocated Host:', '\n')
      parallel_threads = extract(self._stripped_llq_output, 'Parallel Threads:', '\n')
      if allocated_host is '':
        raise Exception('Unexpected behavior for job %s. This needs to be fixed.' % self._jobid)
      else:
        if parallel_threads != "1":
          cores = parallel_threads
        elif node is '' or node is allocated_host:
          cores = 1
    return cores
    
  def get_queued_time(self):
    ''' Get queued time '''
    t = extract(self._llq_output, 'Queue Date:', '\n')
    # format: Mon 12 Mar 2012 09:52:43 PM NZDT
    # new format: Mon Mar 12 18:52:43 2012
    try:
      t = time.strptime(t, '%a %d %b %Y %H:%M:%S %p %Z')
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
        t = time.strptime(t, '%a %d %b %Y %H:%M:%S %Z')
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

  def __get_req_mem_gb(self, memory_type, node=''):
    ''' Get requested memory either physical or virtual memory, defined by parameter 'type' '''
    mem = {}
    mem['split_mode'] = 'task'
    resource_string = extract(self._llq_output, '   Resources:','\n')
    val = extract(resource_string, '%s(' % memory_type, ')')
    if val is '':
      mem['value'] = 'N/A'
    else:
      tmpval = float(val[0:-2])
      unit = val[-2:len(val)]
      if unit.lower() == 'mb':
        tmpval = float(tmpval)/1024
      elif unit.lower() == 'kb':
        tmpval = float(tmpval)/(1024*1024)
      mem['value'] = '%.3f' % tmpval
    return mem  
    
  def get_req_mem_gb(self, node=''):
    ''' Get requested physical memory '''
    return self.__get_req_mem_gb('ConsumableMemory', node)
  
  def get_req_vmem_gb(self, node=''):
    ''' Get requested virtual memory '''
    return self.__get_req_mem_gb('ConsumableVirtualMemory', node)

  def get_used_mem_gb(self):
    ''' Get used memory '''
    return 'N/A'

  def get_execution_nodes(self):
    ''' Get name of nodes that are involved in running this job '''
    hosts = {}
    ah = extract(self._llq_output, 'Allocated Host:','\n')
    if '' == ah:
      ah = extract(self._llq_output, 'Allocated Hosts :','Master Task')
      machines = ah.splitlines();
      for i in range(len(machines)):
        if '+' in machines[i]:
          machines[i] = extract(machines[i], '+', '::')
        else:
          machines[i] = extract(machines[i], None, '::')
      tmp = extract(self._stripped_llq_output, 'Task\n----', '----------------')
      for machine in machines:
        m = {}
        m['cores'] =  self.get_req_cores(machine)
        hosts[machine] = m
        mem = self.get_req_mem_gb()
        if mem['split_mode'] == 'node':
          m['mem'] = mem['value']
        elif mem['split_mode'] == 'task':
          m['mem'] = str(tmp.count(machine) * float(mem['value']))
    else:
      machine = {}
      machine['cores'] = self.get_req_cores()
      # TODO: Make difference between per-node and per-task!!!!!
      machine['mem'] = self.get_req_mem_gb()['value']
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

