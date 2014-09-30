#!/usr/bin/python

import os
import sys
import cgi
import cgitb
import traceback
import cStringIO
from string import whitespace
from cluster.util import system_call
from cluster import config

cgitb.enable()
form = cgi.FieldStorage()

users = {}
info = cStringIO.StringIO()

def check_user(username):
  global users
  if not username in users:
    users[username] = {}
    users[username]['running'] = 0
    users[username]['idle'] = 0

try:
  (stdout,stderr,rc) = system_call.execute('%s get_summary' % config.scheduler_command_prefix)
  tokens = stdout.splitlines()
  sum_active = 0
  sum_idle = 0
  sum_suspended = 0
  sum_other = 0
  for token in tokens:
    token = token.strip()
    if not token or token.startswith('#'):
      continue
    user,active,idle,suspended,other = token.split('|')
    sum_active += int(active)
    sum_idle += int(idle)
    sum_suspended += int(suspended)
    sum_other += int(other)
    
  info.write('<h2>Summary of jobs</h2>')
  info.write('<table>')
  info.write('<tr><td><b>Total number of jobs</b>:</td><td>%d</td></tr>' % (sum_active + sum_idle + sum_suspended + sum_other))
  info.write('<tr><td><b>Running</b>:</td><td>%d</td></tr>' % sum_active)
  info.write('<tr><td><b>Queued</b>:</td><td>%d</td></tr>' % sum_idle)
  info.write('<tr><td><b>Suspended</b>:</td><td>%d</td></tr>' % sum_suspended)
  info.write('<tr><td><b>Other</b>:</td><td>%d</td></tr>' % sum_other)
  info.write('</table>')
  info.write('''<table id="usertable" class="tablesorter">
    <thead>
      <tr>
        <th>User</th>
        <th>Running</th>
        <th>Queued</th>
        <th>Suspended</th>
        <th>Other</th>
      </tr>
    </thead>
    <tbody>''')

  for token in tokens:
    token = token.strip()
    if not token or token.startswith('#'):
      continue
    user,active,idle,suspended,other = token.split('|')
    info.write('<tr>')
    info.write('<td><a href="./showq.cgi?user=%s">%s</a></td>' % (user,user))
    info.write('<td>%s</td>' % active)
    info.write('<td>%s</td>' % idle)
    info.write('<td>%s</td>' % suspended)
    info.write('<td>%s</td>' % other)
    info.write('</tr>')

  info.write('</tbody></table>')
except Exception:
  info.write("Error while gathering information: %s" % traceback.format_exc())
  

# print response
print '''Content-Type: text/html

  <html>
    <head>
      <link rel="stylesheet" href="/jobs/style/tablesorter/theme.default.css" type="text/css" media="print, screen"/>
      <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
      <script type="text/javascript" src="/jobs/js/jquery-1.8.3.min.js"></script>
      <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
      <script type="text/javascript">
        $(document).ready(function() {
          $("#usertable").tablesorter({sortList:[[0,0]]});
        });
      </script>
    </head>
    <body>'''

print info.getvalue()
#print '<center><img src="/jobs/pics/construction.jpg"/><font color="003366"><h1>Porting to SLURM... coming soon</h1></font></center>'


print "</div></body></html>"
