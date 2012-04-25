import unittest
from .util import pbs_fake_node as fakenode
from .config import testdata

class NodeTests(unittest.TestCase):
  
  def test_dummy(self):
    fakenode.data = testdata[0]
    node = fakenode.Node('compute-59')
    assert [] == node.get_job_ids()
