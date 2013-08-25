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
import cStringIO
from cluster import config
import cluster.util.system_call as systemcall

cgitb.enable()
form = cgi.FieldStorage()
colormaps = { 'cpu': [ '#ffffff', '#ffe6e5', '#ffcdcd', '#ffb4b4', '#ff9b9b', '#ff8282', '#ff6969', '#ff5050', '#ff3737', '#ff1e1e', '#ff0000', '#eeee00' ],
              'mem': [ '#ffffff', '#e6e5ff', '#cdcdff', '#b4b4ff', '#9b9bff', '#8282ff', '#6969ff', '#5050ff', '#3737ff', '#1e1eff', '#0000ff', '#eeee00' ] }
reload_interval_ms = 60000
failed_hosts = ''
overloaded_hosts = []
info = cStringIO.StringIO()
error = False

def createHeatmap(hostlist, category):
  global overloaded_hosts
  global failed_hosts
  global error
  html = cStringIO.StringIO()
  html.write('<table class="heatmap">')
  colcount = 0

  for host in hostlist:
    if colcount == 0:
      html.write('<tr>')
    if colcount != 0 and (colcount % numcols) == 0:
      html.write('</tr><tr>')

    values = handler.hostdict[host]
    try:
      if category == 'cpu':
        tooltip = "Host: %s\nCPU cores: %s\nNumber processes: %s" % (host, values['cpu_num'], values['num_processes'])
        usage = float(values['num_processes']) / int(values['cpu_num'])
        if float(values['num_processes']) > (float(values['cpu_num'])):
          overloaded_hosts.append({ 'node': host, 'numprocs': values['num_processes'], 'cpus': values['cpu_num'], 'overload': (float(values['num_processes']) - float(values['cpu_num'])) })
      elif category == 'mem':
        tooltip = "Host: %s\nMem total: %s\nMem free: %s" % (host, values['mem_total'], values['mem_free'])
        usage = (float(values['mem_total']) - int(values['mem_free'])) / int(values['mem_total'])
    except KeyError:
      error = True
      tooltip = "Host: %s\n(Error gathering metrics)" % (host)
      usage = 0
      if host not in failed_hosts:
        failed_hosts += '%s ' % host

    color_index = int(round(usage * 10))
    if color_index > 10:
      color_index = 11

    if category == 'cpu':
      color = colormaps['cpu'][color_index]
    else:
      color = colormaps['mem'][color_index]

    html.write('<td class="heatmap"><div onclick="location.href=\'./shownode.cgi?nodename=%s\'" title="%s" style="width:17px; height:17px; float:left; background:%s; cursor: pointer;"></div></td>' % (host, tooltip, color))
  
    colcount += 1

  while colcount < (numcols * numrows):
    html.write('<td class="heatmap">&nbsp;</td>')
    colcount += 1

  html.write('</tr></table>')
  tmp = html.getvalue();
  html.close()
  return tmp


# Parsing handler for SAX events 
class MyHandler(xml.sax.ContentHandler):
  hostdict = {}
  subnets = ["10.0.102", "10.0.103", "10.0.104", "10.0.105", "10.0.106", "10.0.111"]
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
  error = False
  showcpumem = False
  showcpu = False
  showmem = False
  if form.has_key('show'):
    if form['show'].value == 'cpumem':
      showcpumem = True
    elif form['show'].value == 'cpu':
      showcpu = True
    elif form['show'].value == 'mem':
      showmem = True

  # read header from file
  f = open('%s%s%s' % (os.path.dirname(__file__), os.sep, 'header.tpl'))
  info.write(f.read() % config.ganglia_main_page)
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

  info.write('<table cellpadding="10"><tr>')
  info.write('<td><b>CPU utilization</b><br>')
  info.write(createHeatmap(hostlist,'cpu'))
  info.write('</td>')
  info.write('<td><b>Memory utilization</b><br>')
  info.write(createHeatmap(hostlist,'mem'))
  info.write('</td>')
  info.write('''<td><br>
    These maps gives an overview of the cluster utilization.<br>Each square represents a cluster machine.<br>
    The color of a square represents the utilization of a cluster machine. The color encoding is
    <ul><li>white == no/low utilization</li><li>red/blue == high utilization</li><li>yellow == overloaded</li></ul>
    Note that this map represents the real utilization, and not the requested/scheduled utilisation.<br>
    Mouse over the squares to get more details about the machine.''')
  if error:
    info.write("<br><br><font color='red'><b>There was an error gathering information for the following hosts from Ganglia:</b></font><br>%s" % failed_hosts)
  info.write('</td></tr></table>')

  info.write('<table cellpadding="30"><tr>')
  # overloaded_hosts:
  info.write('<td>')
  info.write('<b>Cluster nodes where more processes/threads run than CPU cores available</b><br>')
  info.write('''<table id="overloaded_nodes_table" class="tablesorter">
    <thead>
      <tr>
        <th>Node</th>
        <th>OverLoad</th>
        <th>#Processes/Threads</th>
        <th>#CPU cores</th>
      </tr>
    </thead>
    <tbody>''')
  for node in overloaded_hosts:
    info.write('<tr><td><a href="./shownode.cgi?nodename=%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (node['node'], node['node'], node['overload'], node['numprocs'], node['cpus']))
  info.write('</tbody></table>')
  info.write('</td>')

  # hosts where weak processes run:
  info.write('<td>')
  info.write('<b>Cluster nodes where processes run that have CPU usage between 5% and 60%</b><br>')
  info.write('''<table id="nodes_with_weak_processes_table" class="tablesorter">
    <thead>
      <tr>
        <th>Node</th>
        <th>#Processes</th>
      </tr>
    </thead>
    <tbody>''')
  for key in handler.hostdict:
    if handler.hostdict[key]['num_weak_processes'] > 0:
      info.write('<tr><td><a href="./shownode.cgi?nodename=%s">%s</a></td><td>%s</td></tr>' % (key,key,handler.hostdict[key]['num_weak_processes']))
  info.write('</tbody></table>')
  info.write('</td>')
  info.write('</tr></table>')

 
except:
  info.write("Failed to create heatmap:<br><pre>%s</pre>" % traceback.format_exc())

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
        window.location.href = window.location.href;
      }

      function refresh() {
        window.location.reload(true);
      }
      setTimeout(refresh, %s);
   </script>
  </head>
  <body>''' % reload_interval_ms

print info.getvalue()
info.close()

print "</div></body></html>"
