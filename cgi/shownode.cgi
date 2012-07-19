#!/usr/bin/python

import os
import traceback 
import string
import datetime
import cgi
import cgitb
import cluster.util.factory as factory
from cluster import config

cgitb.enable()
form = cgi.FieldStorage()
info = ''
failure = False

# make sure we have a nodename here
def valid_nodename(form):
    trtable = string.maketrans(string.lowercase, string.lowercase)
    return form.has_key('nodename') and len(form['nodename'].value) < 50 

# read header from file
f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
info += f.read() % config.ganglia_main_page
f.close()

if valid_nodename(form):
  nodename = form['nodename'].value
  mpi_job_present = False
  try:
    nodeinfo = factory.create_node_instance(nodename).get_info()
    now = datetime.datetime.now()
    info += "<h2>Node overview for node %s</h2>" % nodeinfo['name']
    info += "<table border=0>"
    info += "<tr><td><b>Physical Memory</b>:</td><td>%s GB</td></tr>" % '%s' % nodeinfo['phys_mem_gb']
    info += "<tr><td><b>Available Memory</b>:</td><td>%s GB</td></tr>" % '%s' % nodeinfo['avail_mem_gb']
    info += "<tr><td><b>CPU Cores</b>:</td><td>%s</td></tr>" % nodeinfo['cores']
    info += "<tr><td><b>Available CPU Cores</b>:</td><td>%s</td></tr>" % nodeinfo['avail_cores']
    info += "</table><br>"

    if len(nodeinfo['job_ids']) > 0:
      info += "<b>Running Jobs and their allocated resources</b>:<br>"
      info += '''<table id="jobs" class="tablesorter">
        <thead><tr>
          <th>Job ID</th>
          <th>User</th>
          <th>Requested CPU Cores</th>
          <th>Requested Memory [GB]</th>
          <th>Used Walltime [h:m:s]</th>
          <th>Requested Walltime [h:m:s]</th>
          <th>Queue</th>
        </tr></thead><tbody>'''
      for jobid in nodeinfo['job_ids']:
        job = factory.create_job_instance(jobid).get_info()
        info += '<tr>'
        info += '<td><a href=./showjob.cgi?jobid=%s>%s</a>' % (job['id'],job['id'])
        if len(job['execution_nodes']) > 1:
          mpi_job_present = True
          info += ' (*)'
        info += '</td>'
        info += '<td><a href="./showq.cgi?user=%s">%s</a></td>' % (job['user'],job['user'])
        info += '<td>%s</td>' % job['execution_nodes'][nodename]['cores']
        info += '<td>%s</td>' % job['execution_nodes'][nodename]['mem']
        info += '<td>%s</td>' % job['used_walltime']
        info += '<td>%s</td>' % job['req_walltime']
        info += '<td>%s</td>' % job['queue']
        info += '</tr>'
      info += '</tbody></table>'

    if mpi_job_present:
      info += "(*) This job runs on multiple nodes. The displayed memory related and CPU core related parameters of this job apply to this node only. "
      info += "Click on the jobid for full information about the job.<br>"
    info += "<br><hr><br>"

    info += "<b>Explanation:</b><br>"
    info += "<table border=0>"
    info += "<tr><td><i>Physical Memory</i>:</td><td>Total amount of physical memory available on the node</td></tr>"
    info += "<tr><td><i>Available Memory</i>:</td><td>Amount of available memory that has not been requested by other jobs</td></tr>"
    info += "<tr><td><i>CPU Cores</i>:</td><td>Total number of CPU cores</td></tr>"
    info += "<tr><td><i>Available CPU Cores</i>:</td><td>Number of CPU cores that have not been requested by other jobs</td></tr>"
    info += "<tr><td><i>Job IDs</i>:</td><td>IDs of jobs running on the node</td></tr>"
    info += "</table><br>"
    info += "<b>Note: This information is a snaphshot taken at "
    info += now.strftime("%Y-%m-%d %H:%M") 
    info += " and is subject to change as jobs finish or new jobs are started on this node</b>"
  except:
    info = "Failed to gather node information:<br><pre>%s</pre>" % traceback.format_exc()
    failure = True
else:
  failure = True

# print response
print '''Content-Type: text/html

<html>
  <head>
    <link rel="stylesheet" href="/jobs/style/tablesorter/blue/style.css" type="text/css" media="print, screen"/>
    <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
    <script type="text/javascript" src="/jobs/js/jquery-1.7.min.js"></script>
    <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
    <script type="text/javascript" src="/jobs/js/jquery.blockUI.2.39.js"></script>
    <script type="text/javascript">
      $(document).ready(function() {
'''

if not failure: 
  print "$(\"#jobs\").tablesorter({sortList:[[3,1]], widgets:['zebra']});"
else:
  # get cluster node list and display as modal
  node_list = factory.create_nodes_instance().get_node_list()
  string = '<b>Pick a node</b><hr><table width="100%"><tr><td valign="top">'
  maxrows = 15
  colcount = 0
  for node in node_list:
    if colcount % maxrows == 0 and colcount != 0:
      string += '</td><td valign="top">'
    colcount += 1
    string += '<a href="./shownode.cgi?nodename=%s">%s</a><br>' % (node,node)
  string += '</td></tr></table>'
  print "var str = '%s';" % string
  print "$.blockUI({ message: str, css: { height: '80%', width: '80%', top: '10%', left: '10%'} });"  

print '''
      });
    </script>
</head>
<body>
'''

print info

print "</div></body></html>"
