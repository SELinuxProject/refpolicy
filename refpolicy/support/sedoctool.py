#!/usr/bin/python

#  Author: Joshua Brindle <jbrindle@tresys.com>
#
# Copyright (C) 2003 - 2005 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

"""
	this does dstuff
"""

import sys
import getopt
import pyplate
from xml.dom.ext import *
from xml.dom.ext.reader import Sax2

def read_policy_xml(filename):
	try:
		reader = Sax2.Reader()
		doc = reader.fromStream(filename)
	except: 
		error("Error while parsing xml")
	
	return doc

def gen_tunable_conf(doc, file):
	for node in doc.getElementsByTagName("tunable"):
		s = string.split(node.firstChild.data, "\n")
		for line in s:
			file.write("# %s\n" % line)
		tun_name = tun_val = None
        	for (name, value) in node.attributes.items():
			if name[1] == "name":
				tun_name = value.value
			elif name[1] == "dftval":
				tun_val = value.value

			if tun_name and tun_val:
	            		file.write("%s = %s\n\n" % (tun_name, tun_val))
				tun_name = tun_val = None

def gen_module_conf(doc, file):
	for node in doc.getElementsByTagName("module"):
		for desc in node.getElementsByTagName("summary"):
			s = string.split(desc.firstChild.data, "\n")
			for line in s:
				file.write("# %s\n" % line)	
			file.write("#\n")
			for (name, value) in node.attributes.items():
				if name[1] == "name":
					file.write("# %s\n\n" % value.value)

def gen_docs(doc, file):
	try:
		bodyfile = open("templates/header.html", "r")
		intfile = open("templates/interface.html", "r")
	except:
		error("Could not open templates")

	interface_buf = None
	interface_parameters = {}

	for node in doc.getElementsByTagName("module"):
		for interface in node.getElementsByTagName("interface"):
			interface_tpl = pyplate.Template(intfile.read())
			for i,v in interface.attributes.items():
				interface_name = v
			for desc in interface.getElementsByTagName("description"):
				interface_desc = desc.firstChild.data
			for desc in interface.getElementsByTagName("securitydesc"):
				if desc:
					interface_secdesc = desc.firstChild.data
				else:
					interface_secdesc = None
			
			for args in interface.getElementsByTagName("parameter"):
				paramdesc = args.firstChild.data
				for i,v in interface.attributes.items():
					arg = { "name" : v,
						"desc" : paramdesc }
					

def error(error):
        sys.stderr.write("%s exiting for: " % sys.argv[0])
        sys.stderr.write("%s\n" % error)
        sys.stderr.flush()
        sys.exit(1)

def usage():
	sys.stdout.write("%s [-tmd] -x <xmlfile>\n\n" % sys.argv[0])
	sys.stdout.write("Options:\n")
	sys.stdout.write("-t --tunables			--	write tunable config to <file>\n")
	sys.stdout.write("-m --modules <file>		--	write module config to <file>\n")
	sys.stdout.write("-d --docs <dir>		--	write interface documentation to <dir>\n")
	sys.stdout.write("-x --xml <file>		--	filename to read xml data from\n")


try:
	opts, args = getopt.getopt(sys.argv[1:], "t:m:d:x:", ["tunables","modules","docs","xml"])
except getopt.GetoptError:
	usage()
	sys.exit(1)

tunables = modules = docs = xmlfile = None

for opt, val in opts:
	if opt in ("-t", "--tunables"):
		tunables = val
	if opt in ("-m", "--modules"):
		modules = val
	if opt in ("-d", "--docs"):
		docs = val
	if opt in ("-x", "--xml"):
		xmlfile = val

if xmlfile == None:
	usage()
	sys.exit(1)

doc = read_policy_xml(xmlfile)
		
if tunables:
	try:
		conf = open(tunables, 'w')
	except:
		error("Could not open tunables file for writing")
	gen_tunable_conf(doc, conf)
	conf.close()


if modules:
	try:
		conf = open(modules, 'w')
	except:
		error("Could not open modules file for writing")
	gen_module_conf(doc, conf)
	conf.close()

if docs: 
	gen_docs(doc, sys.stdout)
