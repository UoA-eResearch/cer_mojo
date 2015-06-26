#!/usr/bin/python

import os
import traceback
import cgi
import cgitb
import xml.sax
import math
import cStringIO
from cluster import config
import cluster.util.system_call as systemcall

cgitb.enable()
form = cgi.FieldStorage()
colormaps = { 'default': [ '#ffffff', '#ffe6e6', '#ffcdcd', '#ffb4b4', '#ff9b9b', '#ff8282', '#ff6969', '#ff5050', '#ff3737', '#ff1e1e', '#ff0000', '#eeee00' ],
              'dev_under': [ '#e6ffe6', '#cdffcd', '#b4ffb4', '#9bff9b', '#82ff82', '#69ff69', '#50ff50', '#37ff37', '#1eff1e', '#06ff06', '#00ff00' ],
              'dev_over': [ '#ffe6e6', '#ffcdcd', '#ffb4b4', '#ff9b9b', '#ff8282', '#ff6969', '#ff5050', '#ff3737', '#ff1e1e', '#ff0606', '#ff0000' ] }
views = {
  'cpusused': 'CPU cores: actual usage',
  'cpusreq': 'CPU cores: requested usage',
  'cpusdeviation': 'CPU cores: discrepancy used vs requested',
  'memused': 'Memory: actual usage',
  'memreq': 'Memory: requested usage',
  'memdeviation': 'Memory: discrepancy used vs requested',
}
reload_interval_ms = 180000
hosts = {}
failed_hosts = []
overloaded_hosts = []
info = cStringIO.StringIO()
error = False

def createHeatmap(category):
  global hosts
  global overloaded_hosts
  global failed_hosts
  global error
  html = cStringIO.StringIO()
  html.write('<table class="heatmap">')
  colcount = 0

  for host in hostlist:
    values = hosts[host]
    if colcount == 0:
      html.write('<tr>')
    if colcount != 0 and (colcount % numcols) == 0:
      html.write('</tr><tr>')
    tooltip = "Host: %s\n\nCPUs: %s\nCPUs requested: %s\nCPUs used: %s\n\nMemory [MB]: %.2f\nMemory requested [MB]: %.2f\nMemory used [MB]: %.2f\n\nVirtual Memory [MB]: %.2f\nVirtual Memory requested [MB]: %.2f\nVirtual Memory used [MB]: %.2f" % (
              host, values['cpus'], values['cpusreq'], values['cpusused'], values['mem_mb'], values['memreq_mb'], values['memused_mb'], values['vmem_mb'], values['vmemreq_mb'], values['vmemused_mb'])
    color='#ffffff'
    try:
      if category == 'cpusused':
        usage = float(values['cpusused']) / values['cpus']
        if usage > 1:
          overloaded_hosts.append({ 'node': host, 'numprocs': values['cpusused'], 'cpus': values['cpus'], 'overload': (float(values['cpusused']) - float(values['cpus'])) })
        color_index = int(round(usage * 10))
        if color_index > 10:
          color_index = 11
        color = colormaps['default'][color_index]
      elif category == 'cpusreq':
        usage = float(values['cpusreq']) / int(values['cpus'])
        color_index = int(round(usage * 10))
        if color_index > 10:
          color_index = 11
        color = colormaps['default'][color_index]
      elif category == 'cpusdeviation':
        usage = float(values['cpusused'] - values['cpusreq']) / values['cpus']
        color_index = int(round(usage * 10))
        if color_index < 0:
          if color_index < -10:
            color_index = -10
          color = colormaps['dev_under'][-color_index]
        elif color_index > 0:
          colmapsize = len(colormaps['dev_over'])
          if color_index > (colmapsize - 1):
            # TODO: handle outbreaks like this
            color_index = colmapsize - 1
          color = colormaps['dev_over'][color_index]
      elif category == 'memused':
        usage = float(values['memused_mb'] / values['mem_mb'])
        color_index = int(round(usage * 10))
        if color_index > 10:
          color_index = 11
        color = colormaps['default'][color_index]
      elif category == 'memreq':
        usage = float(values['memreq_mb']) / values['mem_mb']
        colmapsize = len(colormaps['default'])
        color_index = int(round(usage * 10))
        if color_index > (colmapsize - 1):
          color_index = colmapsize - 1
        color = colormaps['default'][color_index]
      elif category == 'memdeviation':
        usage = float(values['memused_mb'] - values['memreq_mb']) / values['mem_mb']
        color_index = int(round(usage * 10))
        if color_index < 0:
          if color_index < -10:
            color_index = -10
          color = colormaps['dev_under'][-color_index]
        elif color_index > 0:
          colmapsize = len(colormaps['dev_under'])
          if color_index > (colmapsize - 1):
            # TODO: handle outbreaks like this
            color_index = colmapsize - 1
          color = colormaps['dev_over'][color_index]
    except:
      error = True
      usage = 0
      raise 
      if host not in failed_hosts:
        failed_hosts.append(host)

    html.write('<td class="heatmap"><div onclick="location.href=\'./shownode.cgi?nodename=%s\'" title="%s" style="width:15px; height:15px; float:left; background:%s; cursor: pointer;"></div></td>' % (host, tooltip, color))
    colcount += 1

  while colcount < (numcols * numrows):
    html.write('<td class="heatmap"><div style="width:15px; height:15px; float:left;"></div></td>')
    colcount += 1

  html.write('</tr></table>')
  tmp = html.getvalue();
  html.close()
  return tmp

def get_nodes():
  nodes = []
  (stdout,stderr,rc) = systemcall.execute('%s get_nodes' % config.scheduler_command_prefix)
  if stdout:
    nodes = ' '.join(stdout.splitlines(True))
  return nodes

def get_node_details():
  command = 'get_machine_data %s' % get_nodes()
  nodes = {}
  (stdout,stderr,rc) = systemcall.execute('%s %s' % (config.scheduler_command_prefix, command))
  if stdout:
    lines = stdout.splitlines(True)[1:]
    for line in lines:
      if not line.strip():
        continue
      tokens = line.split('|')
      node_name = tokens[0]
      nodes[node_name] = {}
      nodes[node_name]['cpus'] = int(tokens[3])
      nodes[node_name]['cpusreq'] = int(tokens[3]) - int(tokens[4])
      nodes[node_name]['cpusused'] = 0
      nodes[node_name]['total_actual_load'] = 0
      nodes[node_name]['total_requested_load'] = int(nodes[node_name]['cpusreq']) * 100
      mem_mb = tokens[1]
      mem_avail_mb = tokens[2]
      if mem_mb.endswith('G'):
        mem_mb = int(mem_mb[0:-1]) * 1024
      elif mem_mb.endswith('M'):
        mem_mb = int(mem_mb[0:-1]) 
      else:
        mem_mb = int(mem_mb)

      if mem_avail_mb.endswith('P'):
        mem_avail_mb = int(float(mem_avail_mb[0:-1]) * 1024 * 1024)
      elif mem_avail_mb.endswith('G'):
        mem_avail_mb = int(float(mem_avail_mb[0:-1]) * 1024)
      elif mem_avail_mb.endswith('M'):
        mem_avail_mb = int(float(mem_avail_mb[0:-1]))
      elif mem_avail_mb.endswith('K'):
        mem_avail_mb = int(float(mem_avail_mb[0:-1]) / 1024)
      else:
        mem_avail_mb = int(mem_avail_mb)
      nodes[node_name]['mem_mb'] = mem_mb
      nodes[node_name]['memreq_mb'] = mem_mb - mem_avail_mb
      nodes[node_name]['memused_mb'] = 0
      nodes[node_name]['vmem_mb'] = mem_mb
      nodes[node_name]['vmemreq_mb'] = mem_mb - mem_avail_mb
      nodes[node_name]['vmemused_mb'] = 0
      nodes[node_name]['num_weak_processes'] = 0
  return nodes
  
# Parsing handler for SAX events 
class MyHandler(xml.sax.ContentHandler):
  global hosts
  subnets = ["10.0.102", "10.0.103", "10.0.104", "10.0.105", "10.0.106", "10.0.111"]
  hosttmp = ''
  iptmp = ''
  cpu_usage_threshold = 4
  weak_processes_lower_threshold = 5
  weak_processes_upper_threshold = 60

  def startElement(self, name, attrs):
    if name == "HOST":
      self.hosttmp = attrs.getValue("NAME")
      if self.hosttmp.endswith('-p'):
        self.hosttmp = self.hosttmp[0:-2]
      self.iptmp = attrs.getValue("IP")
    if name == "METRIC" and self.iptmp[0:8] in self.subnets and self.hosttmp in hosts:
      attrname = attrs.getValue("NAME")
      if "ps-" in attrname:
        val = attrs.getValue("VAL")
        if val != '':
          try:
            percent_cpu = float(val.split('|')[3])
            percent_mem = float(val.split('|')[4])
            peak_vmem = float(val.split('|')[6])
            hosts[self.hosttmp]['total_actual_load'] += percent_cpu
            hosts[self.hosttmp]['cpusused'] += percent_cpu
            hosts[self.hosttmp]['memused_mb'] += (percent_mem * hosts[self.hosttmp]['mem_mb']) / 100
            hosts[self.hosttmp]['vmemused_mb'] += peak_vmem/1024
            if percent_cpu > self.weak_processes_lower_threshold and percent_cpu < self.weak_processes_upper_threshold:
              hosts[self.hosttmp]['num_weak_processes'] += 1
          except:
            pass

  def endElement(self, name):
    if name == "HOST" and self.hosttmp in hosts:
      usage = hosts[self.hosttmp]['cpusused']
      if usage:
         hosts[self.hosttmp]['cpusused'] = int(((usage - self.cpu_usage_threshold)/100)+1)

try:
  error = False
  view1='cpusused'
  view2='cpusreq'
  view3='cpusdeviation'

  if form.has_key('view1') and form['view1'].value in views:
    view1 = form['view1'].value
  if form.has_key('view2') and form['view2'].value in views:
    view2 = form['view2'].value
  if form.has_key('view3') and form['view3'].value in views:
    view3 = form['view3'].value
    
  select1='<select id="view1">'
  for view in sorted(views.keys()):
    if view == view1:
      select1 += '<option value="%s" selected>%s</option>' % (view,views[view])
    else:
      select1 += '<option value="%s">%s</option>' % (view,views[view])
  select1 += '</select>'
   
  select2='<select id="view2">'
  for view in sorted(views.keys()):
    if view == view2:
      select2 += '<option value="%s" selected>%s</option>' % (view,views[view])
    else:
      select2 += '<option value="%s">%s</option>' % (view,views[view])
  select2 += '</select>'
   
  select3='<select id="view3">'
  for view in sorted(views.keys()):
    if view == view3:
      select3 += '<option value="%s" selected>%s</option>' % (view,views[view])
    else:
      select3 += '<option value="%s">%s</option>' % (view,views[view])
  select3 += '</select>'
  
  button = '<button onclick="reload()">Go!</button>'
  
  hosts = get_node_details()
  
  # get all information in XML format from ganglia gmond via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

  # parse XML
  handler = MyHandler()
  xml.sax.parseString(stdout, handler)

  # Calculate total cluster load
  cluster_actual_load = 0.0
  cluster_requested_load = 0.0
  load_ratio = 0.0
  effective_load = 0.0

  for key in hosts.keys():
    cluster_actual_load += float(hosts[key]['total_actual_load']) / hosts[key]['cpus']
    cluster_requested_load += float(hosts[key]['total_requested_load']) / hosts[key]['cpus']
  cluster_actual_load = cluster_actual_load / len(hosts)
  cluster_requested_load = cluster_requested_load / len(hosts)
  if cluster_requested_load > 0:
    load_ratio = cluster_actual_load / cluster_requested_load
    effective_load = (cluster_actual_load / cluster_requested_load) * cluster_actual_load

  # figure out table properties (num rows and cols)
  hostlist = hosts.keys()
  hostlist.sort()
  numhosts = len(hostlist)
  numcols = int(math.sqrt(numhosts))
  numrows = int(numhosts/numcols)
  if (numcols * numrows) != numhosts:
    numrows += 1

  info.write('<b>Cluster load</b>: Actual: %s%%, Requested: %s%%, Load ratio: %s, Effective Load: %s%%<br><br>' % (int(cluster_actual_load), int(cluster_requested_load), round(load_ratio,2), int(effective_load)))
  info.write('<table cellpadding="5"><tr>')
  info.write('<td><b>%s</b><br>' % select1)
  info.write(createHeatmap(view1))
  info.write('</td>')
  info.write('<td><b>%s</b><br>' % select2)
  info.write(createHeatmap(view2))
  info.write('</td>')
  info.write('<td><b>%s %s</b><br>' % (select3, button))
  info.write(createHeatmap(view3))
  info.write('</td></tr></table>')
  info.write('''
    These maps gives an overview of the cluster utilization. Each square represents a cluster machine.
    The color encoding is
    <table cellspacing="3">
      <tr>
        <td>
          <b>Usage maps</b>:<br>
          white: no/low utilization<br>
          red: high utilization<br>
          yellow: host has suspended jobs, or is overloaded<br>
        </td>
        <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<td>
        <td>
          <b>Discrepancy maps</b>:<br>
          white: actual and requested utilization are the same<br>
          green: less actual utilization than requested<br>
          red: higher actual utilization than requested<br>
        </td>
      </tr>
    </table>
    Mouse over the squares to high-level information about the machine.
    Click on a square to see details about the machine.''')
  if error:
    info.write("<br><br><font color='red'><b>There was an error gathering information for the following hosts:</b></font><br>%s" % ', '.join(failed_hosts))

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
  for host in hosts:
    if hosts[host]['num_weak_processes'] > 0:
      info.write('<tr><td><a href="./shownode.cgi?nodename=%s">%s</a></td><td>%s</td></tr>' % (host,host,hosts[host]['num_weak_processes']))
  info.write('</tbody></table>')
  info.write('</td>')
  info.write('</tr></table>')

 
except:
  info.write("Failed to create heatmap:<br><pre>%s</pre>" % traceback.format_exc())

# print response
print '''Content-Type: text/html

  <html>
  <head>
     <meta http-equiv="Expires" content="-1">
     <link rel="stylesheet" href="/jobs/style/tablesorter/theme.default.css" type="text/css" media="print, screen"/>
     <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
     <script type="text/javascript" src="/jobs/js/jquery-1.8.3.min.js"></script>
     <script type="text/javascript" src="/jobs/js/jquery.tablesorter.min.js"></script>
    <style type="text/css">
      table.heatmap { border-collapse:collapse; }
      table.heatmap, th.heatmap, td.heatmap { border: 3px solid black; background-color:#444444; }
      td.heatmap { padding: 0px; }
    </style>
    <script type="text/javascript">
      $(document).ready(function() {
          $("#overloaded_nodes_table").tablesorter({sortList:[[1,1]]});
          $("#nodes_with_weak_processes_table").tablesorter({sortList:[[1,1]]});
      });

      function reload() {
        var view1 = $("#view1 option:selected").val();
        var view2 = $("#view2 option:selected").val();
        var view3 = $("#view3 option:selected").val();
        window.location.href = window.location.pathname + "?view1=" + view1 + "&view2=" + view2 + "&view3=" + view3;
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
