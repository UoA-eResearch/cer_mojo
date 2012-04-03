import sys
from cluster.monitoring.loadleveler.node import Node as Node

nodename = sys.argv[1]
nodeinfo = Node(nodename).get_info()
print nodeinfo
