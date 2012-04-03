from cluster.util.timeutil import to_unix_timestamp
from cluster.util.timeutil import create_duration_string

# Verify normal conversion works fine
def test_to_unix_timestamp():
  assert 0 == to_unix_timestamp("1970-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
  assert 1284101485 == to_unix_timestamp("2010-09-10 18:51:25","%Y-%m-%d %H:%M:%S")

# Verify exception if datetime_string or format are None
def test_to_unix_timestamp_error():
  try:
    to_unix_timestamp(None, "%Y-%m-%d %H:%M:%S") 
    assert False 
  except:
    assert True

  try:
    to_unix_timestamp("1970-01-01 12:00:00", None)
    assert False 
  except:
    assert True

# Verify creation of duration string works fine
def test_create_duration_string():
  assert "00:00:00" == create_duration_string(0)
  assert "00:00:05" == create_duration_string(5)
  assert "00:01:00" == create_duration_string(60)
  assert "00:01:29" == create_duration_string(89)
  assert "01:00:00" == create_duration_string(3600)
  assert "01:00:05" == create_duration_string(3605)
  assert "120:00:05" == create_duration_string(432005)

# Verify exception if duration_sec is < 0 or None
def test_create_duration_string_error():
  try:
    create_duration_string(None)
    assert False
  except:
    assert True 

  try:
    create_duration_string(-1)
    assert False
  except:
    assert True 

