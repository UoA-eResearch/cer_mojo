import re
from cluster.util.stringutil import extract
from cluster.util.timeutil import time
from cluster.monitoring.loadleveler.queue import Queue as LLQueue

class Queue(LLQueue):
  
  def get_active_jobs(self, user=''):
    ''' Get list of active jobs '''
    jobs = []
    ll_jobs = re.split('===== Job Step .* =====',self._llq_output)
    for ll_job in ll_jobs:
      if len(ll_job) > 0:
        status = extract(ll_job, 'Status:', '\n')
        if status == "Running":
          job = {}
          job['id'] = extract(ll_job, 'Job Step Id:', '\n')
          job['user'] = extract(ll_job, 'Owner:', '\n')
          job['group'] = extract(ll_job, 'Class:', '\n')
          node = extract(ll_job, 'Allocated Host:', '\n')
          if node != '':
            job['node'] = node
            job['cores'] = 1
          else: 
            # probably more than one core requested
            node = extract(ll_job, 'Allocated Hosts :', 'Master Task')
            job['node'] = extract(node, None, '::')
            tmp = extract(ll_job, 'Task\n----\n')
            job['cores'] = extract(tmp, 'Num Task Inst:', '\n')
          # format: Tue 20 Mar 2012 02:49:00 PM NZDT
          # new format: Mon Mar 12 18:52:43 2012
          start_time = extract(ll_job, 'Dispatch Time:', '\n')
          try:
            t = time.strptime(start_time, '%a %d %b %Y %I:%M:%S %p %Z')
          except:
            t = time.strptime(start_time, '%a %b %d %H:%M:%S %Y')
          job['start_time'] = time.strftime('%m/%d %H:%M:%S',t)
          if user == '' or user == job['user']:
            jobs.append(job)
    return jobs

