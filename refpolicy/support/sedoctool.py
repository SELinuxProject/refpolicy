#!/usr/bin/python

#  Author: Joshua Brindle <jbrindle@tresys.com>
#
# Copyright (C) 2003 - 2005 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

"""
	This module generates configuration files and documentation from the 
	SELinux reference policy XML format. 
"""

import sys
import getopt
import pyplate
import os
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
	file.write("#\n# This file contains a listing of available modules.\n")
	file.write("# To prevent a module from  being used in policy\n")
	file.write("# creation, uncomment the line with its name.\n#\n")
	for node in doc.getElementsByTagName("module"):
		mod_name = mod_layer = None
		for (name, value) in node.attributes.items():
			if name[1] == "name":
				mod_name = value.value
			if name[1] == "layer":
				mod_layer = value.value

			if mod_name and mod_layer:
				file.write("# Layer: %s\n# Module: %s\n#\n" % (mod_layer,mod_name))

		for desc in node.getElementsByTagName("summary"):
			s = string.split(desc.firstChild.data, "\n")
			for line in s:
				file.write("# %s\n" % line)	
			file.write("#\n#%s\n\n" % mod_name)

def gen_doc_menu(mod_layer, module_list):
	menu = {}
	for name, value in module_list.iteritems():
		if not menu.has_key(name):
			menu[name] = {}
		if name == mod_layer or mod_layer == None:
		#we are in our layer so fill in the other modules or we want them all
			for mod, desc in value.iteritems():
				menu[name][mod] = desc
	return menu

def gen_docs(doc, dir, templatedir):

	try:
		bodyfile = open(templatedir + "/header.html", "r")
		bodydata = bodyfile.read()
		bodyfile.close()
		intfile = open(templatedir + "/interface.html", "r")
		intdata = intfile.read()
		intfile.close()
		menufile = open(templatedir + "/menu.html", "r")
		menudata = menufile.read()
		menufile.close()
		indexfile = open(templatedir + "/module_list.html","r")
		indexdata = indexfile.read()
		indexfile.close()
		modulefile = open(templatedir + "/module.html","r")
		moduledata = modulefile.read()
		modulefile.close()
	except:
		error("Could not open templates")


	try:
		os.chdir(dir)
	except:
		error("Could now chdir to target directory")	


#arg, i have to go through this dom tree ahead of time to build up the menus
	module_list = {}
	for node in doc.getElementsByTagName("module"):
                mod_name = mod_layer = interface_buf = ''
		for (name, value) in node.attributes.items():
			if name[1] == "name":
				mod_name = value.value
			if name[1] == "layer":
				mod_layer = value.value
		for desc in node.getElementsByTagName("summary"):
			mod_summary = desc.firstChild.data
	
		if not module_list.has_key(mod_layer):
			module_list[mod_layer] = {}

		module_list[mod_layer][mod_name] = mod_summary

#generate index pages
	main_content_buf = ''
	for mod_layer,modules in module_list.iteritems():
		menu = gen_doc_menu(mod_layer, module_list)

		menu_args = { "menulist" : menu,
			      "mod_layer" : mod_layer }
		menu_tpl = pyplate.Template(menudata)
		menu_buf = menu_tpl.execute_string(menu_args)

		content_tpl = pyplate.Template(indexdata)
		content_buf = content_tpl.execute_string(menu_args)

		main_content_buf += content_buf

		body_args = { "menu" : menu_buf,
			      "content" : content_buf }
	
		index_file = mod_layer + ".html"
		index_fh = open(index_file, "w")
		body_tpl = pyplate.Template(bodydata)
		body_tpl.execute(index_fh, body_args)
		index_fh.close()	

	menu = gen_doc_menu(None, module_list)
	menu_args = { "menulist" : menu,
		      "mod_layer" : None }
	menu_tpl = pyplate.Template(menudata)
	menu_buf = menu_tpl.execute_string(menu_args)

	body_args = { "menu" : menu_buf,
		      "content" : main_content_buf }

	index_file = "index.html"
	index_fh = open(index_file, "w")
	body_tpl = pyplate.Template(bodydata)
	body_tpl.execute(index_fh, body_args)
	index_fh.close()
	

	for node in doc.getElementsByTagName("module"):
                mod_name = mod_layer = interface_buf = ''
		for (name, value) in node.attributes.items():
			if name[1] == "name":
				mod_name = value.value
			if name[1] == "layer":
				mod_layer = value.value
		for desc in node.getElementsByTagName("summary"):
			mod_summary = desc.firstChild.data
		for interface in node.getElementsByTagName("interface"):
			interface_parameters = []
			interface_secdesc = None
			interface_tpl = pyplate.Template(intdata)
			for i,v in interface.attributes.items():
				interface_name = v.value
			for desc in interface.getElementsByTagName("description"):
				interface_desc = desc.firstChild.data
			for desc in interface.getElementsByTagName("securitydesc"):
				if desc:
					interface_secdesc = desc.firstChild.data
			
			for args in interface.getElementsByTagName("parameter"):
				paramdesc = args.firstChild.data
				paramname = None
				paramopt = False
				for name,val in args.attributes.items():
					if name[1] == "name":
						paramname = val.value
					if name[1] == "optional":
						paramopt = val.value
				parameter = { "name" : paramname,
					      "desc" : paramdesc,
					      "optional" : paramopt }
				interface_parameters.append(parameter)
			interface_args = { "interface_name" : interface_name,
					   "interface_desc" : interface_desc,
					   "interface_parameters" : interface_parameters,
					   "interface_secdesc" : interface_secdesc }
			interface_buf += interface_tpl.execute_string(interface_args)
		
		menu = gen_doc_menu(mod_layer, module_list)

		menu_args = { "menulist" : menu }
		menu_tpl = pyplate.Template(menudata)
		menu_buf = menu_tpl.execute_string(menu_args)

		module_args = { "mod_layer" : mod_layer,
			      "mod_name" : mod_name,	
			      "mod_summary" : mod_summary,
			      "interfaces" : interface_buf }

		module_tpl = pyplate.Template(moduledata)
		module_buf = module_tpl.execute_string(module_args)

		body_args = { "menu" : menu_buf,
			      "content" : module_buf }
			  
		module_file = mod_layer + "_" + mod_name + ".html"
		module_fh = open(module_file, "w")
		body_tpl = pyplate.Template(bodydata)
		body_tpl.execute(module_fh, body_args)
		module_fh.close()

def error(error):
        sys.stderr.write("%s exiting for: " % sys.argv[0])
        sys.stderr.write("%s\n" % error)
        sys.stderr.flush()
	raise
        sys.exit(1)

def usage():
	sys.stdout.write("%s [-tmdT] -x <xmlfile>\n\n" % sys.argv[0])
	sys.stdout.write("Options:\n")
	sys.stdout.write("-t --tunables	<file>		--	write tunable config to <file>\n")
	sys.stdout.write("-m --modules <file>		--	write module config to <file>\n")
	sys.stdout.write("-d --docs <dir>		--	write interface documentation to <dir>\n")
	sys.stdout.write("-x --xml <file>		--	filename to read xml data from\n")
	sys.stdout.write("-T --templates <dir>		--	template directory for documents\n")


try:
	opts, args = getopt.getopt(sys.argv[1:], "t:m:d:x:T:", ["tunables","modules","docs","xml", "templates"])
except getopt.GetoptError:
	usage()
	sys.exit(1)

tunables = modules = docs = None
templatedir = "templates/"
xmlfile = "policy.xml"

for opt, val in opts:
	if opt in ("-t", "--tunables"):
		tunables = val
	if opt in ("-m", "--modules"):
		modules = val
	if opt in ("-d", "--docs"):
		docsdir = val
	if opt in ("-x", "--xml"):
		xmlfile = val
	if opt in ("-T", "--templates"):
		templatedir = val

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

if docsdir: 
	gen_docs(doc, docsdir, templatedir)
