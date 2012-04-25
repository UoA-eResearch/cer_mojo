import unittest
import util.pbs_fake_node as fakenode
import testdata

class NodeTests(unittest.TestCase):
  
  def test_dummy(self):
    fakenode.data = testdata.testdata[0]
    node = fakenode.Node('compute-59')
    assert [] == node.get_job_ids()
