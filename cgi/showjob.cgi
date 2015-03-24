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

def valid_jobid(form):
  return form.has_key('jobid') and len(form['jobid'].value) < 30

try:
  if valid_jobid(form):
    (stdout,stderr,rc) = system_call.execute('%s get_job_details %s' % (config.scheduler_command_prefix, form['jobid'].value))
    lines = stdout.splitlines()
    for line in lines:
      line = line.strip()
      if line and not line.startswith('#'):
        break
    tokens = line.split('|')

    # jobid|username|jobstatus|queue|req_num_cores|req_mem|job_directory|submit_time|start_time|req_walltime|runtime|comma-sep list of nodes [node:cpucores:mem]
    #   0      1         2       3        4          5         6            7            8          9          10               11
    if tokens and len(tokens) > 5:
      info += "<h2>Job details for job %s</h2>" % tokens[0]
      info += "<table>"
      info += "<tr><td><b>Status</b>:</td><td>%s</td></tr>" % tokens[2]
      info += "<tr><td><b>User</b>:</td><td>%s</td></tr>" % tokens[1]
      info += "<tr><td><b>Job Directory</b>:</td><td>%s</td></tr>" % tokens[6]
      info += "<tr><td><b>Queue</b>:</td><td>%s</td></tr>" % tokens[3]
      info += "<tr><td><b>Requested CPU Cores</b>:</td><td>%s</td></tr>" % tokens[4]
      info += "<tr><td><b>Requested Memory</b>:</td><td>%s</td></tr>" % tokens[5]
      info += "<tr><td><b>Requested Walltime [d-h:m:s]</b>:</td><td>%s</td></tr>" % tokens[9]
      info += "<tr><td><b>Used Walltime [d-h:m:s]</b>:</td><td>%s</td></tr>" % tokens[10]
      info += "<tr><td><b>Queued time</b>:</td><td>%s</td></tr>" % tokens[7]
      info += "<tr><td><b>Start time</b>:</td><td>%s</td></tr>" % tokens[8]
      info += "<tr><td><b>Execution nodes</b>:</td><td>"
      for resources in tokens[11].split(','):
        try:
          node,cores,mem = resources.strip().split(':')
        except:
          continue
        info += "<a href=./shownode.cgi?nodename=%s>%s</a> (CpuCores: %s, Memory: %s)<br>" % (node, node, cores, mem)
      info += "</td></tr>"
      info += "</table><br><hr><br><b>More details</b>:<br><pre>"
      (stdout,stderr,rc) = system_call.execute('%s get_scontrol_job_output %s' % (config.scheduler_command_prefix, form['jobid'].value))
      info += stdout 
      info += "</pre>"
    else:
      info += "<b>No such job</b>"
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
#print '<center><img src="/jobs/pics/construction.jpg"/><font color="003366"><h1>Porting to SLURM... coming soon</h1></font></center>'

print "</div></body></html>"
