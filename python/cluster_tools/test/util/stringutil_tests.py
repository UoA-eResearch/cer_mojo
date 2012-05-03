import unittest
from cluster.util.stringutil import extract
from cluster.util.stringutil import strip_lines
from cluster.util.stringutil import strip_multiple_ws

class StringutilTests(unittest.TestCase):
  
  # Verify normal extraction works fine
  def test_extract(self):
    expected = 'some text'
    assert expected == extract('123 some text 456', '123', '456')
  
    expected = '123 some text'
    assert expected == extract('123 some text 456', None, '456')
  
    expected = 'some text 456'
    assert expected == extract('123 some text 456', '123', None)

    expected = 'value'
    assert expected == extract('test(value) test2(value2)', 'test(', ')')

    expected = 'value'
    assert expected == extract('test:value', ':')
  
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
  def test_extract_error_01(self):
    try:
      extract('some string', None, None)
      assert False
    except:
      assert True
  
  # Verify exception is raised if string is None
  def test_extract_error_02(self):
    try:
      extract(None, 'sub1', 'sub2')
      assert False
    except:
      assert True
  
  # Verify normal strip_lines works fine
  def test_strip_lines(self):
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
  def test_strip_lines_error_01(self):
    try:
      strip_lines(None)
      assert False
    except:
      assert True 
  
  def test_strip_multiple_ws(self):
    expected = ' 1 2 3 4 '
    assert expected == strip_multiple_ws('  1   2 	3 4		')
    string = ''' 1	 2
3
4 '''
    assert expected == strip_multiple_ws(string)
  
  # Verify exception if string is None
  def test_strip_multiple_ws_error(self):
    try:
      strip_multiple_ws(None)
      assert False
    except:
      assert True
  
  
