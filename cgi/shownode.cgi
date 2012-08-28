#!/usr/bin/python

import os
import re
import traceback 
import string
import datetime
import cgi
import cgitb
import xml.sax
import cluster.util.factory as factory
from cluster import config
import cluster.util.system_call as systemcall

cgitb.enable()
form = cgi.FieldStorage()
info = ''
failure = False

# tooltips
tt = {}
tt['userId'] = "User ID"
tt['physMem'] = "Total amount of physical memory available on the node"
tt['availMem'] = "Amount of available memory that has not been requested by other jobs"
tt['cpuCores'] = "Total number of CPU cores"
tt['availCpuCores'] = "Number of CPU cores that have not been requested by other jobs"
tt['jobId'] = "Job ID assigned by the batch scheduler"
tt['reqCpuCores'] = "Number of CPU cores requested by the user"
tt['reqMem'] = "Amount of memory requested by the user"
tt['usedWallTime'] = "Real time the job ran for"
tt['reqWallTime'] = "Max real time the job will run before it will be terminated by the batch scheduler"
tt['queue'] = "Batch scheduler queue"
tt['pid'] = "Process ID"
tt['cmd'] = "The command name of this process, without arguments"
tt['%cpu'] = "The percentage of available CPU cycles occupied by this process. This is always an approximate figure, which is more accurate for longer running processes"
tt['%mem'] = "The percentage of physical memory occupied by this process"
tt['size'] = "The size of the 'text' memory segment of this process, in kilobytes. This approximately relates the size of the executable itself (depending on the BSS segment)"
tt['data'] = "Approximately the size of all dynamically allocated memory of this process, in kilobytes. Includes the Heap and Stack of the process. Defined as the 'resident' - 'shared' size, where resident is the total amount of physical memory used, and shared is defined below. Includes the the text segment as well if this process has no children"
tt['shared'] = "The size of the shared memory belonging to this process, in kilobytes. Defined as any page of this process' physical memory that is referenced by another process. Includes shared libraries such as the standard libc and loader"
tt['vm'] = "The total virtual memory size used by this process, in kilobytes"

# Parsing handler for SAX events: extract information of processes for this machine
class MyHandler(xml.sax.ContentHandler):
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
      
    if name == "METRIC":
      attrname = attrs.getValue("NAME")
      if re.match(self.pattern, attrname) and self.save:
        process = attrs.getValue("VAL")
        elements = process.split(',')
        p = {}
        for element in elements:
          (key,val) = element.split('=')
          p[key.strip()] = val.strip()
        self.processes.append(p)


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
    
    # fetch process information from ganglia
    # get all information in XML format from ganglia gmetad via netcat
    (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmetad_host, config.ganglia_gmetad_port))

    # parse XML
    handler = MyHandler()
    handler.setHostName(nodename)
    xml.sax.parseString(stdout, handler)
    
    processes = handler.processes
    
    nodeinfo = factory.create_node_instance(nodename).get_info()
    now = datetime.datetime.now()
    info += "<h2>Node overview for node %s</h2>" % nodeinfo['name']
    info += "<p>(Mouse over the labels and table headers to get more information)</p>"
    info += "<table border=0>"
    info += "<tr><td><b><span title='%s'>Physical Memory [GB]</span></b>:</td><td>%s</td></tr>" % (tt['physMem'], nodeinfo['phys_mem_gb'])
    info += "<tr><td><b><span title='%s'>Available Memory [GB]</span></b>:</td><td>%s</td></tr>" % (tt['availMem'], nodeinfo['avail_mem_gb'])
    info += "<tr><td><b><span title='%s'>CPU Cores</span></b>:</td><td>%s</td></tr>" % (tt['cpuCores'], nodeinfo['cores'])
    info += "<tr><td><b><span title='%s'>Available CPU Cores</span></b>:</td><td>%s</td></tr>" % (tt['availCpuCores'], nodeinfo['avail_cores'])
    info += "</table><br>"

    info += '<b>Job started by the batch scheduler, and their allocated resources</b>:<br>'
    info += '<table id="jobs" class="tablesorter"><thead><tr>'
    info += '<th><span title="%s">Job ID</span></th>' % tt['jobId']
    info += '<th><span title="%s">User</span></th>' % tt['userId']
    info += '<th><span title="%s">Requested CPU Cores</span></th>' % tt['reqCpuCores']
    info += '<th><span title="%s">Requested Memory [GB]</span></th>' % tt['reqMem']
    info += '<th><span title="%s">Used Walltime [h:m:s]</span></th>' % tt['usedWallTime']
    info += '<th><span title="%s">Requested Walltime [h:m:s]</span></th>' % tt['reqWallTime']
    info += '<th><span title="%s">Queue</span></th>' % tt['queue']
    info += '</tr></thead><tbody>'
      
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

    # System process information
    info += "<b>Process information</b>:<br>"
    info += '<table id="processes" class="tablesorter"><thead><tr>'
    info += '<th><span title="%s">PID</span></th>' % tt['pid']
    info += '<th><span title="%s">User</span></th>' % tt['userId']
    info += '<th><span title="%s">Command</span></th>' % tt['cmd']
    info += '<th><span title="%s">%%CPU</span></th>' % tt['%cpu']
    info += '<th><span title="%s">%%MEM</span></th>' % tt['%mem']
    info += '<th><span title="%s">vm [kB]</span></th>' % tt['vm']
    info += '<th><span title="%s">size [kB]</span></th>' % tt['size']
    info += '<th><span title="%s">data [kB]</span></th>' % tt['data']
    info += '<th><span title="%s">shared [kB]</span></th>' % tt['shared']
    info += '</tr></thead><tbody>'
  
    for p in processes:
      info += '<tr>'
      info += '<td>%s</td>' % p['pid']
      info += '<td>%s</td>' % p['user']
      info += '<td>%s</td>' % p['cmd']
      info += '<td>%s</td>' % p['%cpu']
      info += '<td>%s</td>' % p['%mem']
      info += '<td>%s</td>' % p['vm']
      info += '<td>%s</td>' % p['size']
      info += '<td>%s</td>' % p['data']
      info += '<td>%s</td>' % p['shared']
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
  print "$(\"#processes\").tablesorter({sortList:[[3,1]], widgets:['zebra']});"
else:
  # get cluster node list and display as modal
  node_list = factory.create_nodes_instance().get_node_list()
  string = '<b>Pick a node</b>: <select>'
  for node in node_list:
    string += '''<option onclick="location.href=\\'./shownode.cgi?nodename=%s\\'">%s</option>''' % (node, node)
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

print "</div></body></html>"

