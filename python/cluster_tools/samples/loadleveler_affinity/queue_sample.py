from cluster.monitoring.loadleveler_affinity.queue import Queue as Queue

queue = Queue()
jobs = queue.get_jobs()
print jobs
