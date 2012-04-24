import cluster.monitoring.pbs.node

# Configuration data for the node
data = {}

# Fake a PBS node. Information about the node is not fetched from local
# resource manager commands, but read from the configuration data
class Node(cluster.monitoring.pbs.node.Node):

  def __init__(self, nodename):
    global data
    self._nodename = nodename
    self._node_listing = data['node'][nodename]['qmgr_output']
