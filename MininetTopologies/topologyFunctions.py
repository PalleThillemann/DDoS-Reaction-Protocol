from mininet.node import ( Host, CPULimitedHost, Controller, OVSController,
                           Ryu, NOX, RemoteController, findController,
                           DefaultController, NullController,
                           UserSwitch, OVSSwitch, OVSBridge,
                           IVSSwitch )
from mininet.net import Mininet
from mininet.cli import CLI

hostCounter = 1
switchCounter = 1


net = Mininet(switch=OVSSwitch, autoSetMacs=True)
net.addController(name="pox", controller=RemoteController, 
				ip="127.0.0.1", protocol="tcp", port=6633)

isp_one = ISP(net, 5, 2, 1)
isp_two = ISP(net, 4, 2, 2)

ConnectTwoISPs(net, isp_one, isp_two)


#has to build before able to get values
net.build()
nodes = net.values()

print(nodes)

class GatewaySwitch():
	def __init__(self, mininetSwitch):
		self.mininetSwitch = mininetSwitch
		self.IsConnectedToGateway = False

class ISP():
	#static variable for unique ID assignment
	static_id = 0

	def __init__(self, net, numberOfHosts, numberOfSwitches, numberOfGateways)
		self.net = net
		self.listOfHosts = AddHosts(numberOfHosts)
		self.listOfSwitches = AddSwitches(numberOfSwitches, True)
		self.listOfGateways = AddSwitches(numberOfGateways, False)
		#self.delegator = delegator
		self.id = static_id
		static_id += 1

		if self.listOfHosts and self.listOfSwitches #if both lists are not empty
			ConnectISPDevices()
		if self.listOfSwitches and self.listOfGateways
			ConnectSwitchesAndGateways()

	#example 5 hosts, 2 switches
	def ConnectISPDevices():
		number = self.listOfHosts/listOfSwitches
		j = 0
		for i in range(0, len(self.listOfSwitches)):
			while j < len(self.listOfHosts):
				self.net.addLink(self.listOfSwitches[i], self.listOfHosts[j])
				j += 1
				if j % len(self.listOfSwitches) == 0:
					break

		if len(self.listOfHosts)%2 != 0: #if number of hosts is uneven
			self.net.addLink(self.listOfHosts[-1], self.listOfSwitches[-1]) #link last hosts with last switch

		#example: list with 2 switches
		if len(self.listOfSwitches) > 1
			for i in range (0, len(self.listOfSwitches)-1)
				self.net.addLink(self.listOfSwitches[i], self.listOfSwitches[i+1])

	#example: 2 switches and 1 gateway
	def ConnectSwitchesAndGateways():
		for i in range(0, len(self.listOfSwitches))


	def AddHosts(net, numberOfHosts):
		hosts = []
		for i in range(0, numberOfHosts):
			host = net.addHost("h%d"% (hostCounter))
			hostCounter += 1
			hosts.append(host)
		return hosts

	def AddSwitches(net, numberOfSwitches, IsSwitch):
		switches = []
		if IsSwitch:
			for i in range(0, numberOfSwitches):
				switch = net.AddSwitch("s%d"% (switchCounter))
				switchCounter += 1
				switches.append(switch)
			return switches
		else #is gateway
			for i in range(0, numberOfSwitches):
				switch = GatewaySwitch(net.AddSwitch("s%d"% (switchCounter)))
				switchCounter += 1
				switches.append(switch)
			return switches

def ConnectTwoISPs(net, isp_a, isp_b):
	for i in range(0, isp_a.listOfGateways):
		for j in range(0, isp_b.listOfGateways):
			if isp_a.listOfGateways[i].IsConnectedToGateway == False and isp_b.listOfGateways[j].IsConnectedToGateway == False
				net.addLink(isp_a.listOfGateways[i].mininetSwitch, isp_b.listOfGateways[j].mininetSwitch)
				isp_a.listOfGateways[i].IsConnectedToGateway = True
				isp_b.listOfGateways[j].IsConnectedToGateway = True
				return True
	return False

'''

def ConnectHostsToSingleSwitch(net, hosts, switch)
	links = []
	for host in hosts
		links = net.addLinks(host, switch)

#how-to-link: always link all hosts with every switch. And every switch should have a maksimum of two connections to other switches
def SingleISP(net, numberOfHosts=3, numberOfSwitches=1):
	AddHosts(net, numberOfHosts)
	AddSwitches(net, numberOfSwitches)

	#connect 
	for switch in numberOfSwitches:
		for host in numberOfHosts:
			net.addLink(switch, host)

'''