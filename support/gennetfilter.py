#!/usr/bin/python

# Author: Chris PeBenito <cpebenito@tresys.com>
#
# Copyright (C) 2006 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

import sys,string,getopt,re

NETPORT = re.compile("^network_port\(\s*\w+\s*(\s*,\s*\w+\s*,\s*\w+\s*,\s*\w+\s*)+\s*\)\s*(#|$)")

DEFAULT_INPUT_PACKET = "server_packet_t"
DEFAULT_OUTPUT_PACKET = "client_packet_t"
DEFAULT_MCS = "s0"
DEFAULT_MLS = "s0"

PACKET_INPUT = "_server_packet_t"
PACKET_OUTPUT = "_client_packet_t"

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
		self.mcs_cats = DEFAULT_MCS

class Packet:
	def __init__(self, prefix, ports):
		# prefix
		self.prefix = prefix

		# A list of Ports
		self.ports = ports

def print_input_rules(packets,mls,mcs):
	line = "base -A selinux_new_input -j SECMARK --selctx system_u:object_r:"+DEFAULT_INPUT_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS

	print line

	for i in packets:
		for j in i.ports:
			line="base -A selinux_new_input -p "+j.proto+" --dport "+j.num+" -j SECMARK --selctx system_u:object_r:"+i.prefix+PACKET_INPUT
			if mls:
				line += ":"+j.mls_sens
			elif mcs:
				line += ":"+j.mcs_cats
			print line

	print "post -A selinux_new_input -j CONNSECMARK --save"
	print "post -A selinux_new_input -j RETURN"

def print_output_rules(packets,mls,mcs):
	line = "base -A selinux_new_output -j SECMARK --selctx system_u:object_r:"+DEFAULT_OUTPUT_PACKET
	if mls:
		line += ":"+DEFAULT_MLS
	elif mcs:
		line += ":"+DEFAULT_MCS
	print line

	for i in packets:
		for j in i.ports:
			line = "base -A selinux_new_output -p "+j.proto+" --dport "+j.num+" -j SECMARK --selctx system_u:object_r:"+i.prefix+PACKET_OUTPUT
			if mls:
				line += ":"+j.mls_sens
			elif mcs:
				line += ":"+j.mcs_cats
			print line

	print "post -A selinux_new_output -j CONNSECMARK --save"
	print "post -A selinux_new_output -j RETURN"

def parse_corenet(file_name):
	packets = []

	corenet_te_in = open(file_name, "r")

	while True:
		corenet_line = corenet_te_in.readline()

		# If EOF has been reached:
		if not corenet_line:
			break

		if NETPORT.match(corenet_line):
			corenet_line = corenet_line.strip();

			# parse out the parameters
			openparen = string.find(corenet_line,'(')+1
			closeparen = string.find(corenet_line,')',openparen)
			parms = re.split('\W+',corenet_line[openparen:closeparen])
			name = parms[0]
			del parms[0];

			ports = []
			while len(parms) > 0:
				# add a port combination.
				ports.append(Port(parms[0],parms[1],parms[2]))
				del parms[:3]

			packets.append(Packet(name,ports))
		
	corenet_te_in.close()

	return packets

def print_netfilter_config(packets,mls,mcs):
	print "pre *mangle"
	print "pre :PREROUTING ACCEPT [0:0]"
	print "pre :INPUT ACCEPT [0:0]"
	print "pre :FORWARD ACCEPT [0:0]"
	print "pre :OUTPUT ACCEPT [0:0]"
	print "pre :POSTROUTING ACCEPT [0:0]"
	print "pre :selinux_input - [0:0]"
	print "pre :selinux_output - [0:0]"
	print "pre :selinux_new_input - [0:0]"
	print "pre :selinux_new_output - [0:0]"
	print "pre -A INPUT -j selinux_input"
	print "pre -A OUTPUT -j selinux_output"
	print "pre -A selinux_input -m state --state NEW -j selinux_new_input"
	print "pre -A selinux_input -m state --state RELATED,ESTABLISHED -j CONNSECMARK --restore"
	print "pre -A selinux_output -m state --state NEW -j selinux_new_output"
	print "pre -A selinux_output -m state --state RELATED,ESTABLISHED -j CONNSECMARK --restore"
	print_input_rules(packets,mls,mcs)
	print_output_rules(packets,mls,mcs)
	print "post COMMIT"

mls = False
mcs = False

try:
	opts, paths = getopt.getopt(sys.argv[1:],'mc',['mls','mcs'])
except getopt.GetoptError, error:
	print "Invalid options."
	sys.exit(1)

for o, a in opts:
	if o in ("-c","--mcs"):
		mcs = True
	if o in ("-m","--mls"):
		mls = True

if len(paths) == 0:
	sys.stderr.write("Need a path for corenetwork.te.in!\n")
	sys.exit(1)
elif len(paths) > 1:
	sys.stderr.write("Ignoring extra specified paths\n")

packets=parse_corenet(paths[0])
print_netfilter_config(packets,mls,mcs)
