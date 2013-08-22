import sys
from cluster.monitoring.loadleveler_affinity.job import Job as Job

node = ''

jobid = sys.argv[1]
if len(sys.argv) > 2:
  node = sys.argv[2]

#jobdata = open(jobid, 'r').read()
job = Job(jobid=jobid)
print "requested #cores: %s" % job.get_req_cores(node=node)
print "requested memory[gb]: %s" % job.get_req_mem_gb()
print "execution nodes:\n"
print job.get_execution_nodes()
