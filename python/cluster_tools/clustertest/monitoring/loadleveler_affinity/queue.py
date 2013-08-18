import re, time
import clustertest.monitoring.loadleveler_affinity.config as config
from clustertest.monitoring.loadleveler_affinity.job import Job as Job
import clustertest.util.system_call as syscall
from clustertest.util.stringutil import strip_lines
from clustertest.util.stringutil import extract

class Queue:

  _llq_output = ''

  def __init__(self, llq_output=''):
    if llq_output == '':
      (stdout,stderr,rc) = syscall.execute('%s -l' % config.llq)
      self._llq_output = strip_lines(stdout)
    else:
      self._llq_output = strip_lines(llq_output)
      
  def get_active_jobs(self, user=''):
    ''' Get list of active jobs '''
    jobs = []
    ll_jobs = re.split('===== Job Step .* =====',self._llq_output)
    for ll_job in ll_jobs:
      if len(ll_job) > 0:
        status = extract(ll_job, 'Status:', '\n')
        if status == "Running":
          job = {}
          j = Job(extract(ll_job, 'Job Step Id:', '\n'), ll_job)
          job['id'] = j.get_id()
          job['user'] = j.get_user()
          job['group'] = j.get_queue()
          node = extract(ll_job, 'Allocated Host:', '\n')
          if node != '':
            job['node'] = node
          else: 
            # probably more than one core requested
            node = extract(ll_job, 'Allocated Hosts :', 'Master Task')
            job['node'] = extract(node, None, '::')
          job['cores'] = j.get_req_cores()
          job['start_time'] = j.get_start_time()
          if user == '' or user == job['user']:
            jobs.append(job)
    return jobs

  def get_idle_jobs(self, user=''):
    ''' Get list of idle jobs '''
    jobs = []
    ll_jobs = re.split('===== Job Step .* =====',self._llq_output)
    for ll_job in ll_jobs:
      if len(ll_job) > 0:
        status = extract(ll_job, 'Status:', '\n')
        if status == "Idle":
          job = {}
          job['id'] = extract(ll_job, 'Job Step Id:', '\n')
          job['user'] = extract(ll_job, 'Owner:', '\n')
          job['group'] = extract(ll_job, 'Class:', '\n')
          tmp = extract(ll_job, 'Node\n----\n')
          if '' == tmp:
            job['cores'] = 1
          else:
            cores = extract(tmp, 'Total Tasks     :', '\n')
            if cores != '':
              job['cores'] = int(cores)
            else:
              job['cores'] = -1
          # format: Tue 20 Mar 2012 02:49:00 PM NZDT
          # new format: Mon Mar 12 18:52:43 2012
          queue_time = extract(ll_job, 'Queue Date:', '\n')
          try:
            t = time.strptime(queue_time, '%a %d %b %Y %I:%M:%S %p %Z')
          except:
            t = time.strptime(queue_time, '%a %b %d %H:%M:%S %Y')
          job['queued_time'] = time.strftime('%m/%d %H:%M:%S',t)
          if user == '' or user == job['user']:
            jobs.append(job)
    return jobs

  def get_blocked_jobs(self, user=''):
    ''' Get list of blocked jobs '''
    return []

  def get_jobs(self, user=''):
    ''' Get lists of active, idle and blocked jobs '''
    jobs = {}
    jobs['active_jobs'] = self.get_active_jobs(user)
    jobs['idle_jobs'] = self.get_idle_jobs(user)
    jobs['blocked_jobs'] = self.get_blocked_jobs(user)
    return jobs
