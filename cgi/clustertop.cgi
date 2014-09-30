#!/usr/bin/python

import os
import re
import traceback 
import string
import datetime
import cgi
import cgitb
import xml.sax
import cStringIO
from cluster import config
import cluster.util.system_call as systemcall

cgitb.enable()
form = cgi.FieldStorage()
info = cStringIO.StringIO()
failure = False

# tooltips
tt = {}
tt['hostname'] = "Name of the cluster node"
tt['userId'] = "User ID"
tt['pid'] = "Process ID"
tt['cmd'] = "The command name of this process, without arguments"
tt['%cpu'] = "The percentage of available CPU cycles occupied by this process. This is always an approximate figure, which is more accurate for longer running processes"
tt['%mem'] = "The percentage of physical memory occupied by this process"
tt['vm'] = "The total virtual memory size currently used by this process, in kilobytes"
tt['vmpeak'] = "The total virtual peak memory size used by this process, in kilobytes"

# Parsing handler for SAX events: extract information of processes for this machine
class MyHandler(xml.sax.ContentHandler):
  hostname = ''
  pattern = r'ps-[0-9]+$'
  processes = []
  cpu_threshold = 0.5
  memory_threshold = 0.5

  def startElement(self, name, attrs):
    if name == "HOST":
      self.hostname = attrs.getValue("NAME")
      
    if name == "METRIC":
      attrname = attrs.getValue("NAME")
      if re.match(self.pattern, attrname):
        value = attrs.getValue("VAL")
        if value != '':
          process = value.split('|')
          if float(process[3]) > self.cpu_threshold or float(process[4]) > self.memory_threshold:
            p = {}
            p['pid'] = process[0]
            p['cmd'] = process[1]
            p['user'] = process[2]
            p['%cpu'] = process[3]
            p['%mem'] = process[4]
            p['vm'] = process[5]
            p['vmpeak'] = process[6]
            p['hostname'] = self.hostname
            self.processes.append(p)

  def getProcessesSortedByHost(self):
    return sorted(self.processes, key=lambda x: x['hostname'])


try:
    
  # fetch process information from ganglia
  # get all information in XML format from ganglia gmond via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

  # parse XML
  handler = MyHandler()
  xml.sax.parseString(stdout, handler)
  processes = handler.getProcessesSortedByHost()
  
  info.write('<b>User processes on the cluster</b>:<br>')
  info.write('(Only processes that have more than %s%% CPU usage or use more than %s%% of the available memory are shown)<br>' % (handler.cpu_threshold, handler.memory_threshold))
  info.write('<table id="processes" class="tablesorter"><thead><tr>')
  info.write('<th><span title="%s">Cluster node</span></th>' % tt['hostname'])
  info.write('<th><span title="%s">PID</span></th>' % tt['pid'])
  info.write('<th><span title="%s">User</span></th>' % tt['userId'])
  info.write('<th><span title="%s">%%CPU</span></th>' % tt['%cpu'])
  info.write('<th><span title="%s">%%MEM</span></th>' % tt['%mem'])
  info.write('<th><span title="%s">vm [kB]</span></th>' % tt['vm'])
  info.write('<th><span title="%s">Peak vm [kB]</span></th>' % tt['vmpeak'])
  info.write('<th><span title="%s">Command</span></th>' % tt['cmd'])
  info.write('</tr></thead><tbody>')
  
  for p in processes:
    info.write('<tr>')
    info.write('<td>%s</td>' % p['hostname'])
    info.write('<td>%s</td>' % p['pid'])
    info.write('<td>%s</td>' % p['user'])
    info.write('<td>%s</td>' % p['%cpu'])
    info.write('<td>%s</td>' % p['%mem'])
    info.write('<td>%s</td>' % p['vm'])
    info.write('<td>%s</td>' % p['vmpeak'])
    info.write('<td>%s</td>' % p['cmd'])
    info.write('</tr>')
  info.write('</tbody></table>')
except:
  info.write("Failed to gather node information:<br><pre>%s</pre>" % traceback.format_exc())
  failure = True

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
'''

if not failure: 
  print "$(\"#processes\").tablesorter({sortList:[[0,0]]});"

print '''
      });
    </script>
</head>
<body>
'''

print info.getvalue()
info.close()
#print '<center><img src="/jobs/pics/construction.jpg"/><font color="003366"><h1>Porting to SLURM... coming soon</h1></font></center>'


print "</div></body></html>"
