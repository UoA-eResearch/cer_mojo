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
  
  def startElement(self, name, attrs):
    if name == "HOST":
      self.hostname = attrs.getValue("NAME")
      
    if name == "METRIC":
      attrname = attrs.getValue("NAME")
      if re.match(self.pattern, attrname):
        value = attrs.getValue("VAL")
        if value != '':
          process = value.split('|')
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


# read header from file
f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
info += f.read() % config.ganglia_main_page
f.close()

try:
    
  # fetch process information from ganglia
  # get all information in XML format from ganglia gmond via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

  # parse XML
  handler = MyHandler()
  xml.sax.parseString(stdout, handler)
    
  processes = handler.processes
  
  info += '<b>User processes on the cluster</b>:<br>'
  info += '<table id="processes" class="tablesorter"><thead><tr>'
  info += '<th><span title="%s">Cluster node</span></th>' % tt['hostname']
  info += '<th><span title="%s">PID</span></th>' % tt['pid']
  info += '<th><span title="%s">User</span></th>' % tt['userId']
  info += '<th><span title="%s">%%CPU</span></th>' % tt['%cpu']
  info += '<th><span title="%s">%%MEM</span></th>' % tt['%mem']
  info += '<th><span title="%s">vm [kB]</span></th>' % tt['vm']
  info += '<th><span title="%s">Peak vm [kB]</span></th>' % tt['vmpeak']
  info += '<th><span title="%s">Command</span></th>' % tt['cmd']
  info += '</tr></thead><tbody>'
  
  for p in processes:
    info += '<tr>'
    info += '<td>%s</td>' % p['hostname']
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
  print "$(\"#processes\").tablesorter({sortList:[[0,0]], widgets:['zebra']});"

print '''
      });
    </script>
</head>
<body>
'''

print info

print "</div></body></html>"

