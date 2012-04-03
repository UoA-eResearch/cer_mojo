import re

def extract(string, sub1=None, sub2=None):
  ''' Extract and return the string between sub1 and sub2 from string
      If sub1 is None, everything from the start to sub2 is returned
      If sub2 is None, everything from sub1 to the end is returned
      If either sub1 or sub2 cannot be found, an empty string is returned
      The returned value is stripped
  '''
  retval = ''
  if string is None:
    raise Exception('Cannot extract text from None')
  if sub1 is None:
    if sub2 is not None:
      tmp = string.split(sub2)[0]
      if tmp != string:
        retval = tmp
  else:
    tmp1 = string.split(sub1)[-1]
    if tmp1 != string:
      if sub2 is None:
        retval = tmp1
      else:
        tmp2 = tmp1.split(sub2)[0].strip()
        if tmp1 != tmp2:
          retval = tmp2
  return retval.strip()

def strip_multiple_ws(string):
  ''' Return a copy of string where multiple occurences of whitespaces is replaced with a single blank '''
  if string is None:
    raise Exception('Cannot process None')
  return re.sub('\s+' , ' ', string)

def strip_lines(string):
  ''' Return a copy of string with each line being stripped '''
  if string is None:
    raise Exception('Cannot strip lines from None')
  tmp = ''
  lines = string.split('\n')
  for line in lines:
    line = line.strip()
    tmp += '%s\n' % line
  return tmp.strip()

