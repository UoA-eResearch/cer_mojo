#!/usr/bin/python

import re
import os
import traceback
import datetime
import cgi
import cgitb
import cluster.util.factory as factory
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
    jobid = form['jobid'].value
    job = factory.create_job_instance(jobid).get_info()
    info += "<h2>Job details for job %s</h2>" % job['id']
    info += "<table>"
    info += "<tr><td><b>Status</b>:</td><td>%s</td></tr>" % job['status']
    info += "<tr><td><b>User</b>:</td><td>%s</td></tr>" % job['user']
    info += "<tr><td><b>Job Directory</b>:</td><td>%s</td></tr>" % job['job_directory']
    info += "<tr><td><b>Queue</b>:</td><td>%s</td></tr>" % job['queue']
    info += "<tr><td><b>Requested CPU Cores</b>:</td><td>%s</td></tr>" % job['req_cores']
    info += "<tr><td><b>Requested Memory [GB]</b>:</td><td>%s (per %s)</td></tr>" % (job['req_mem_gb']['value'], job['req_mem_gb']['split_mode'])
    info += "<tr><td><b>Used Memory [GB]</b>:</td><td>%s</td></tr>" % job['used_mem_gb']
    info += "<tr><td><b>Requested Walltime [h:m:s]</b>:</td><td>%s</td></tr>" % job['req_walltime']
    info += "<tr><td><b>Used Walltime [h:m:s]</b>:</td><td>%s</td></tr>" % job['used_walltime']
    info += "<tr><td><b>Queued time</b>:</td><td>%s</td></tr>" % job['queued_time']
    info += "<tr><td><b>Start time</b>:</td><td>%s</td></tr>" % job['start_time']
    info += "<tr><td><b>Execution nodes</b>:</td><td>"
    for name in job['execution_nodes'].keys():
      info += "<a href=./shownode.cgi?nodename=%s>%s</a> (%s cores), " % (name, name, job['execution_nodes'][name]['cores'])
    info = info[:-2]
    info += "</td></tr>"
    info += "</table><br><hr>"

    if print_specifics:
      info += "<a href=./showjob.cgi?jobid=%s>Hide scheduler command details</a>" % jobid
      info += "<h3>Scheduler command details</h3>"
      for (key,value) in job['scheduler_command_details'].items():
        info += "<b>%s</b>" % key
        info += "<pre>%s</pre>" % value
    else:
      info += "<a href=./showjob.cgi?jobid=%s&specifics=true>Print scheduler command details</a>" % jobid
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
