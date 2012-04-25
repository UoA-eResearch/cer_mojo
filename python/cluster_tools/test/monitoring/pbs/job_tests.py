import unittest
import util.pbs_fake_job as fakejob
import testdata

class JobTests(unittest.TestCase):
  
  def test_dummy(self):
    fakejob.data = testdata.testdata[0]
    job = fakejob.Job('12345')
    assert '' == job.get_status()
