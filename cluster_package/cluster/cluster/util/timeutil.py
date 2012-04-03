import time

def to_unix_timestamp(datetime_string, format):
  ''' Return unix timestamp for the given date time string '''
  if datetime_string is None or format is None:
    raise Exception('None parameters not accepted')
  struct_time = time.strptime(datetime_string, format)
  return int(time.mktime(struct_time))

def create_duration_string(duration_sec):
    ''' Create a string hours:minutes:seconds given a duration in seconds (int)''' 
    if duration_sec is None or duration_sec < 0:
      raise Exception('duration < 0 or None')
    tmp = duration_sec
    hours =  int(tmp/3600)
    tmp -= 3600 * hours
    minutes = int(tmp/60)
    tmp -= 60 * minutes
    seconds = tmp
    return '%02d:%02d:%02d' % (hours,minutes,seconds)
