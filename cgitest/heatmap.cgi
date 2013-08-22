#!/usr/bin/python

import re
import os
import traceback
import cgi
import cgitb
import xml.sax
import math
import shlex
import subprocess
from clustertest import config
import clustertest.util.system_call as systemcall

cgitb.enable()
form = cgi.FieldStorage()
info = ''

colormap = [ '#ffffff', '#ffe6e5', '#ffcdcd', '#ffb4b4', '#ff9b9b', '#ff8282', '#ff6969', '#ff5050', '#ff3737', '#ff1e1e', '#ff0000', '#c40606' ]

reload_interval_ms = 60000

# Parsing handler for SAX events 
class MyHandler(xml.sax.ContentHandler):
  hostdict = {}
  subnets = ["10.0.102", "10.0.103", "10.0.104", "10.0.105", "10.0.111"]
  hosttmp = ''
  iptmp = ''
  cpu_usage_threshold = 4
  weak_processes_lower_threshold = 5
  weak_processes_upper_threshold = 60

  def startElement(self, name, attrs):
    if name == "HOST":
      self.hosttmp = attrs.getValue("NAME")
      self.iptmp = attrs.getValue("IP")
      if self.hosttmp not in config.ganglia_blacklist and self.iptmp[0:8] in self.subnets:
        self.hostdict[self.hosttmp] = {}
        self.hostdict[self.hosttmp]['num_processes'] = 0
        self.hostdict[self.hosttmp]['num_weak_processes'] = 0
    if name == "METRIC" and self.iptmp[0:8] in self.subnets:
      attrname = attrs.getValue("NAME")
      if self.hosttmp in self.hostdict and (attrname == "mem_free" or attrname == "mem_total" or attrname == "cpu_num"):
        self.hostdict[self.hosttmp][attrname] = attrs.getValue("VAL")
      if "ps-" in attrname:
        val = attrs.getValue("VAL")
        if val != '':
          percent_cpu = float(val.split('|')[3])
          self.hostdict[self.hosttmp]['num_processes'] += int(((percent_cpu - self.cpu_usage_threshold)/100)+1)
          if percent_cpu > self.weak_processes_lower_threshold and percent_cpu < self.weak_processes_upper_threshold:
            self.hostdict[self.hosttmp]['num_weak_processes'] += 1

try:
  mode = ''
  error = False
  showcpumem = False
  showcpu = False
  showmem = False
  if form.has_key('mode') and form['mode'].value == 'naked':
    mode = form['mode'].value
  if form.has_key('show'):
    if form['show'].value == 'cpumem':
      showcpumem = True
    elif form['show'].value == 'cpu':
      showcpu = True
    elif form['show'].value == 'mem':
      showmem = True

  if mode != 'naked':
    # read header from file
    f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
    info += f.read() % config.ganglia_main_page
    f.close()

  # get all information in XML format from ganglia gmond via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

  # parse XML
  handler = MyHandler()
  xml.sax.parseString(stdout, handler)

  # figure out table properties (num rows and cols)
  hostlist = handler.hostdict.keys()
  hostlist.sort()
  numhosts = len(hostlist)
  numcols = int(math.sqrt(numhosts))
  numrows = int(numhosts/numcols)
  if (numcols * numrows) != numhosts:
    numrows += 1

  # print information
  cpumem_selected = ''
  cpu_selected = ''
  mem_selected = ''
  if showcpu:
    cpu_selected = 'selected="selected"'
  elif showmem:
    mem_selected = 'selected="selected"'
  else:
    cpumem_selected = 'selected="selected"'
    
  info += '''<form id='myform'>
      <select id="checker" onChange="reload()">
        <option value="cpumem" %s>Show system load and memory utilization</option>
        <option value="cpu" %s>Show system load only</option>
        <option value="mem" %s>Show memory utilization only</option>
      </select>
    </form>''' % (cpumem_selected, cpu_selected, mem_selected)
    
  if mode != "naked":
    info += '<table cellpadding="10"><tr><td>'

  info += '<table class="heatmap">'
  colcount = 0
  overloaded_hosts = []
  hosts_with_low_performing_processes = []
  failed_hosts = ''

  for host in hostlist:
    if colcount == 0:
      info += '<tr>'
    if colcount != 0 and (colcount % numcols) == 0:
      info += '</tr><tr>'
    
    values = handler.hostdict[host] 
    try:
      tooltip = "Host: %s\nCPU cores: %s\nNumber processes: %s\nMem total: %s\nMem free: %s" % (host, values['cpu_num'], values['num_processes'], values['mem_total'], values['mem_free'])
      cpu_usage = float(values['num_processes']) / int(values['cpu_num']) 
      mem_usage = (float(values['mem_total']) - int(values['mem_free'])) / int(values['mem_total'])
      if float(values['num_processes']) > (float(values['cpu_num'])+1):
        overloaded_hosts.append({ 'node': host, 'numprocs': values['num_processes'], 'cpus': values['cpu_num'], 'overload': (float(values['num_processes']) - float(values['cpu_num'])) })
    except KeyError:
      error = True
      tooltip = "Host: %s\n(Error gathering metrics)" % (host)
      cpu_usage = 0
      mem_usage = 0
      failed_hosts += '%s ' % host
    
    if showcpu:
      color_index = int(round(cpu_usage * 10))
    elif showmem:
      color_index = int(round(mem_usage * 10))
    else:
      # create euclidian distance of cpu_usage and mem_usage to get the color_index
      color_index = int(round(math.sqrt(cpu_usage * cpu_usage + mem_usage * mem_usage) * 10))

    if color_index > 10:
      color_index = 11
      
    info += '<td class="heatmap"><div onclick="location.href=\'./shownode.cgi?nodename=%s\'" title="%s" style="width:30px; height:30px; float:left; background:%s; cursor: pointer;"></div></td>' % (host, tooltip, colormap[color_index])
    colcount += 1

  while colcount < (numcols * numrows):
    info += '<td>&nbsp;</td>'
    colcount += 1

  info += '</tr></table>'
  if mode != 'naked':
    info += '''</td><td>
      This map gives an overview of the cluster utilization.<br>Each square represents a cluster machine.<br>
      The color of a square represents the utilization of a cluster machine.
      If you show both system load and memory utilization the euclidian metric of both values is used.<br> 
      The color encoding is
      <ul><li>white == no/low utilization</li><li>red == high utilization</li></ul>
      Note that this map represents the real utilization, and not the requested/scheduled utilisation.<br><br>
      Mouse over the squares to get more details about the machine.'''

  # overloaded_hosts:
  info += '<br><br><b>Cluster nodes where more processes/threads run than CPU cores available</b>:<br>'
  info += '''<table id="overloaded_nodes_table" class="tablesorter">
    <thead>
      <tr>
        <th>Node</th>
        <th>OverLoad</th>
        <th>#Processes/Threads</th>
        <th>#CPU cores</th>
      </tr>
    </thead>
    <tbody>'''
  for node in overloaded_hosts:
   info += '<tr><td><a href="./shownode.cgi?nodename=%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (node['node'], node['node'], node['overload'], node['numprocs'], node['cpus'])
  info += '</tbody></table>'

  # hosts where weak processes run:
  info += '<br><br><b>Cluster nodes where processes run that have CPU usage between 5% and 60%</b>:<br>'
  info += '''<table id="nodes_with_weak_processes_table" class="tablesorter">
    <thead>
      <tr>
        <th>Node</th>
        <th>#Processes</th>
      </tr>
    </thead>
    <tbody>'''
  for key in handler.hostdict:
    if handler.hostdict[key]['num_weak_processes'] > 0:
      info += '<tr><td><a href="./shownode.cgi?nodename=%s">%s</a></td><td>%s</td></tr>' % (key,key,handler.hostdict[key]['num_weak_processes'])
  info += '</tbody></table>'

  info += '</td></tr></table>'


  if error:
    info += "<font color='red'><b>There was an error gathering information for the following hosts from Ganglia:</b></font><br>%s" % failed_hosts
 
except:
  info += "Failed to create heatmap:<br><pre>%s</pre>" % traceback.format_exc()

# print response
print '''Content-Type: text/html

  <html>
  <head>
     <link rel="stylesheet" href="/jobs/style/tablesorter/blue/style.css" type="text/css" media="print, screen"/>
     <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
     <script type="text/javascript" src="/jobs/js/jquery-1.7.min.js"></script>
     <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
    <style type="text/css">
      table.heatmap { border-collapse:collapse; }
      table.heatmap, th.heatmap, td.heatmap { border: 3px solid black; background-color:#444444; }
      td.heatmap { padding: 0px; }
    </style>
    <script type="text/javascript">
      $(document).ready(function() {
          $("#overloaded_nodes_table").tablesorter({sortList:[[1,1]], widgets:['zebra']});
          $("#nodes_with_weak_processes_table").tablesorter({sortList:[[1,1]], widgets:['zebra']});
      });

      function reload() {
        var have_qs = window.location.href.indexOf("?");
        var mode = (window.location.href.indexOf("mode=naked") > -1) ? "naked" : "";
        var url = (have_qs===-1) ? window.location.href : window.location.href.substr(0,have_qs);
        var myselect = document.getElementById("checker");
        var selected_val = myselect.options[myselect.selectedIndex].value;
        if (selected_val == "cpu") {
          url += '?show=cpu';
        } else if (selected_val == "mem") {
          url += '?show=mem';
        } else {
          url += '?show=cpumem';        
        }
        if (mode == 'naked') {
          url += "&mode=naked";
        }
        window.location.href = url;
      }

      function refresh() {
        window.location.reload(true);
      }
      setTimeout(refresh, %s);
   </script>
  </head>
  <body>''' % reload_interval_ms

print info

print "</div></body></html>"
