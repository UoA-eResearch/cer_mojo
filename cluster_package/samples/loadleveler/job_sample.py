import sys
from cluster.monitoring.loadleveler.job import Job as Job

jobid = sys.argv[1]
jobinfo = Job(jobid).get_info()
print jobinfo


