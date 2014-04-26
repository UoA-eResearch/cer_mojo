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
  command = '/home/ganglia/bin/get_summary'
  (stdout,stderr,rc) = system_call.execute('%s %s' % (config.scheduler_command_prefix, command))
  tokens = stdout.splitlines()
  sum_active = 0
  sum_idle = 0
  sum_nq = 0
  for token in tokens:
    user,active,idle,nq = token.split('|')
    sum_active += int(active)
    sum_idle += int(idle)
    sum_nq += int(nq)
    
  # read header from file
  f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
  info.write(f.read() % config.ganglia_main_page)
  f.close()

  info.write('<h2>Summary of jobs</h2>')
  info.write('<table>')
  info.write('<tr><td><b>Total number of jobs</b>:</td><td>%d</td></tr>' % (sum_active + sum_idle + sum_nq))
  info.write('<tr><td><b>Running</b>:</td><td>%d</td></tr>' % sum_active)
  info.write('<tr><td><b>Queued</b>:</td><td>%d</td></tr>' % sum_idle)
  info.write('<tr><td><b>Not Queued</b>:</td><td>%d</td></tr>' % sum_nq)
  info.write('</table>')
  info.write('''<table id="usertable" class="tablesorter">
    <thead>
      <tr>
        <th>User</th>
        <th>Running</th>
        <th>Queued</th>
        <th>Not Queued</th>
      </tr>
    </thead>
    <tbody>''')

  for token in tokens:
    user,active,idle,nq = token.split('|')
    info.write('<tr>')
    info.write('<td><a href="./showq.cgi?user=%s">%s</a></td>' % (user,user))
    info.write('<td>%s</td>' % active)
    info.write('<td>%s</td>' % idle)
    info.write('<td>%s</td>' % nq)
    info.write('</tr>')

  info.write('</tbody></table>')
except Exception:
  info.write("Error while gathering information: %s" % traceback.format_exc())
  

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

print info.getvalue()

print "</div></body></html>"
