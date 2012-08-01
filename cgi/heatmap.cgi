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
from cluster import config
import cluster.util.system_call as systemcall

cgitb.enable()
form = cgi.FieldStorage()
info = ''

colormap = [ '#ffffff', '#ffe6e5', '#ffcdcd', '#ffb4b4', '#ff9b9b', '#ff8282', '#ff6969', '#ff5050', '#ff3737', '#ff1e1e', '#ff0000', '#c40606' ]

reload_interval_ms = 60000

# Parsing handler for SAX events 
class MyHandler(xml.sax.ContentHandler):
  hostdict = {}
  hosttmp = ''

  def startElement(self, name, attrs):
    if name == "HOST":
      self.hosttmp = attrs.getValue("NAME")
      if self.hosttmp not in config.ganglia_blacklist:
        self.hostdict[self.hosttmp] = {}
    if name == "METRIC":
      attrname = attrs.getValue("NAME")
      if self.hosttmp in self.hostdict and (attrname == "load_one" or attrname == "mem_free" or attrname == "mem_total" or attrname == "cpu_num"):
        self.hostdict[self.hosttmp][attrname] = attrs.getValue("VAL")

try:

  mode = ''
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

  # get all information in XML format from ganglia gmetad via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmetad_host, config.ganglia_gmetad_port))

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
  for host in hostlist:
    if colcount == 0:
      info += '<tr>'
    if colcount != 0 and (colcount % numcols) == 0:
      info += '</tr><tr>'
    
    values = handler.hostdict[host] 
    tooltip = "Host: %s\nCPU cores: %s\nCurrent Load: %s\nMem total: %s\nMem free: %s" % (host, values['cpu_num'], values['load_one'], values['mem_total'], values['mem_free'])
    cpu_usage = float(values['load_one']) / int(values['cpu_num']) 
    mem_usage = (float(values['mem_total']) - int(values['mem_free'])) / int(values['mem_total'])
    
    if showcpu:
      color_index = int(round(cpu_usage * 10))
    elif showmem:
      color_index = int(round(mem_usage * 10))
    else:
      # create euclidian distance of cpu_usage and mem_usage to get the color_index
      color_index = int(round(math.sqrt(cpu_usage * cpu_usage + mem_usage * mem_usage) * 10))

    if color_index > 10:
      color_index = 11
      
    info += '<td class="heatmap"><div title="%s" style="width:30px; height:30px; float:left; background:%s;"></div></td>' % (tooltip, colormap[color_index])
    colcount += 1

  while colcount < (numcols * numrows):
    info += '<td>&nbsp;</td>'
    colcount += 1

  if mode == "naked":
    info += "</tr></table>"
  else:
    info += '</tr></table></td><td>'
    info += 'This map gives an overview of the cluster utilization.<br>Each square represents a cluster machine.<br>'
    info += 'The color of a square represents the utilization of a cluster machine. '
    info += 'If you show both system load and memory utilization the euclidian metric of both values is used.<br>' 
    info += 'The color encoding is'
    info += '<ul><li>white == no/low utilization</li><li>red == high utilization</li></ul>'
    info += 'Note that this map represents the real utilization, and not the requested/scheduled utilisation.<br><br>'
    info += 'Mouse over the squares to get more details about the machine.'
    info += '</td></tr></table>'
 
except:
  info += "Failed to create heatmap:<br><pre>%s</pre>" % traceback.format_exc()

# print response
print '''Content-Type: text/html

  <html>
  <head>
    <link rel="stylesheet" href="/jobs/style/main.css" type="text/css" media="print, screen"/>
    <style type="text/css">
      table.heatmap { border-collapse:collapse; }
      table.heatmap, th.heatmap, td.heatmap { border: 3px solid black; background-color:#444444; }
      td.heatmap { padding: 0px; }
    </style>
    <script type="text/javascript">
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
