from cluster.monitoring.pbs.queue import Queue as Queue

queue = Queue()
active_jobs = queue.get_active_jobs()
idle_jobs = queue.get_idle_jobs()
blocked_jobs = queue.get_blocked_jobs()

print active_jobs
print idle_jobs
print blocked_jobs
