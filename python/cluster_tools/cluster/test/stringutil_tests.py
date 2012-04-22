from cluster.util.stringutil import extract
from cluster.util.stringutil import strip_lines
from cluster.util.stringutil import strip_multiple_ws

# Verify normal extraction works fine
def test_extract():
  expected = 'some text'
  assert expected == extract('123 some text 456', '123', '456')

  expected = '123 some text'
  assert expected == extract('123 some text 456', None, '456')

  expected = 'some text 456'
  assert expected == extract('123 some text 456', '123', None)

  expected = '''Task
----'''

  string = '''
some text

Task
----

some more text'''
  result = extract(string, 'some text', 'some more text')
  assert result == expected

# Verify exception is raised if both sub1 and sub2 are None
def test_extract_error_01():
  try:
    extract('some string', None, None)
    assert False
  except:
    assert True

# Verify exception is raised if string is None
def test_extract_error_02():
  try:
    extract(None, 'sub1', 'sub2')
    assert False
  except:
    assert True

# Verify normal strip_lines works fine
def test_strip_lines():
  string = '''
    some text  

 Task		 
----

     some more text''' 

  expected = '''some text

Task
----

some more text''' 
  assert expected == strip_lines(string)

# Verify exception if string is None
def test_strip_lines_error_01():
  try:
    strip_lines(None)
    assert False
  except:
    assert True 

def test_strip_multiple_ws():
  expected = ' 1 2 3 4 '
  assert expected == strip_multiple_ws('  1   2 	3 4		')
  input = ''' 1	 2
3
4 '''
  assert expected == strip_multiple_ws(input)

# Verify exception if string is None
def test_strip_multiple_ws_error():
  try:
    strip_multiple_ws(None)
    assert False
  except:
    assert True


