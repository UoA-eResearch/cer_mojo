from cornice import Service
import cluster.util.factory as factory

nodes = Service(name='nodes', path='/node')
node = Service(name='node', path='/node/{id}')
jobs = Service(name='jobs', path='/job')
job = Service(name='job', path='/job/{id}')

@nodes.get()
def get_nodes(request):
  nodelist = factory.create_nodes_instance().get_node_list()
  return { 'nodes': nodelist }


@node.get()
def get_node(request):
  nodename = str(request.matchdict['id'])
  node = factory.create_node_instance(nodename).get_info()
  return { 'node': node }  

@jobs.get()
def get_jobs(request):
  uid = ''
  if 'uid' in request.params:
    uid = str(request.params['uid'])
  jobs = factory.create_queue_instance().get_jobs(uid)
  return { 'jobs': jobs }


@job.get()
def get_job(request):
  jobid = str(request.matchdict['id'])
  job = factory.create_job_instance(jobid).get_info()
  return { 'job': job }
