'''
This script describes and sets up our Mininiet instance
We manually build a simple topology:

delegator1---S2----delegator2
	|     __/  \__    |
	|  __/		  \__ |
	S1/				 \S2
	|				  |
	|				  |
  client		   attacker

We also include sFlow in the Mininet instance, so that
we can monitor (visualize) traffic on the network.
Furthermore, sFlow enables use of IDS tools like
FastNetMon. 
Disclaimer: We have NOT written the code, enableling sFlow

Also, noteworthy is that we install queues (0 and 1)
on all switches, for the purpose of throttling.
'''

from mininet.net import Mininet
from mininet.topo import LinearTopo
from mininet.node import OVSKernelSwitch, OVSSwitch, RemoteController, Host, CPULimitedHost
from threading import Thread
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.clean import Cleanup
import os, time
from mininet.util import quietRun
from mininet.link import Intf
from mininet.log import setLogLevel, info
from mininet.nodelib import LinuxBridge
import thread, threading

#--------------------SFLOW SEGMENT START----------------------------
from mininet.util import quietRun
from requests import put
from json import dumps
from subprocess import call, check_output
from os import listdir
import re
import socket

collector = '127.0.0.1'
sampling = 10
polling = 10

def getIfInfo(ip):
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect((ip, 0))
  ip = s.getsockname()[0]
  ifconfig = check_output(['ifconfig'])
  ifs = re.findall(r'^(\S+).*?inet addr:(\S+).*?', ifconfig, re.S|re.M)
  for entry in ifs:
    if entry[1] == ip:
      return entry

def configSFlow(net,collector,ifname):
  print "*** Enabling sFlow:"
  sflow = 'ovs-vsctl -- --id=@sflow create sflow agent=%s target=%s sampling=%s polling=%s --' % (ifname,collector,sampling,polling)
  for s in net.switches:
    sflow += ' -- set bridge %s sflow=@sflow' % s
  print ' '.join([s.name for s in net.switches])
  quietRun(sflow)

def sendTopology(net,agent,collector):
  print "*** Sending topology"
  topo = {'nodes':{}, 'links':{}}
  for s in net.switches:
    topo['nodes'][s.name] = {'agent':agent, 'ports':{}}
  path = '/sys/devices/virtual/net/'
  for child in listdir(path):
    parts = re.match('(^s[0-9]+)-(.*)', child)
    if parts == None: continue
    ifindex = open(path+child+'/ifindex').read().split('\n',1)[0]
    topo['nodes'][parts.group(1)]['ports'][child] = {'ifindex': ifindex}
  i = 0
  for s1 in net.switches:
    j = 0
    for s2 in net.switches:
      if j > i:
        intfs = s1.connectionsTo(s2)
        for intf in intfs:
          s1ifIdx = topo['nodes'][s1.name]['ports'][intf[0].name]['ifindex']
          s2ifIdx = topo['nodes'][s2.name]['ports'][intf[1].name]['ifindex']
          linkName = '%s-%s' % (s1.name, s2.name)
          topo['links'][linkName] = {'node1': s1.name, 'port1': intf[0].name, 'node2': s2.name, 'port2': intf[1].name}
      j += 1
    i += 1

  put('http://'+collector+':8008/topology/json',data=dumps(topo))

def wrapper(fn,collector):
  def result( *args, **kwargs):
    res = fn( *args, **kwargs)
    net = args[0]
    (ifname, agent) = getIfInfo(collector)
    configSFlow(net,collector,ifname)
    sendTopology(net,agent,collector) 
    return res
  return result
#--------------------SFLOW SEGMENT END----------------------------

# Install q0 and q1 on a given switch interface
# with q1 employing the described throttling - queueSize
def InitializeThrottleQueue(switchInterface, minBitsPerSecond=0, 
	maxBitsPerSecond=10000000, queueSize=3000000):
	os.system("sudo ovs-vsctl -- set Port "+str(switchInterface)+" qos=@newqos -- \
--id=@newqos create QoS type=linux-htb other-config:max-rate="+str(maxBitsPerSecond)+" queues=0=@q0,1=@q1 -- \
--id=@q0 create Queue other-config:min-rate="+str(minBitsPerSecond)+" other-config:max-rate="+str(maxBitsPerSecond)+" -- \
--id=@q1 create Queue other-config:min-rate="+str(queueSize)+" other-config:max-rate="+str(queueSize))

os.system("sudo ovs-vsctl emer-reset")

net = Mininet(switch = OVSSwitch, autoSetMacs=True)

# Enable sFlow
setattr(Mininet, 'start', wrapper(Mininet.__dict__['start'], collector))

# Add the external POX controller (needs to run before running this script)
poxcontroller = net.addController(name="pox",
				controller=RemoteController, 
				ip="127.0.0.1", protocol="tcp", 
				port=6633) 

# Add hosts
client = net.addHost('h1')		#10.0.0.1
attacker = net.addHost('h2')	#10.0.0.2

# Add delegators
del1 = net.addHost('h3')		#10.0.0.3
del2 = net.addHost('h4')		#10.0.0.4

# Add switches
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
s3 = net.addSwitch('s3')

SwitchList = [s1, s2, s3]

# Add links
net.addLink(client, s1)
net.addLink(del1, s1)
net.addLink(del2, s3)
net.addLink(del1, s2)
net.addLink(del2, s2)
net.addLink(attacker, s3)
net.addLink(s1, s2)
net.addLink(s2, s3)

net.build()
# Added NAT, for the purpose of communicating into and out of Mininet
# as we wish to talk with ThrottleManager and Print Server (outside of MN)
net.addNAT().configDefault()
net.start()

# Install queues for each interface on each switch
print "Adding queues for switches..."
for switch in SwitchList:
	interfaces = switch.intfNames()
	for i in range(1, len(interfaces)):
		InitializeThrottleQueue(interfaces[i])
	# Print queues that have just been created
	os.system("sudo ovs-ofctl -O openflow10 queue-stats %s"%(switch.name))
print "Added queues for switches!"

net.pingAll()

# Start delegator program on the two delegators
delegatorPath = 'python Delegator.py'
delegator1 = net.get('h3')
delegator2 = net.get('h4')
thread.start_new_thread(delegator1.cmd, (delegatorPath, ))
thread.start_new_thread(delegator2.cmd, (delegatorPath, ))

# Enter the Mininet CLI
cli = CLI(net)

net.stop()
# Remember to run "sudo mn -c", after an Mininet instace has exited