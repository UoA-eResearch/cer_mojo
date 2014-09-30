#!/usr/bin/python

import os
import re
import traceback 
import string
import datetime
import cgi
import cgitb
import xml.sax
from cluster import config
from cluster.util import system_call

cgitb.enable()
form = cgi.FieldStorage()
info = ''
failure = False

# tooltips
tt = {}
tt['userId'] = "User ID"
tt['physMem'] = "Total amount of physical memory available on the node"
tt['virtMem'] = "Total amount of virtual memory available on the node"
tt['availMem'] = "Amount of available memory that has not been requested by other jobs"
tt['availVirtMem'] = "Amount of available virtual memory that has not been requested by other jobs"
tt['cpuCores'] = "Total number of CPU cores"
tt['availCpuCores'] = "Number of CPU cores that have not been requested by other jobs"
tt['jobId'] = "Job ID assigned by the batch scheduler"
tt['reqCpuCores'] = "Number of CPU cores requested by the user"
tt['reqMem'] = "Amount of memory requested by the user"
tt['reqVirtMem'] = "Amount of virtual memory requested by the user"
tt['usedWallTime'] = "Real time the job ran for"
tt['reqWallTime'] = "Max real time the job will run before it will be terminated by the batch scheduler"
tt['queue'] = "Batch scheduler queue"
tt['status'] = "Status of the job"
tt['pid'] = "Process ID"
tt['cmd'] = "The command name of this process, without arguments"
tt['%cpu'] = "The percentage of available CPU cycles occupied by this process. This is always an approximate figure, which is more accurate for longer running processes"
tt['%mem'] = "The percentage of physical memory occupied by this process"
tt['vm'] = "The total virtual memory size currently used by this process, in GB"
tt['vmpeak'] = "The total peak virtual memory size used by this process, in GB"

# Parsing handler for SAX events: extract information of processes for this machine
class MyHandler(xml.sax.ContentHandler):
  nodes = []
  hostname = ''
  processes = []
  save = False
  pattern = r'ps-[0-9]+$'
  
  def setHostName(self, hostname):
    self.hostname = hostname

  def startElement(self, name, attrs):
    if name == "HOST":
      hostpattern = '%s.*' % self.hostname
      if re.match(hostpattern, attrs.getValue("NAME")):
        self.save = True
      else:
      	self.save = False
      if "compute" in attrs.getValue("NAME"):
        self.nodes.append(attrs.getValue("NAME"))
 
    if name == "METRIC":
      attrname = attrs.getValue("NAME")
      if re.match(self.pattern, attrname) and self.save:
        value = attrs.getValue("VAL")
        if value != '':
          process = value.split('|')
          p = {}
          p['pid'] = process[0]
          p['cmd'] = process[1]
          p['user'] = process[2]
          p['%cpu'] = process[3]
          p['%mem'] = process[4]
          p['vm'] = round(float(process[5])/1024/1024,2)
          p['vmpeak'] = round(float(process[6])/1024/1024,2)
          self.processes.append(p)

# make sure we have a nodename here
def valid_nodename(form):
    trtable = string.maketrans(string.lowercase, string.lowercase)
    return form.has_key('nodename') and len(form['nodename'].value) < 50 


if valid_nodename(form):
  nodename = form['nodename'].value
  mpi_job_present = False
  try:
    
    # fetch process information from ganglia
    # get all information in XML format from ganglia gmond via netcat
    (stdout,stderr,rc) = system_call.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

    # parse XML
    handler = MyHandler()
    handler.setHostName(nodename)
    xml.sax.parseString(stdout, handler)
    
    processes = handler.processes
    
    (stdout,stderr,rc) = system_call.execute('%s get_machine_data %s' % (config.scheduler_command_prefix, nodename))
    nodetokens = stdout.splitlines()[1].split('|')
      
    jobtokens = ''
    if len(nodetokens) > 5 and nodetokens[5].strip():
      (stdout,stderr,rc) = system_call.execute('%s get_job_details %s' % (config.scheduler_command_prefix, nodetokens[5].replace(',',' ')))
      jobtokens = stdout.splitlines()[1:]

    info += "<h2>Node overview for node %s</h2>" % nodename
    info += "<p>(Mouse over the labels and table headers to get more information)</p>"
    info += "<table border=0>"
    info += "<tr><td><b><span title='%s'>Total Memory</span></b>:</td><td>%s</td></tr>" % (tt['physMem'], nodetokens[1])
    info += "<tr><td><b><span title='%s'>Available Memory</span></b>:</td><td>%s</td></tr>" % (tt['availMem'], nodetokens[2])
    info += "<tr><td><b><span title='%s'>CPU Cores</span></b>:</td><td>%s</td></tr>" % (tt['cpuCores'], nodetokens[3])
    info += "<tr><td><b><span title='%s'>Available CPU Cores</span></b>:</td><td>%s</td></tr>" % (tt['availCpuCores'], nodetokens[4])
    info += "</table><br>"

    info += '<b>Job started by the batch scheduler, and their allocated resources</b>:<br>'
    info += '<table id="jobs" class="tablesorter"><thead><tr>'
    info += '<th><span title="%s">Job ID</span></th>' % tt['jobId']
    info += '<th><span title="%s">User</span></th>' % tt['userId']
    info += '<th><span title="%s">Requested CPU Cores</span></th>' % tt['reqCpuCores']
    info += '<th><span title="%s">Requested Memory</span></th>' % tt['reqMem']
    info += '<th><span title="%s">Used Walltime [d+h:m:s]</span></th>' % tt['usedWallTime']
    info += '<th><span title="%s">Requested Walltime [d+h:m:s]</span></th>' % tt['reqWallTime']
    info += '<th><span title="%s">Status</span></th>' % tt['status']
    info += '<th><span title="%s">Queue</span></th>' % tt['queue']
    info += '</tr></thead><tbody>'

    if jobtokens != '':
      for token in jobtokens:
        if not token:
          continue
        t = token.split('|')
        geometry = t[11]
        for resources in geometry.split(','):
          try:
            node,cores,mem = resources.split(':')
          except:
            continue
          if node == nodename:
            break
        info += '<tr>'
        info += '<td><a href=./showjob.cgi?jobid=%s>%s</a>' % (t[0],t[0])
        if len(geometry.split(',')) > 1:
          mpi_job_present = True
          info += ' (*)'
        info += '</td>'
        info += '<td><a href="./showq.cgi?user=%s">%s</a></td>' % (t[1],t[1])
        info += '<td>%s</td>' % cores
        info += '<td>%s</td>' % mem
        info += '<td>%s</td>' % t[10]
        info += '<td>%s</td>' % t[9]
        info += '<td>%s</td>' % t[2]
        info += '<td>%s</td>' % t[3]
        info += '</tr>'
      info += '</tbody></table>'

      if mpi_job_present:
        info += "(*) This job runs on multiple nodes. The displayed memory related and CPU core related parameters of this job apply to this node only. "
        info += "Click on the jobid for full information about the job.<br>"

    # System process information
    info += "<br><b>Process information</b>:<br>"
    info += "Note: There might be up to 15s delay to sync the processes belonging to a job<br>"
    info += '<table id="processes" class="tablesorter"><thead><tr>'
    info += '<th><span title="%s">PID</span></th>' % tt['pid']
    info += '<th><span title="%s">User</span></th>' % tt['userId']
    info += '<th><span title="%s">%%CPU</span></th>' % tt['%cpu']
    info += '<th><span title="%s">%%MEM</span></th>' % tt['%mem']
    info += '<th><span title="%s">vm [GB]</span></th>' % tt['vm']
    info += '<th><span title="%s">Peak vm [GB]</span></th>' % tt['vmpeak']
    info += '<th><span title="%s">Command</span></th>' % tt['cmd']
    info += '</tr></thead><tbody>'
  
    for p in processes:
      info += '<tr>'
      info += '<td>%s</td>' % p['pid']
      info += '<td>%s</td>' % p['user']
      info += '<td>%s</td>' % p['%cpu']
      info += '<td>%s</td>' % p['%mem']
      info += '<td>%s</td>' % p['vm']
      info += '<td>%s</td>' % p['vmpeak']
      info += '<td>%s</td>' % p['cmd']
      info += '</tr>'
    info += '</tbody></table>'    
  except:
    info = "Failed to gather node information:<br><pre>%s</pre>" % traceback.format_exc()
    failure = True
else:
  failure = True

# print response
print '''Content-Type: text/html

<html>
  <head>
    <link rel="stylesheet" href="/jobs/style/tablesorter/theme.default.css" type="text/css" media="print, screen"/>
    <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
    <script type="text/javascript" src="/jobs/js/jquery-1.8.3.min.js"></script>
    <script type="text/javascript" src="/jobs/js/jquery.blockUI.2.39.js"></script>
    <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
    <script type="text/javascript">
    
      function reloadWithNode(nodename) {
        location.href='./shownode.cgi?nodename=' + nodename;
      }
    
      $(document).ready(function() {
'''

if not failure: 
  print "$(\"#jobs\").tablesorter({sortList:[[2,1]]});"
  print "$(\"#processes\").tablesorter({sortList:[[2,1]]});"
else:
  (stdout,stderr,rc) = system_call.execute('%s get_nodes' % config.scheduler_command_prefix)
  nodes = stdout.splitlines()

  # get cluster node list and display as modal
  string = '<b>Pick a node</b>: <select onchange="reloadWithNode(this.value)"><option value=""></option>'
  for node in sorted(nodes):
    string += '<option value="%s">%s</option>' % (node, node)
  string += '</select>'  
  print "var str = '%s';" % string
  print "$.blockUI({ message: str });"  

print '''
      });
    </script>
</head>
<body>
'''

print info
#print '<center><img src="/jobs/pics/construction.jpg"/><font color="003366"><h1>Porting to SLURM... coming soon</h1></font></center>'

print "</div></body></html>"


