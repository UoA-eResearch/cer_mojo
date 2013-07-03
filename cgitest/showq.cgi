#!/usr/bin/python

import os
import sys
import traceback
import itertools as it
import cgi
import cgitb
import clustertest.util.factory as factory
from clustertest import config

cgitb.enable()
form = cgi.FieldStorage()

type = 'all'
user = ''
info = ''
active_jobs = []
idle_jobs = []
blocked_jobs = []

try:
  queue = factory.create_queue_instance()

  if form.has_key('type'):
    type = form['type'].value
  if form.has_key('user'):
    user = form['user'].value

  # read header from file
  f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
  info += f.read() % config.ganglia_main_page
  f.close()

  if user != '':
    info += '<h2>Jobs of user %s</h2>' % user

  ### running jobs
  if type == 'all' or type == 'Running':
    if user == '':
      active_jobs = queue.get_active_jobs()
    else:
      active_jobs = queue.get_active_jobs(user)
    info += "<h3>Running Jobs</h3>"
    if len(active_jobs) > 0:
      info += '''<table id="running" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
            <th>Queue</th>
            <th>Node</th>
            <th>Requested Cores</th>
            <th>Start time</th>
          </tr>
        </thead>
        <tbody>'''

      for job in active_jobs:
        info += "<tr>"
        info += "<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (job['id'],job['id'])
        info += "<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (job['user'],job['user'])
        info += "<td>%s</td>" % job['group']
        info += "<td><a href=\"./shownode.cgi?nodename=%s\">%s</a></td>" % (job['node'],job['node'])
        info += "<td>%s</td>" % job['cores']
        info += "<td>%s</td>" % job['start_time']
        info += "</tr>"

      info += "</tbody></table>"
    else:
      info += 'No active jobs.'

  ### idle jobs
  if type == 'all' or type == 'Queued':
    if user == '':
      idle_jobs = queue.get_idle_jobs()
    else:
      idle_jobs = queue.get_idle_jobs(user)
    info += "<h3>Queued Jobs</h3>"
    if len(idle_jobs) > 0:
      info += '''<table id="idle" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
            <th>Group</th>
            <th>Requested Cores</th>
            <th>Queued time</th>
          </tr>
        </thead><tbody>'''

      for job in idle_jobs:
        info += "<tr>"
        info += "<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (job['id'],job['id'])
        info += "<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (job['user'],job['user'])
        info += "<td>%s</td>" % job['group']
        info += "<td>%s</td>" % job['cores']
        info += "<td>%s</td>" % job['queued_time']
        info += "</tr>"

      info += "</tbody></table>"
    else:
      info += "No queued jobs."

  ### blocked jobs
  if type == 'all' or type == 'Blocked':
    if user == '':
      blocked_jobs = queue.get_blocked_jobs()
    else:
      blocked_jobs = queue.get_blocked_jobs(user)
    info += "<h3>Blocked Jobs</h3>"
    if len(blocked_jobs) > 0:
      info += '''<table id="blocked" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
          </tr>
        </thead>
        <tbody>'''

      for job in blocked_jobs:
        info += "<tr>"
        info += "<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (job['id'],job['id'])
        info += "<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (job['user'],job['user'])
        info += "</tr>"

      info += "</tbody></table>"
    else:
      info += 'No blocked jobs.'
except:
  #info = "Failed to gather information: %s" % sys.exc_info()[1]
  info = "Failed to gather node information:<br><pre>%s</pre>" % traceback.format_exc()

# print response
print '''Content-Type: text/html

  <html>
  <head>
    <link rel="stylesheet" href="/jobs/style/tablesorter/blue/style.css" type="text/css" media="print, screen"/>
    <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
    <script type="text/javascript" src="/jobs/js/jquery-1.7.min.js"></script>
    <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
    <script type="text/javascript">
       $(document).ready(function() {
          $("#usertable").tablesorter({sortList:[[0,0]], widgets:['zebra']});
          $("#running").tablesorter({sortList:[[0,0]], widgets:['zebra']});
          $("#idle").tablesorter({sortList:[[0,0]], widgets:['zebra']});
          $("#blocked").tablesorter({sortList:[[0,0]], widgets:['zebra']});
       });
    </script>
  </head>
  <body>'''

print info

print "</div></body></html>"
