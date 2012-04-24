import util.pbs_fake_job as fakejob
import testdata

def test_1():
  fakejob.data = testdata.testdata[0]
  job = fakejob.Job('12345')
  assert '' == job.get_status()
