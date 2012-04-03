import sys
from cluster.monitoring.pbs.node import Node as Node

nodename = sys.argv[1]
nodeinfo = Node(nodename).get_info()
print nodeinfo
