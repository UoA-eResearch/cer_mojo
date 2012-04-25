import unittest
from .util import pbs_fake_job as fakejob
from .config import testdata

class JobTests(unittest.TestCase):
  
  def test_dummy(self):
    fakejob.data = testdata[0]
    job = fakejob.Job('12345')
    assert '' == job.get_status()
