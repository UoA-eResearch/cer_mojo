#!/usr/bin/python

import os
import math
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
colormap = [ 
 { 'c': '#ffffff', 'min': 0, 'max': 0, 'label': '0 kb/s' },
 { 'c': '#ffe3e3', 'min': 1, 'max': 9, 'label': '[ 1 kb/s - 10 kb/s )' },
 { 'c': '#ffc7c7', 'min': 10, 'max': 99, 'label': '[ 11 kb/s - 100 kb/s )' },
 { 'c': '#ffaaaa', 'min': 100, 'max': 999, 'label': '[ 100 kb/s - 1 mb/s )' },
 { 'c': '#ff8e8e', 'min': 1000, 'max': 9999, 'label': '[ 1 mb/s - 10 mb/s )' },
 { 'c': '#ff7272', 'min': 10000, 'max': 99999, 'label': '[ 10 mb/s - 100 mb/s )' },
 { 'c': '#ff5555', 'min': 100000, 'max': 999999, 'label': '[ 100 mb/s - 1 gb/s )' },
 { 'c': '#ff3939', 'min': 1000000, 'max': 9999999, 'label': '[ 1 gb/s - 10 gb/s )' },
 { 'c': '#ff1d1d', 'min': 10000000, 'max': 99999999, 'label': '[ 10 gb/s - infinity )' }
]

#categories = { "iconnect.kbin": "Data Received" , "iconnect.kbout": "Data Transmitted", "iconnect.pktin": "Packets Received", "iconnect.pktout": "Packets Transmitted" }
categories = { "iconnect.kbin": "Data Received" , "iconnect.kbout": "Data Transmitted" }
max = '41943040' # 40gb in kb
reload_interval_ms = 20000
hosts = {}
failed_hosts = []
info = cStringIO.StringIO()
error = False

def get_colormap_index(val_kb):
  if val_kb == 0:
    return 0
  else:
    for i in range(1, len(colormap)):
      if val_kb >= colormap[i]['min'] and val_kb <= colormap[i]['max']:
        return i
  raise Exception('problem with generating colormap index')

def transform_value(val_kb):
  val = long(val_kb)
  if val >= 1000000:
    return "%sgb/s" % str(round(float(val)/1000000,2))
  elif val >= 1000:
    return "%smb/s " % str(round(float(val)/1000,2))
  else:
    return "%skb/s" % val

def createHeatmap(category):
  global hosts
  global failed_hosts
  global error
  global max
  html = cStringIO.StringIO()
  html.write('<table class="heatmap">')
  colcount = 0

  for host in sorted(hosts.keys()):
    values = hosts[host]
    if colcount == 0:
      html.write('<tr>')
    if colcount != 0 and (colcount % numcols) == 0:
      html.write('</tr><tr>')
    if category in values:
      tooltip = "%s: %s" % (host, transform_value(values[category]))
      color='#ffffff'
      try:
        color_index = 0
        if long(values[category]) > 0:
          color_index = get_colormap_index(long(values[category]))
        color = colormap[color_index]['c']
      except:
        error = True
        usage = 0
        if host not in failed_hosts:
          failed_hosts.append(host)
    else:
      tooltip = "%s: %s kb/sec" % (host, 'N/A')
      color = "#00CCFF"

    html.write('<td class="heatmap"><div title="%s" style="width:15px; height:15px; float:left; background:%s; cursor: pointer;"></div></td>' % (tooltip, color))
    colcount += 1

  while colcount < (numcols * numrows):
    html.write('<td class="heatmap"><div style="width:15px; height:15px; float:left;"></div></td>')
    colcount += 1

  html.write('</tr></table>')
  tmp = html.getvalue();
  html.close()
  return tmp


# Parsing handler for SAX events 
class MyHandler(xml.sax.ContentHandler):
  global hosts
  global categories
  hosttmp = ''
  iptmp = ''

  def startElement(self, name, attrs):
    if name == "HOST":
      self.hosttmp = str(attrs.getValue("NAME"))
      self.iptmp = str(attrs.getValue("IP"))
    if name == "METRIC":
      attrname = str(attrs.getValue("NAME"))
      for category in categories.keys():
        if attrname == category:
          val = str(attrs.getValue("VAL"))
          if val:
            if not self.hosttmp in hosts:
              hosts[self.hosttmp] = {}
            hosts[self.hosttmp][attrname] = val  


try:
  error = False
  
  # get all information in XML format from ganglia gmond via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

  # parse XML
  handler = MyHandler()
  xml.sax.parseString(stdout, handler)
  
  # figure out table properties (num rows and cols)
  numcols = 0
  numrows = 0
  numhosts = len(hosts.keys())
  if (numhosts > 0):
    numcols = int(math.sqrt(numhosts))
  if numcols > 0:
    numrows = int(numhosts/numcols)
  if (numcols * numrows) != numhosts:
    numrows += 1

  info.write("<h3>Infiniband utilization maps</h3>")
  info.write('<table cellpadding="5"><tr>')
  for cat in categories.keys():
    info.write('<td><b>%s (%s)</b><br>' % (categories[cat], cat))
    info.write(createHeatmap(cat))
    info.write('</td>')
  info.write('<td>');
  info.write('''Color encoding:
    <table cellspacing="0" style="border:1px solid black">
     <tr><td style="border:1px solid black" bgcolor="#00CCFF">No data available</td></tr>''')
  for i in range(0,len(colormap)):
    info.write('<tr><td style="border:1px solid black" bgcolor="%s">%s</td></tr>' % (colormap[i]['c'], colormap[i]['label']))
  info.write('</table>')
  info.write('</td>');
  info.write('</tr></table>')
  if error:
    info.write("<br><br><font color='red'><b>There was an error gathering information for the following hosts:</b></font><br>%s" % ', '.join(failed_hosts))

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
