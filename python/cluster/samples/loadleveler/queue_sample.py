from cluster.monitoring.loadleveler.queue import Queue as Queue

queue = Queue()
jobs = queue.get_jobs()
print jobs
