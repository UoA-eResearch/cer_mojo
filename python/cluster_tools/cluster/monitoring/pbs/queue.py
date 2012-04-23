import re, os, time
import cluster.monitoring.pbs.config as config
import cluster.util.system_call as syscall

class Queue:

  def get_active_jobs(self, user=''):
    ''' Get list of active jobs '''
    (stdout,stderr,rc) = syscall.execute('%s -r' % config.showq)
    tmp = re.sub(' +',' ',stdout)
    lines = tmp.splitlines()[2:-2]
    jobs = []
    for line in lines:
      # JobName S Par Effic XFactor Q User Group MHost Procs Remaining StartTime
      line = line.strip()
      fields = line.split()
      job = {}
      job['id'] = fields[0].replace('+','')
      job['user'] = fields[6]
      job['group'] = fields[7]
      job['node'] = fields[8]
      job['cores'] = fields[9]
      t = '%s %s %s, %s' % (fields[11], fields[12], fields[13], fields[14])
      # format: Wed Mar 7, 15:29:07
      date_time = time.strptime(t, '%a %b %d, %H:%M:%S')
      job['start_time'] = time.strftime('%m/%d %H:%M:%S',date_time)
      if user == '' or user == job['user']:
        jobs.append(job)
    return jobs 

  def get_idle_jobs(self, user=''):
    ''' Get list of idle jobs '''
    (stdout,stderr,rc) = syscall.execute('%s -i' % config.showq)
    tmp = re.sub(' +',' ',stdout)
    lines = tmp.splitlines()[2:-2]
    jobs = []
    for line in lines:
      # JobName Priority XFactor Q User Group Procs WCLimit Class SystemQueueTime
      line = line.strip()
      fields = line.split()
      job = {}
      job['id'] = re.sub('\*', '', fields[0])
      job['user'] = fields[4]
      job['group'] = fields[5]
      job['cores'] = fields[6]
      job['queued_time'] = '%s %s %s, %s' % (fields[9], fields[10], fields[11], fields[12])
      if user == '' or user == job['user']:
        jobs.append(job)
    return jobs

  def get_blocked_jobs(self, user=''):
    ''' Get list of blocked jobs '''
    (stdout,stderr,rc) = syscall.execute('%s -b' % config.showq)
    tmp = re.sub(' +',' ',stdout)
    lines = tmp.splitlines()[2:]
    jobs = []
    for line in lines:
      # JobName User Reason
      line = line.strip()
      fields = line.split()
      job = {}
      job['id'] = fields[0]
      job['user'] = fields[1]
      if user == '' or user == job['user']:
        jobs.append(job)
    return jobs

  def get_jobs(self, user=''):
    ''' Get lists of active, idle and blocked jobs '''
    jobs = {}
    jobs['active_jobs'] = self.get_active_jobs(user)
    jobs['idle_jobs'] = self.get_idle_jobs(user)
    jobs['blocked_jobs'] = self.get_blocked_jobs(user)
    return jobs
