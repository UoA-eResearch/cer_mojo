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
  showmem = True
  showcpu = True
  if form.has_key('mode') and form['mode'].value == 'naked':
    mode = form['mode'].value
  if form.has_key('showmem') and form['showmem'].value == 'false':
    showmem = False
  if form.has_key('showcpu') and form['showcpu'].value == 'false':
    showcpu = False

   
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
  cpu_checked = ''
  mem_checked = ''
  if showcpu:
    cpu_checked = 'checked'
  if showmem:
    mem_checked = 'checked'

  info += '''<form id='checker'>
      <input type="checkbox" name="showcpu" onClick="reload(this.form)" %s>Show System Load
      <input type="checkbox" name="showmem" onClick="reload(this.form)" %s>Show Memory Utilization
    </form>''' % (cpu_checked, mem_checked);
     
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
    
    if not showmem and not showcpu:
      color_index = 0
    elif showmem and not showcpu:
      color_index = int(round(mem_usage * 10))
    elif showcpu and not showmem:
      color_index = int(round(cpu_usage * 10))
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
      function reload(myform) {
        var have_qs = window.location.href.indexOf("?");
        var mode = (window.location.href.indexOf("mode=naked") > -1) ? "naked" : "";
        var url = (have_qs===-1) ? window.location.href : window.location.href.substr(0,have_qs);
        if (!(myform.showcpu.checked)) {
          url += '?showcpu=false';
        }
        if (!myform.showmem.checked) {
          if (url.indexOf("?") === -1) {
            url += "?";
          } else {
            url += "&";
          }
          url += 'showmem=false';
        }
        if (mode == 'naked') {
          if (url.indexOf("?") === -1) {
            url += "?";
          } else {
            url += "&";
          }
          url += "mode=naked";
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