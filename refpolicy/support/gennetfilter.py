import re

NETPORT = re.compile("^network_port\(\s*\w+\s*(\s*,\s*\w+\s*,\s*\w+\s*,\s*\w+\s*)+\s*\)\s*$")

DEFAULT_PACKET = "packet_t"
PACKET_INPUT = "_server_packet_t"
PACKET_OUTPUT = "_client_packet_t"

packets = []

class Port:
	def __init__(self, proto, num, mls_sens, mcs_cats=""):
		# protocol of the port
		self.proto = proto

		# port number
		self.num = num

		# MLS sensitivity
		self.mls_sens = mls_sens

		# MCS categories
		# not currently supported, so we always get s0
		if mcs_cats == "":
			self.mcs_cats = "s0"
		else
			self.mcs_cats = "s0:"+mcs_cats

class Packet:
	def __init__(self, prefix, ports):
		# prefix
		self.prefix = prefix

		# A list of Ports
		self.ports = ports

def print_input_rules():
	print "-A selinux_new_input -j SECMARK --selctx system_u:object_r:"+DEFAULT_PACKET
	for i in packets:
		for j in i.ports:
			output_line="-A selinux_new_input -p "+j.proto+" --dport "+j.num+" -j SECMARK --selctx system_u:object_r:"+i.prefix+PACKET_INPUT

	print "-A selinux_new_input -j CONNSECMARK --save"
	print "-A selinux_new_input -j RETURN"

def print_output_rules():
	print "-A selinux_new_output -j SECMARK --selctx system_u:object_r:"+DEFAULT_PACKET
	for i in packets:
		for j in i.ports:
			print "-A selinux_new_output -p "+j.proto+" --dport "+j.num+" -j SECMARK --selctx system_u:object_r:"+i.prefix+PACKET_OUTPUT

	print "-A selinux_new_output -j CONNSECMARK --save"
	print "-A selinux_new_output -j RETURN"

def parse_corenet(file_name):
	corenet_te_in = open(file_name, "r")

	while True:
		corenet_line = corenet_te_in.readline()

		# If EOF has been reached:
		if not corenet_line:
			break

		if NETPORT.match(corenet_line):
			corenet_line = corenet_line.strip();

			# parse out the parameters
			parms = re.split('\W+',corenet_line[13:-1])
			name = parms[0]
			del parms[0];

			ports = []
			while len(parms) > 0:
				# add a port combination.
				ports.append(Port(parms[0],parms[1],parms[2]))
				del parms[:3]

			packets.append(Packet(name,ports))
		
	corenet_te_in.close()

def write_netfilter_config():
	print "*mangle"
	print ":PREROUTING ACCEPT [0:0]"
	print ":INPUT ACCEPT [0:0]"
	print ":FORWARD ACCEPT [0:0]"
	print ":OUTPUT ACCEPT [0:0]"
	print ":POSTROUTING ACCEPT [0:0]"
	print ":selinux_input [0:0]"
	print ":selinux_output [0:0]"
	print ":selinux_new_input [0:0]"
	print ":selinux_new_output [0:0]"
	print "-A INPUT -j selinux_input"
	print "-A OUTPUT -j selinux_output"
	print "-A selinux_input -m state --state NEW -j selinux_new_input"
	print "-A selinux_input -m state --state RELATED,ESTABLISHED -j CONNSECMARK --restore"
	print "-A selinux_output -m state --state NEW -j selinux_new_output"
	print "-A selinux_output -m state --state RELATED,ESTABLISHED -j CONNSECMARK --restore"
	print_input_rules()
	print_output_rules()
	print "COMMIT"

parse_corenet("policy/modules/kernel/corenetwork.te.in")
write_netfilter_config()
