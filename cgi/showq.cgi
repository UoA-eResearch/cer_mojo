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
suspended_jobs = []
queued_jobs = []

try:
  if form.has_key('type'):
    type = form['type'].value
  if form.has_key('user'):
    user = form['user'].value

  if not user:
    (stdout,stderr,rc) = system_call.execute('%s get_jobs' % config.scheduler_command_prefix)
    jobs = stdout.splitlines() 
  else:
    info.write('<h2>Jobs of user %s</h2>' % user)
    (stdout,stderr,rc) = system_call.execute('%s get_jobs %s' % (config.scheduler_command_prefix, user))
    jobs = stdout.splitlines() 

  for job in jobs:
    if job:
      status = job.split('|')[1]
      if status == 'R':
        active_jobs.append(job)
      elif status == 'PD':
        queued_jobs.append(job)
      elif status == 'S':
        suspended_jobs.append(job)
    
  ### running jobs
  if type == 'all' or type == 'Running':
    info.write("<h3>Running Jobs</h3>")
    if len(active_jobs) > 0:
      info.write('''<table id="running" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
            <th>Working Directory</th>
            <th>Requested Cores</th>
            <th>Start time</th>
            <th>Nodes</th>
            <th>Queue</th>
          </tr>
        </thead>
        <tbody>''')

      for job in active_jobs:
        # jobid|jobstatus|userid|queue|numcores|nodes|starttime|jobdir
        tok = job.split('|')
        info.write("<tr>")
        info.write("<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (tok[0],tok[0]))
        info.write("<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (tok[2],tok[2]))
        info.write("<td>%s</td>" % tok[7])
        info.write("<td>%s</td>" % tok[4])
        info.write("<td>%s</td>" % tok[6])
        info.write("<td>%s</td>" % tok[5])
        info.write("<td>%s</td>" % tok[3])
        info.write("</tr>")

      info.write("</tbody></table>")
    else:
      info.write('No active jobs.')

  ### suspended jobs
  if type == 'all' or type == 'Suspended':
    info.write("<h3>Suspended Jobs</h3>")
    if len(suspended_jobs) > 0:
      info.write('''<table id="suspended" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
            <th>Working Directory</th>
            <th>Requested Cores</th>
            <th>Start time</th>
            <th>Nodes</th>
            <th>Queue</th>
          </tr>
        </thead>
        <tbody>''')

      for job in suspended_jobs:
        # jobid|jobstatus|userid|queue|numcores|nodes|starttime|jobdir
        tok = job.split('|')
        info.write("<tr>")
        info.write("<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (tok[0],tok[0]))
        info.write("<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (tok[2],tok[2]))
        info.write("<td>%s</td>" % tok[7])
        info.write("<td>%s</td>" % tok[4])
        info.write("<td>%s</td>" % tok[6])
        info.write("<td>%s</td>" % tok[5])
        info.write("<td>%s</td>" % tok[3])
        info.write("</tr>")

      info.write("</tbody></table>")
    else:
      info.write('No suspended jobs.')

  ### queued jobs
  if type == 'all' or type == 'Queued':
    info.write("<h3>Queued Jobs</h3>")
    if len(queued_jobs) > 0:
      info.write('''<table id="queued" class="tablesorter">
        <thead>
          <tr>
            <th>Job ID</th>
            <th>User</th>
            <th>Working Directory</th>
            <th>Requested Cores</th>
            <th>Queue</th>
          </tr>
        </thead><tbody>''')

      for job in queued_jobs:
        # jobid|jobstatus|userid|queue|numcores|nodes|starttime|jobdir
        tok = job.split('|')
        info.write("<tr>")
        info.write("<td><a href=\"./showjob.cgi?jobid=%s\">%s</a></td>" % (tok[0],tok[0]))
        info.write("<td><a href=\"./showq.cgi?user=%s\">%s</a></td>" % (tok[2],tok[2]))
        info.write("<td>%s</td>" % tok[7])
        info.write("<td>%s</td>" % tok[4])
        info.write("<td>%s</td>" % tok[3])
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
    <link rel="stylesheet" href="/jobs/style/tablesorter/theme.default.css" type="text/css" media="print, screen"/>
    <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
    <script type="text/javascript" src="/jobs/js/jquery-1.8.3.min.js"></script>
    <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
    <script type="text/javascript">
       $(document).ready(function() {
          var size = Math.max($("#usertable").find("tr").size(), 
                              $("#running").find("tr").size(), 
                              $("#queued").find("tr").size()); 
          if (size < 3000) {                  
            $("#usertable").tablesorter({sortList:[[0,0]]});
            $("#running").tablesorter({sortList:[[0,0]]});
            $("#suspended").tablesorter({sortList:[[0,0]]});
            $("#queued").tablesorter({sortList:[[0,0]]});
          }
       });
    </script>
  </head>
  <body>'''

print info.getvalue()
#print '<center><img src="/jobs/pics/construction.jpg"/><font color="003366"><h1>Porting to SLURM... coming soon</h1></font></center>'

print "</div></body></html>"
