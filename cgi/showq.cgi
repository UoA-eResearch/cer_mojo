#!/usr/bin/python

import os
import sys
import traceback
import cgi
import cgitb
import cStringIO
from cluster.util import system_call
from cluster import config

cgitb.enable()
form = cgi.FieldStorage()

type = 'all'
user = ''
info = cStringIO.StringIO()
active_jobs = []
queued_jobs = []

try:
  if form.has_key('type'):
    type = form['type'].value
  if form.has_key('user'):
    user = form['user'].value

  # read header from file
  f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
  info.write(f.read() % config.ganglia_main_page)
  f.close()

  if user != '':
    info.write('<h2>Jobs of user %s</h2>' % user)

  if user == '':
    command = '/home/ganglia/bin/get_jobs'
    (stdout,stderr,rc) = system_call.execute('%s %s' % (config.scheduler_command_prefix, command))
    jobs = stdout.splitlines() 
  else:
    command = '/home/ganglia/bin/get_jobs %s' % user
    (stdout,stderr,rc) = system_call.execute('%s %s' % (config.scheduler_command_prefix, command))
    jobs = stdout.splitlines() 

  for job in jobs:
    status = job.split('|')[1]
    if status == 'R':
      active_jobs.append(job)
    elif status == 'I':
      queued_jobs.append(job)
    
  ### running jobs
  if type == 'all' or type == 'Running':
    info.write("<h3>Running Jobs</h3>")
    if len(active_jobs) > 0:
      info.write('''<table id="running" class="tablesorter">
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
        <tbody>''')

      for job in active_jobs:
        tokens = job.split('|')
        info.write("<tr>")
        info.write("<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (tokens[0],tokens[0]))
        info.write("<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (tokens[2],tokens[2]))
        info.write("<td>%s</td>" % tokens[3])
        info.write("<td><a href=\"./shownode.cgi?nodename=%s\">%s</a></td>" % (tokens[5],tokens[5]))
        info.write("<td>%s</td>" % tokens[4])
        info.write("<td>%s</td>" % tokens[7])
        info.write("</tr>")

      info.write("</tbody></table>")
    else:
      info.write('No active jobs.')

  ### queued jobs
  if type == 'all' or type == 'Queued':
    info.write("<h3>Queued Jobs</h3>")
    if len(queued_jobs) > 0:
      info.write('''<table id="queued" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
            <th>Group</th>
            <th>Requested Cores</th>
            <th>Queued time</th>
          </tr>
        </thead><tbody>''')

      for job in queued_jobs:
        tokens = job.split('|')
        info.write("<tr>")
        info.write("<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (tokens[0],tokens[0]))
        info.write("<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (tokens[2],tokens[2]))
        info.write("<td>%s</td>" % tokens[3])
        info.write("<td>%s</td>" % tokens[4])
        info.write("<td>%s</td>" % tokens[6])
        info.write("</tr>")

      info.write("</tbody></table>")
    else:
      info.write("No queued jobs.")

except:
  info.write("Failed to gather node information:<br><pre>%s</pre>" % traceback.format_exc())

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
          var size = Math.max($("#usertable").find("tr").size(), 
                              $("#running").find("tr").size(), 
                              $("#queued").find("tr").size()); 
          if (size < 1000) {                  
            $("#usertable").tablesorter({sortList:[[0,0]], widgets:['zebra']});
            $("#running").tablesorter({sortList:[[0,0]], widgets:['zebra']});
            $("#queued").tablesorter({sortList:[[0,0]], widgets:['zebra']});
          }
       });
    </script>
  </head>
  <body>'''

print info.getvalue()

print "</div></body></html>"
