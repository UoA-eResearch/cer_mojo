from cluster.monitoring.loadleveler.job import Job as LLJob
from cluster.util.stringutil import extract

class Job(LLJob):

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
      # TODO: Make difference between per-node and per-task!!!!!
      machine['mem'] = self.get_req_mem_gb().replace('(Per Node)','').replace('(Per Task)','')
      hosts[ah] = machine
    return hosts
