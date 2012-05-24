#!/usr/bin/python

import os
import sys
import cgi
import cgitb
import cluster.util.factory as factory
from cluster import config

cgitb.enable()
form = cgi.FieldStorage()

users = {}
info = ''

def check_user(username):
  global users
  if not username in users:
    users[username] = {}
    users[username]['running'] = 0
    users[username]['idle'] = 0
    users[username]['blocked'] = 0

try:
  queue = factory.create_queue_instance()
  active_jobs = queue.get_active_jobs()
  idle_jobs = queue.get_idle_jobs()
  blocked_jobs = queue.get_blocked_jobs()

  # Create per user overview
  for job in active_jobs:
    check_user(job['user'])
    users[job['user']]['running'] += 1
      
  for job in idle_jobs:
    check_user(job['user'])
    users[job['user']]['idle'] += 1

  for job in blocked_jobs:
    check_user(job['user'])
    users[job['user']]['blocked'] += 1

  # read header from file
  f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
  info += f.read() % config.main_ganglia_page
  f.close()

  info += '<h2>Summary of jobs</h2>'
  info += '<table>'
  info += '<tr><td><b>Total number of jobs</b>:</td><td>%d</td></tr>' % (len(active_jobs) + len(idle_jobs) + len(blocked_jobs))
  info += '<tr><td><b>Running jobs</b>:</td><td>%d</td></tr>' % len(active_jobs)
  info += '<tr><td><b>Queued jobs</b>:</td><td>%d</td></tr>' % len(idle_jobs)
  info += '<tr><td><b>Blocked jobs</b>:</td><td>%d</td></tr>' % len(blocked_jobs)
  info += '</table>'
  info += '''<table id="usertable" class="tablesorter">
    <thead>
      <tr>
        <th>User</th>
        <th>Running Jobs</th>
        <th>Queued Jobs</th>
        <th>Blocked Jobs</th>
      </tr>
    </thead>
    <tbody>'''

  for user,map in users.items():
    info += '<tr>'
    info += '<td><a href="./showq.cgi?user=%s">%s</a></td>' % (user,user)
    info += '<td>%s</td>' % map['running']
    info += '<td>%s</td>' % map['idle']
    info += '<td>%s</td>' % map['blocked']
    info += '</tr>'

  info += '</tbody></table>'
except Exception:
  info = "Error while gathering information: %s" % sys.exc_info()[1]


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
        });
      </script>
    </head>
    <body>'''

print info

print "</div></body></html>"
