import util.pbs_fake_node as fakenode
import testdata

def test_1():
  fakenode.data = testdata.testdata[0]
  node = fakenode.Node('compute-59')
  assert [] == node.get_job_ids()
