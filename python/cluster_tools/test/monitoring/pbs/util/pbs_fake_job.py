import cluster.monitoring.pbs.job

#  Data to be used by the job
data = {}

# Fake a PBS job. Information about the job is not fetched from local
# resource manager commands, but read from the configuration data
class Job(cluster.monitoring.pbs.job.Job):

  def __init__(self, jobid):
    global data
    self._jobid = jobid
    self._qstat_output = data['job'][jobid]['qstat_output']
    self._checkjob_output = data['job'][jobid]['checkjob_output']
