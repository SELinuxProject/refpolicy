#!/usr/bin/env python3

# Author: Chris PeBenito <cpebenito@tresys.com>
#
# Copyright (C) 2006 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

import sys,getopt,re

NETPORT = re.compile(r"^network_port\(\s*\w+\s*(\s*,\s*\w+\s*,\s*[-0-9]+\s*,\s*\w+\s*)+\s*\)\s*(#|$)")

DEFAULT_INPUT_PACKET = "server_packet_t"
DEFAULT_OUTPUT_PACKET = "client_packet_t"
DEFAULT_MCS = "s0"
DEFAULT_MLS = "s0"

PACKET_INPUT = "_server_packet_t"
PACKET_OUTPUT = "_client_packet_t"
ICMP_PACKET = "icmp_packet_t"

class Port:
	def __init__(self, proto, num, mls_sens):
		# protocol of the port
		self.proto = proto

		# port number
		self.num = num

		# MLS sensitivity
		self.mls_sens = mls_sens

		# MCS categories
		# not currently supported, so we always get s0
		self.mcs_cats = DEFAULT_MCS

class Packet:
	def __init__(self, prefix, ports):
		# prefix
		self.prefix = prefix

		# A list of Ports
		self.ports = ports

def print_nft_secmarks(packets,mls,mcs):
	line = '\tsecmark default_input_packet {\n\t\t"system_u:object_r:'+DEFAULT_INPUT_PACKET
	if mcs:
		line += ":"+DEFAULT_MCS
	elif mls:
		line += ":"+DEFAULT_MLS
	line += '"\n\t}\n\tsecmark default_output_packet {\n\t\t"system_u:object_r:'+DEFAULT_OUTPUT_PACKET
	if mcs:
		line += ":"+DEFAULT_MCS
	elif mls:
		line += ":"+DEFAULT_MLS
	line += '"\n\t}'
	print(line)
	line = '\tsecmark icmp_packet {\n\t\t"system_u:object_r:'+ICMP_PACKET
	if mcs:
		line += ":"+DEFAULT_MCS
	elif mls:
		line += ":"+DEFAULT_MLS
	line += '"\n\t}'
	print(line)
	for i in packets:
		line = "\tsecmark "+i.prefix+'_input {\n\t\t"system_u:object_r:'+i.prefix+PACKET_INPUT
		if mcs:
			line += ":"+DEFAULT_MCS
		elif mls:
			line += ":"+DEFAULT_MLS
		line += '"\n\t}\n\tsecmark '+i.prefix+'_output {\n\t\t"system_u:object_r:'+i.prefix+PACKET_OUTPUT
		if mcs:
			line += ":"+DEFAULT_MCS
		elif mls:
			line += ":"+DEFAULT_MLS
		line += '"\n\t}'
		print(line)

def print_nft_rules(packets,mls,mcs,direction):
	for i in packets:
		for j in i.ports:
			print("\t\tct state new "+j.proto+" dport "+j.num+' meta secmark set "'+i.prefix+'_'+direction+'"')
	print('\t\tip protocol icmp meta secmark set "icmp_packet"')
	print('\t\tip6 nexthdr icmpv6 meta secmark set "icmp_packet"')

def print_input_rules(packets,mls,mcs):
	line = "base -A selinux_new_input -j SECMARK --selctx system_u:object_r:"+DEFAULT_INPUT_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS

	print(line)

	line = "base -A selinux_new_input -p icmp -j SECMARK --selctx system_u:object_r:"+ICMP_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS
	print(line)

	line = "base -A selinux_new_input -p icmpv6 -j SECMARK --selctx system_u:object_r:"+ICMP_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS
	print(line)

	for i in packets:
		for j in i.ports:
			line="base -A selinux_new_input -p "+j.proto+" --dport "+re.sub('-', ':', j.num)+" -j SECMARK --selctx system_u:object_r:"+i.prefix+PACKET_INPUT
			if mls:
				line += ":"+j.mls_sens
			elif mcs:
				line += ":"+j.mcs_cats
			print(line)

	print("post -A selinux_new_input -j CONNSECMARK --save")
	print("post -A selinux_new_input -j RETURN")

def print_output_rules(packets,mls,mcs):
	line = "base -A selinux_new_output -j SECMARK --selctx system_u:object_r:"+DEFAULT_OUTPUT_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS
	print(line)

	line = "base -A selinux_new_output -p icmp -j SECMARK --selctx system_u:object_r:"+ICMP_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS
	print(line)

	line = "base -A selinux_new_output -p icmpv6 -j SECMARK --selctx system_u:object_r:"+ICMP_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS
	print(line)

	for i in packets:
		for j in i.ports:
			line = "base -A selinux_new_output -p "+j.proto+" --dport "+re.sub('-', ':', j.num)+" -j SECMARK --selctx system_u:object_r:"+i.prefix+PACKET_OUTPUT
			if mls:
				line += ":"+j.mls_sens
			elif mcs:
				line += ":"+j.mcs_cats
			print(line)

	print("post -A selinux_new_output -j CONNSECMARK --save")
	print("post -A selinux_new_output -j RETURN")

def parse_corenet(file_name):
	packets = []

	corenet_te_in = open(file_name, "r")

	while True:
		corenet_line = corenet_te_in.readline()

		# If EOF has been reached:
		if not corenet_line:
			break

		if NETPORT.match(corenet_line):
			corenet_line = corenet_line.strip()

			# parse out the parameters
			openparen = corenet_line.find('(')+1
			closeparen = corenet_line.find(')',openparen)
			parms = re.split(r'[^-a-zA-Z0-9_]+',corenet_line[openparen:closeparen])
			name = parms[0]
			del parms[0]

			ports = []
			while len(parms) > 0:
				# add a port combination.
				ports.append(Port(parms[0],parms[1],parms[2]))
				del parms[:3]

			packets.append(Packet(name,ports))

	corenet_te_in.close()

	return packets

def print_netfilter_config_nft(packets,mls,mcs):
	print("#!/usr/sbin/nft -f")
	print("flush ruleset")
	print("table inet security {")
	print_nft_secmarks(packets,mls,mcs)
	print("\tchain INPUT {")
	print("\t\ttype filter hook input priority 0; policy accept;")
	print('\t\tct state new meta secmark set "default_input_packet"')
	print_nft_rules(packets,mls,mcs,'input')
	print("\t\tct state new ct secmark set meta secmark")
	print("\t\tct state established,related meta secmark set ct secmark")
	print("\t}")
	print("\tchain FORWARD {")
	print("\t\ttype filter hook forward priority 0; policy accept;")
	print("\t}")
	print("\tchain OUTPUT {")
	print("\t\ttype filter hook output priority 0; policy accept;")
	print('\t\tct state new meta secmark set "default_output_packet"')
	print_nft_rules(packets,mls,mcs,'output')
	print("\t\tct state new ct secmark set meta secmark")
	print("\t\tct state established,related meta secmark set ct secmark")
	print("\t}")
	print("}")

def print_netfilter_config_iptables(packets,mls,mcs):
	print("pre *mangle")
	print("pre :PREROUTING ACCEPT [0:0]")
	print("pre :INPUT ACCEPT [0:0]")
	print("pre :FORWARD ACCEPT [0:0]")
	print("pre :OUTPUT ACCEPT [0:0]")
	print("pre :POSTROUTING ACCEPT [0:0]")
	print("pre :selinux_input - [0:0]")
	print("pre :selinux_output - [0:0]")
	print("pre :selinux_new_input - [0:0]")
	print("pre :selinux_new_output - [0:0]")
	print("pre -A INPUT -j selinux_input")
	print("pre -A OUTPUT -j selinux_output")
	print("pre -A selinux_input -m state --state NEW -j selinux_new_input")
	print("pre -A selinux_input -m state --state RELATED,ESTABLISHED -j CONNSECMARK --restore")
	print("pre -A selinux_output -m state --state NEW -j selinux_new_output")
	print("pre -A selinux_output -m state --state RELATED,ESTABLISHED -j CONNSECMARK --restore")
	print_input_rules(packets,mls,mcs)
	print_output_rules(packets,mls,mcs)
	print("post COMMIT")

mls = False
mcs = False
nft = False

try:
	opts, paths = getopt.getopt(sys.argv[1:],'mcn',['mls','mcs','nft'])
except getopt.GetoptError:
	print("Invalid options.")
	sys.exit(1)

for o, a in opts:
	if o in ("-c","--mcs"):
		mcs = True
	if o in ("-m","--mls"):
		mls = True
	if o in ("-n","--nft"):
		nft = True

if len(paths) == 0:
	sys.stderr.write("Need a path for corenetwork.te.in!\n")
	sys.exit(1)
elif len(paths) > 1:
	sys.stderr.write("Ignoring extra specified paths\n")

packets=parse_corenet(paths[0])
if nft:
        print_netfilter_config_nft(packets,mls,mcs)
else:
        print_netfilter_config_iptables(packets,mls,mcs)
