#!/usr/bin/python

import re
import os
import traceback
import datetime
import cgi
import cgitb
from time import strftime,localtime
from cluster.util import system_call
from cluster import config

cgitb.enable()
form = cgi.FieldStorage()
info = ''
print_specifics = False

def valid_jobid(form):
  return form.has_key('jobid') and len(form['jobid'].value) < 30

try:
  if form.has_key('specifics') and form['specifics'].value.lower() == 'true':
    print_specifics = True

  # read header from file
  f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
  info += f.read() % config.ganglia_main_page
  f.close()

  if valid_jobid(form):
    command = '/home/ganglia/bin/get_job_details %s' % form['jobid'].value
    (stdout,stderr,rc) = system_call.execute('%s %s' % (config.scheduler_command_prefix, command))
    tokens = stdout.split('|')

    info += "<h2>Job details for job %s</h2>" % tokens[0]
    info += "<table>"
    info += "<tr><td><b>Status</b>:</td><td>%s</td></tr>" % tokens[2]
    info += "<tr><td><b>User</b>:</td><td>%s</td></tr>" % tokens[1]
    info += "<tr><td><b>Job Directory</b>:</td><td>%s</td></tr>" % tokens[8]
    info += "<tr><td><b>Queue</b>:</td><td>%s</td></tr>" % tokens[3]
    info += "<tr><td><b>Requested CPU Cores</b>:</td><td>%s</td></tr>" % tokens[4]
    info += "<tr><td><b>Requested Memory [GB]</b>:</td><td>%s (per task)</td></tr>" % round(float(tokens[5])/1024,2)
    info += "<tr><td><b>Requested Virtual Memory [GB]</b>:</td><td>%s (per Task)</td></tr>" % round(float(tokens[6])/1024,2)
    info += "<tr><td><b>Requested Walltime [d+h:m:s]</b>:</td><td>%s</td></tr>" % tokens[11]
    info += "<tr><td><b>Used Walltime [d+h:m:s]</b>:</td><td>%s</td></tr>" % tokens[12]
    info += "<tr><td><b>Queued time</b>:</td><td>%s</td></tr>" % strftime('%Y/%m/%d %H:%M:%S', localtime(int(tokens[9])))
    info += "<tr><td><b>Start time</b>:</td><td>%s</td></tr>" % strftime('%Y/%m/%d %H:%M:%S', localtime(int(tokens[10])))
    info += "<tr><td><b>Execution nodes</b>:</td><td>"
    for resources in tokens[13].split(','):
      try:
        node,cores,mem,vmem = resources.strip().split(':')
      except:
        continue
      info += "<a href=./shownode.cgi?nodename=%s>%s</a> (CpuCores: %s, Memory[GB]: %s, VirtualMemory[GB]: %s)<br>" % (node, node, cores, round(float(mem)/1024,2),round(float(vmem)/1024,2))
    info += "</td></tr>"
    info += "</table><br><hr>"

    if print_specifics:
      command = '/usr/bin/llq -l %s' % tokens[0]
      (stdout,stderr,rc) = system_call.execute('%s %s' % (config.scheduler_command_prefix, command))

      info += "<a href=./showjob.cgi?jobid=%s>Hide scheduler command details</a>" % tokens[0]
      info += "<h3>Scheduler command details</h3>"
      info += "<b>%s</b>" % command 
      info += "<pre>%s</pre>" % stdout 
    else:
      info += "<a href=./showjob.cgi?jobid=%s&specifics=true>Print scheduler command details</a>" % tokens[0]
  else:
    raise Exception('Invalid job id')
except:
  info += "Failed to gather job information:<br><pre>%s</pre>" % traceback.format_exc()

# print response
print '''Content-Type: text/html

  <html>
  <head>
    <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
  </head>
  <body>'''

print info

print "</div></body></html>"
