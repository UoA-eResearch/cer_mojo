#!/usr/bin/python

import os
import traceback
import json
import xml.sax
import cStringIO
import datetime
from cluster import config
import cluster.util.system_call as systemcall

colormap = [ '#ffffff', '#ffe6e6', '#ffcdcd', '#ffb4b4', '#ff9b9b', '#ff8282', '#ff6969', '#ff5050', '#ff3737', '#ff1e1e', '#ff0000', '#eeee00' ]
hosts = {}
result = { 'datetime': '%s' % datetime.datetime.now(), 'state': None }

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
      nodes[node_name]['cpusused'] = 0
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
            hosts[self.hosttmp]['cpusused'] += percent_cpu
          except:
            pass

  def endElement(self, name):
    if name == "HOST" and self.hosttmp in hosts:
      usage = hosts[self.hosttmp]['cpusused']
      machine = hosts[self.hosttmp]
      if usage:
         machine['cpusused'] = int(((usage - self.cpu_usage_threshold)/100)+1)
         usage = float(machine['cpusused']) / machine['cpus']
         color_index = int(round(usage * 10))
         if color_index > 10:
           color_index = 11
         color = colormap[color_index]
         machine['loadcolor'] = color
      else:
        color = colormap[0]
      machine['loadcolor'] = color

try:
  hosts = get_node_details()

  # get all information in XML format from ganglia gmond via netcat
  (stdout,stderr,rc) = systemcall.execute("nc %s %s" % (config.ganglia_gmond_aggregator, config.ganglia_gmond_port))

  # parse XML
  handler = MyHandler()
  xml.sax.parseString(stdout, handler)
except:
  info.write("Failed to create heatmap:<br><pre>%s</pre>" % traceback.format_exc())

# print response
result['state'] = hosts
info = cStringIO.StringIO()
#json.dump(result, info, sort_keys=True, indent=4, separators=(',', ': '))
json.dump(result, info, sort_keys=True)
body = info.getvalue()
print "Status: 200 OK"
print "Content-Type: application/json"
print "Length:", len(body)
print ""
print body

