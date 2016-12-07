#!/usr/bin/python

#  Author: Joshua Brindle <jbrindle@tresys.com>
#	  Caleb Case <ccase@tresys.com>
#
# Copyright (C) 2005 - 2006 Tresys Technology, LLC
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
import string
from xml.dom.minidom import parse, parseString

#modules enabled and disabled values
MOD_BASE = "base"
MOD_ENABLED = "module"
MOD_DISABLED = "off"

#booleans enabled and disabled values
BOOL_ENABLED = "true"
BOOL_DISABLED = "false"

#tunables enabled and disabled values
TUN_ENABLED = "true"
TUN_DISABLED = "false"


def read_policy_xml(filename):
	"""
	Takes in XML from a file and returns a parsed file.
	"""

	try:
		xml_fh = open(filename)
	except:
		error("error opening " + filename)

	try:
		doc = parseString(xml_fh.read())
	except:
		xml_fh.close()
		error("Error while parsing xml")

	xml_fh.close()
	return doc

def gen_booleans_conf(doc, file_name, namevalue_list):
	"""
	Generates the booleans configuration file using the XML provided and the
	previous booleans configuration.
	"""

	for node in doc.getElementsByTagName("bool"):
		for desc in node.getElementsByTagName("desc"):
			bool_desc = format_txt_desc(desc)
		s = bool_desc.split("\n")
		file_name.write("#\n")
		for line in s:
			file_name.write("# %s\n" % line)

		bool_name = bool_val = None
		for (name, value) in node.attributes.items():
			if name == "name":
				bool_name = value
			elif name == "dftval":
				bool_val = value

			if [bool_name,BOOL_ENABLED] in namevalue_list:
				bool_val = BOOL_ENABLED
			elif [bool_name,BOOL_DISABLED] in namevalue_list:
				bool_val = BOOL_DISABLED

			if bool_name and bool_val:
				file_name.write("%s = %s\n\n" % (bool_name, bool_val))
				bool_name = bool_val = None

	# tunables are currently implemented as booleans
	for node in doc.getElementsByTagName("tunable"):
		for desc in node.getElementsByTagName("desc"):
			bool_desc = format_txt_desc(desc)
		s = bool_desc.split("\n")
		file_name.write("#\n")
		for line in s:
			file_name.write("# %s\n" % line)

		bool_name = bool_val = None
		for (name, value) in node.attributes.items():
			if name == "name":
				bool_name = value
			elif name == "dftval":
				bool_val = value

			if [bool_name,BOOL_ENABLED] in namevalue_list:
				bool_val = BOOL_ENABLED
			elif [bool_name,BOOL_DISABLED] in namevalue_list:
				bool_val = BOOL_DISABLED

			if bool_name and bool_val:
				file_name.write("%s = %s\n\n" % (bool_name, bool_val))
				bool_name = bool_val = None

def gen_module_conf(doc, file_name, namevalue_list):
	"""
	Generates the module configuration file using the XML provided and the
	previous module configuration.
	"""
	# If file exists, preserve settings and modify if needed.
	# Otherwise, create it.

	file_name.write("#\n# This file contains a listing of available modules.\n")
	file_name.write("# To prevent a module from  being used in policy\n")
	file_name.write("# creation, set the module name to \"%s\".\n#\n" % MOD_DISABLED)
	file_name.write("# For monolithic policies, modules set to \"%s\" and \"%s\"\n" % (MOD_BASE, MOD_ENABLED))
	file_name.write("# will be built into the policy.\n#\n")
	file_name.write("# For modular policies, modules set to \"%s\" will be\n" % MOD_BASE)
	file_name.write("# included in the base module.  \"%s\" will be compiled\n" % MOD_ENABLED)
	file_name.write("# as individual loadable modules.\n#\n\n")

	# For required in [True,False] is present so that the requiered modules
	# are at the top of the config file.
	for required in [True,False]:
		for node in doc.getElementsByTagName("module"):
			mod_req = False
			for req in node.getElementsByTagName("required"):
				if req.getAttribute("val") == "true":
					mod_req = True

			# Skip if we arnt working on the right set of modules.
			if mod_req and not required or not mod_req and required:
				continue


			mod_name = mod_layer = None

			mod_name = node.getAttribute("name")
			mod_layer = node.parentNode.getAttribute("name")

			if mod_name and mod_layer:
				file_name.write("# Layer: %s\n# Module: %s\n" % (mod_layer,mod_name))
				if required:
					file_name.write("# Required in base\n")
				file_name.write("#\n")

			for desc in node.getElementsByTagName("summary"):
				if not desc.parentNode == node:
					continue
				s = format_txt_desc(desc).split("\n")
				for line in s:
					file_name.write("# %s\n" % line)

				# If the module is set as disabled.
				if [mod_name, MOD_DISABLED] in namevalue_list:
					file_name.write("%s = %s\n\n" % (mod_name, MOD_DISABLED))
				# If the module is set as enabled.
				elif [mod_name, MOD_ENABLED] in namevalue_list:
					file_name.write("%s = %s\n\n" % (mod_name, MOD_ENABLED))
				# If the module is set as base.
				elif [mod_name, MOD_BASE] in namevalue_list:
					file_name.write("%s = %s\n\n" % (mod_name, MOD_BASE))
				# If the module is a new module.
				else:
					# Set the module to base if it is marked as required.
					if mod_req:
						file_name.write("%s = %s\n\n" % (mod_name, MOD_BASE))
					# Set the module to enabled if it is not required.
					else:
						file_name.write("%s = %s\n\n" % (mod_name, MOD_ENABLED))

def get_conf(conf):
	"""
	Returns a list of [name, value] pairs from a config file with the format
	name = value
	"""

	conf_lines = conf.readlines()

	namevalue_list = []
	for i in range(0,len(conf_lines)):
		line = conf_lines[i]
		if line.strip() != '' and line.strip()[0] != "#":
			namevalue = line.strip().split("=")
			if len(namevalue) != 2:
				warning("line %d: \"%s\" is not a valid line, skipping"\
					 % (i, line.strip()))
				continue

			namevalue[0] = namevalue[0].strip()
			if len(namevalue[0].split()) > 1:
				warning("line %d: \"%s\" is not a valid line, skipping"\
					 % (i, line.strip()))
				continue

			namevalue[1] = namevalue[1].strip()
			if len(namevalue[1].split()) > 1:
				warning("line %d: \"%s\" is not a valid line, skipping"\
					 % (i, line.strip()))
				continue

			namevalue_list.append(namevalue)

	return namevalue_list

def first_cmp_func(a):
	"""
	Return the first element to sort/compare on.
	"""

	return a[0]

def int_cmp_func(a):
	"""
	Return the interface name to sort/compare on.
	"""

	return a["interface_name"]

def temp_cmp_func(a):
	"""
	Return the template name to sort/compare on.
	"""

	return a["template_name"]

def tun_cmp_func(a):
	"""
	Return the tunable name to sort/compare on.
	"""

	return a["tun_name"]

def bool_cmp_func(a):
	"""
	Return the boolean name to sort/compare on.
	"""

	return a["bool_name"]

def gen_doc_menu(mod_layer, module_list):
	"""
	Generates the HTML document menu.
	"""

	menu = []
	for layer, value in module_list.items():
		cur_menu = (layer, [])
		menu.append(cur_menu)
		if layer != mod_layer and mod_layer != None:
			continue
		#we are in our layer so fill in the other modules or we want them all
		for mod, desc in value.items():
			cur_menu[1].append((mod, desc))

	menu.sort(key=first_cmp_func)
	for x in menu:
		x[1].sort(key=first_cmp_func)
	return menu

def format_html_desc(node):
	"""
	Formats a XML node into a HTML format.
	"""

	desc_buf = ''
	for desc in node.childNodes:
		if desc.nodeName == "#text":
			if desc.data is not '':
				if desc.parentNode.nodeName != "p":
					desc_buf += "<p>" + desc.data + "</p>"
				else:
					desc_buf += desc.data
		else:
			desc_buf += "<" + desc.nodeName + ">" \
				 + format_html_desc(desc) \
				 + "</" + desc.nodeName +">"

	return desc_buf

def format_txt_desc(node):
	"""
	Formats a XML node into a plain text format.
	"""

	desc_buf = ''
	for desc in node.childNodes:
		if desc.nodeName == "#text":
			desc_buf += desc.data + "\n"
		elif desc.nodeName == "p":
			desc_buf += desc.firstChild.data + "\n"
			for chld in desc.childNodes:
				if chld.nodeName == "ul":
					desc_buf += "\n"
					for li in chld.getElementsByTagName("li"):
						desc_buf += "\t -" + li.firstChild.data + "\n"

	return desc_buf.strip() + "\n"

def gen_docs(doc, working_dir, templatedir):
	"""
	Generates all the documentation.
	"""

	try:
		#get the template data ahead of time so we don't reopen them over and over
		bodyfile = open(templatedir + "/header.html", "r")
		bodydata = bodyfile.read()
		bodyfile.close()
		intfile = open(templatedir + "/interface.html", "r")
		intdata = intfile.read()
		intfile.close()
		templatefile = open(templatedir + "/template.html", "r")
		templatedata = templatefile.read()
		templatefile.close()
		tunfile = open(templatedir + "/tunable.html", "r")
		tundata = tunfile.read()
		tunfile.close()
		boolfile = open(templatedir + "/boolean.html", "r")
		booldata = boolfile.read()
		boolfile.close()
		menufile = open(templatedir + "/menu.html", "r")
		menudata = menufile.read()
		menufile.close()
		indexfile = open(templatedir + "/module_list.html","r")
		indexdata = indexfile.read()
		indexfile.close()
		modulefile = open(templatedir + "/module.html","r")
		moduledata = modulefile.read()
		modulefile.close()
		intlistfile = open(templatedir + "/int_list.html", "r")
		intlistdata = intlistfile.read()
		intlistfile.close()
		templistfile = open(templatedir + "/temp_list.html", "r")
		templistdata = templistfile.read()
		templistfile.close()
		tunlistfile = open(templatedir + "/tun_list.html", "r")
		tunlistdata = tunlistfile.read()
		tunlistfile.close()
		boollistfile = open(templatedir + "/bool_list.html", "r")
		boollistdata = boollistfile.read()
		boollistfile.close()
		gboollistfile = open(templatedir + "/global_bool_list.html", "r")
		gboollistdata = gboollistfile.read()
		gboollistfile.close()
		gtunlistfile = open(templatedir + "/global_tun_list.html", "r")
		gtunlistdata = gtunlistfile.read()
		gtunlistfile.close()
	except:
		error("Could not open templates")


	try:
		os.chdir(working_dir)
	except:
		error("Could not chdir to target directory")


#arg, i have to go through this dom tree ahead of time to build up the menus
	module_list = {}
	for node in doc.getElementsByTagName("module"):
		mod_name = mod_layer = interface_buf = ''

		mod_name = node.getAttribute("name")
		mod_layer = node.parentNode.getAttribute("name")

		for desc in node.getElementsByTagName("summary"):
			if desc.parentNode == node and desc:
				mod_summary = format_html_desc(desc)
		if not mod_layer in module_list:
			module_list[mod_layer] = {}

		module_list[mod_layer][mod_name] = mod_summary

#generate index pages
	main_content_buf = ''
	for mod_layer,modules in module_list.items():
		menu = gen_doc_menu(mod_layer, module_list)

		layer_summary = None
		for desc in doc.getElementsByTagName("summary"):
			if desc.parentNode.getAttribute("name") == mod_layer:
				layer_summary = format_html_desc(desc)

		menu_args = { "menulist" : menu,
			      "mod_layer" : mod_layer,
			      "layer_summary" : layer_summary }
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
#now generate the individual module pages

	all_interfaces = []
	all_templates = []
	all_tunables = []
	all_booleans = []
	for node in doc.getElementsByTagName("module"):
		mod_name = mod_layer = mod_desc = interface_buf = ''

		mod_name = node.getAttribute("name")
		mod_layer = node.parentNode.getAttribute("name")

		mod_req = None
		for req in node.getElementsByTagName("required"):
			if req.getAttribute("val") == "true":
				mod_req = True

		for desc in node.getElementsByTagName("summary"):
			if desc.parentNode == node:
				mod_summary = format_html_desc(desc)
		for desc in node.getElementsByTagName("desc"):
			if desc.parentNode == node:
				mod_desc = format_html_desc(desc)

		interfaces = []
		for interface in node.getElementsByTagName("interface"):
			interface_parameters = []
			interface_desc = interface_summary = None
			interface_name = interface.getAttribute("name")
			interface_line = interface.getAttribute("lineno")
			for desc in interface.childNodes:
				if desc.nodeName == "desc":
					interface_desc = format_html_desc(desc)
				elif desc.nodeName == "summary":
					interface_summary = format_html_desc(desc)

			for args in interface.getElementsByTagName("param"):
				for desc in args.getElementsByTagName("summary"):
					paramdesc = format_html_desc(desc)
				paramname = args.getAttribute("name")
				if args.getAttribute("optional") == "true":
					paramopt = "Yes"
				else:
					paramopt = "No"
				if args.getAttribute("unused") == "true":
					paramunused = "Yes"
				else:
					paramunused = "No"
				parameter = { "name" : paramname,
					      "desc" : paramdesc,
					      "optional" : paramopt,
					      "unused" : paramunused }
				interface_parameters.append(parameter)
			interfaces.append( { "interface_name" : interface_name,
					   "interface_summary" : interface_summary,
					   "interface_desc" : interface_desc,
					   "interface_parameters" : interface_parameters })
			#all_interfaces is for the main interface index with all interfaces
			all_interfaces.append( { "interface_name" : interface_name,
					   "interface_summary" : interface_summary,
					   "interface_desc" : interface_desc,
					   "interface_parameters" : interface_parameters,
					   "mod_name": mod_name,
					   "mod_layer" : mod_layer })
		interfaces.sort(key=int_cmp_func)
		interface_tpl = pyplate.Template(intdata)
		interface_buf = interface_tpl.execute_string({"interfaces" : interfaces})


# now generate individual template pages
		templates = []
		for template in node.getElementsByTagName("template"):
			template_parameters = []
			template_desc = template_summary = None
			template_name = template.getAttribute("name")
			template_line = template.getAttribute("lineno")
			for desc in template.childNodes:
				if desc.nodeName == "desc":
					template_desc = format_html_desc(desc)
				elif desc.nodeName == "summary":
					template_summary = format_html_desc(desc)

			for args in template.getElementsByTagName("param"):
				for desc in args.getElementsByTagName("summary"):
					paramdesc = format_html_desc(desc)
				paramname = args.getAttribute("name")
				if args.getAttribute("optional") == "true":
					paramopt = "Yes"
				else:
					paramopt = "No"
				if args.getAttribute("unused") == "true":
					paramunused = "Yes"
				else:
					paramunused = "No"
				parameter = { "name" : paramname,
					      "desc" : paramdesc,
					      "optional" : paramopt,
					      "unused": paramunused }
				template_parameters.append(parameter)
			templates.append( { "template_name" : template_name,
					   "template_summary" : template_summary,
					   "template_desc" : template_desc,
					   "template_parameters" : template_parameters })
			#all_templates is for the main interface index with all templates
			all_templates.append( { "template_name" : template_name,
					   "template_summary" : template_summary,
					   "template_desc" : template_desc,
					   "template_parameters" : template_parameters,
					   "mod_name": mod_name,
					   "mod_layer" : mod_layer })

		templates.sort(key=temp_cmp_func)
		template_tpl = pyplate.Template(templatedata)
		template_buf = template_tpl.execute_string({"templates" : templates})

		#generate 'boolean' pages
		booleans = []
		for boolean in node.getElementsByTagName("bool"):
			boolean_parameters = []
			boolean_desc = None
			boolean_name = boolean.getAttribute("name")
			boolean_dftval = boolean.getAttribute("dftval")
			for desc in boolean.childNodes:
				if desc.nodeName == "desc":
					boolean_desc = format_html_desc(desc)

			booleans.append({ "bool_name" : boolean_name,
					  "desc" : boolean_desc,
					  "def_val" : boolean_dftval })
			#all_booleans is for the main boolean index with all booleans
			all_booleans.append({ "bool_name" : boolean_name,
					   "desc" : boolean_desc,
					   "def_val" : boolean_dftval,
					   "mod_name": mod_name,
					   "mod_layer" : mod_layer })
		booleans.sort(key=bool_cmp_func)
		boolean_tpl = pyplate.Template(booldata)
		boolean_buf = boolean_tpl.execute_string({"booleans" : booleans})

		#generate 'tunable' pages
		tunables = []
		for tunable in node.getElementsByTagName("tunable"):
			tunable_parameters = []
			tunable_desc = None
			tunable_name = tunable.getAttribute("name")
			tunable_dftval = tunable.getAttribute("dftval")
			for desc in tunable.childNodes:
				if desc.nodeName == "desc":
					tunable_desc = format_html_desc(desc)

			tunables.append({ "tun_name" : tunable_name,
					  "desc" : tunable_desc,
					  "def_val" : tunable_dftval })
			#all_tunables is for the main tunable index with all tunables
			all_tunables.append({ "tun_name" : tunable_name,
					   "desc" : tunable_desc,
					   "def_val" : tunable_dftval,
					   "mod_name": mod_name,
					   "mod_layer" : mod_layer })
		tunables.sort(key=tun_cmp_func)
		tunable_tpl = pyplate.Template(tundata)
		tunable_buf = tunable_tpl.execute_string({"tunables" : tunables})


		menu = gen_doc_menu(mod_layer, module_list)

		menu_tpl = pyplate.Template(menudata)
		menu_buf = menu_tpl.execute_string({ "menulist" : menu })


		# pyplate's execute_string gives us a line of whitespace in
		# template_buf or interface_buf if there are no interfaces or
		# templates for this module. This is problematic because the
		# HTML templates use a conditional if on interface_buf or
		# template_buf being 'None' to decide if the "Template:" or
		# "Interface:" headers need to be printed in the module pages.
		# This detects if either of these are just whitespace, and sets
		# their values to 'None' so that when applying it to the
		# templates, they are properly recognized as not existing.
		if not interface_buf.strip():
			interface_buf = None
		if not template_buf.strip():
			template_buf = None
		if not tunable_buf.strip():
			tunable_buf = None
		if not boolean_buf.strip():
			boolean_buf = None

		module_args = { "mod_layer" : mod_layer,
			      "mod_name" : mod_name,
			      "mod_summary" : mod_summary,
			      "mod_desc" : mod_desc,
			      "mod_req" : mod_req,
			      "interfaces" : interface_buf,
			      "templates" : template_buf,
			      "tunables" : tunable_buf,
			      "booleans" : boolean_buf }

		module_tpl = pyplate.Template(moduledata)
		module_buf = module_tpl.execute_string(module_args)

		body_args = { "menu" : menu_buf,
			      "content" : module_buf }

		module_file = mod_layer + "_" + mod_name + ".html"
		module_fh = open(module_file, "w")
		body_tpl = pyplate.Template(bodydata)
		body_tpl.execute(module_fh, body_args)
		module_fh.close()


	menu = gen_doc_menu(None, module_list)
	menu_args = { "menulist" : menu,
		      "mod_layer" : None }
	menu_tpl = pyplate.Template(menudata)
	menu_buf = menu_tpl.execute_string(menu_args)

	#build the interface index
	all_interfaces.sort(key=int_cmp_func)
	interface_tpl = pyplate.Template(intlistdata)
	interface_buf = interface_tpl.execute_string({"interfaces" : all_interfaces})
	int_file = "interfaces.html"
	int_fh = open(int_file, "w")
	body_tpl = pyplate.Template(bodydata)

	body_args = { "menu" : menu_buf,
		      "content" : interface_buf }

	body_tpl.execute(int_fh, body_args)
	int_fh.close()


	#build the template index
	all_templates.sort(key=temp_cmp_func)
	template_tpl = pyplate.Template(templistdata)
	template_buf = template_tpl.execute_string({"templates" : all_templates})
	temp_file = "templates.html"
	temp_fh = open(temp_file, "w")
	body_tpl = pyplate.Template(bodydata)

	body_args = { "menu" : menu_buf,
		      "content" : template_buf }

	body_tpl.execute(temp_fh, body_args)
	temp_fh.close()


	#build the global tunable index
	global_tun = []
	for tunable in doc.getElementsByTagName("tunable"):
		if tunable.parentNode.nodeName == "policy":
			tunable_name = tunable.getAttribute("name")
			default_value = tunable.getAttribute("dftval")
			for desc in tunable.getElementsByTagName("desc"):
				description = format_html_desc(desc)
			global_tun.append( { "tun_name" : tunable_name,
						"def_val" : default_value,
						"desc" : description } )
	global_tun.sort(key=tun_cmp_func)
	global_tun_tpl = pyplate.Template(gtunlistdata)
	global_tun_buf = global_tun_tpl.execute_string({"tunables" : global_tun})
	global_tun_file = "global_tunables.html"
	global_tun_fh = open(global_tun_file, "w")
	body_tpl = pyplate.Template(bodydata)

	body_args = { "menu" : menu_buf,
		      "content" : global_tun_buf }

	body_tpl.execute(global_tun_fh, body_args)
	global_tun_fh.close()

	#build the tunable index
	all_tunables = all_tunables + global_tun
	all_tunables.sort(key=tun_cmp_func)
	tunable_tpl = pyplate.Template(tunlistdata)
	tunable_buf = tunable_tpl.execute_string({"tunables" : all_tunables})
	temp_file = "tunables.html"
	temp_fh = open(temp_file, "w")
	body_tpl = pyplate.Template(bodydata)

	body_args = { "menu" : menu_buf,
		      "content" : tunable_buf }

	body_tpl.execute(temp_fh, body_args)
	temp_fh.close()

	#build the global boolean index
	global_bool = []
	for boolean in doc.getElementsByTagName("bool"):
		if boolean.parentNode.nodeName == "policy":
			bool_name = boolean.getAttribute("name")
			default_value = boolean.getAttribute("dftval")
			for desc in boolean.getElementsByTagName("desc"):
				description = format_html_desc(desc)
			global_bool.append( { "bool_name" : bool_name,
						"def_val" : default_value,
						"desc" : description } )
	global_bool.sort(key=bool_cmp_func)
	global_bool_tpl = pyplate.Template(gboollistdata)
	global_bool_buf = global_bool_tpl.execute_string({"booleans" : global_bool})
	global_bool_file = "global_booleans.html"
	global_bool_fh = open(global_bool_file, "w")
	body_tpl = pyplate.Template(bodydata)

	body_args = { "menu" : menu_buf,
		      "content" : global_bool_buf }

	body_tpl.execute(global_bool_fh, body_args)
	global_bool_fh.close()

	#build the boolean index
	all_booleans = all_booleans + global_bool
	all_booleans.sort(key=bool_cmp_func)
	boolean_tpl = pyplate.Template(boollistdata)
	boolean_buf = boolean_tpl.execute_string({"booleans" : all_booleans})
	temp_file = "booleans.html"
	temp_fh = open(temp_file, "w")
	body_tpl = pyplate.Template(bodydata)

	body_args = { "menu" : menu_buf,
		      "content" : boolean_buf }

	body_tpl.execute(temp_fh, body_args)
	temp_fh.close()



def error(error):
	"""
	Print an error message and exit.
	"""

	sys.stderr.write("%s exiting for: " % sys.argv[0])
	sys.stderr.write("%s\n" % error)
	sys.stderr.flush()
	sys.exit(1)

def warning(warn):
	"""
	Print a warning message.
	"""

	sys.stderr.write("%s warning: " % sys.argv[0])
	sys.stderr.write("%s\n" % warn)

def usage():
	"""
	Describes the proper usage of this tool.
	"""

	sys.stdout.write("%s [-tmdT] -x <xmlfile>\n\n" % sys.argv[0])
	sys.stdout.write("Options:\n")
	sys.stdout.write("-b --booleans	<file>		--	write boolean config to <file>\n")
	sys.stdout.write("-m --modules <file>		--	write module config to <file>\n")
	sys.stdout.write("-d --docs <dir>		--	write interface documentation to <dir>\n")
	sys.stdout.write("-x --xml <file>		--	filename to read xml data from\n")
	sys.stdout.write("-T --templates <dir>		--	template directory for documents\n")


# MAIN PROGRAM
try:
	opts, args = getopt.getopt(sys.argv[1:], "b:m:d:x:T:", ["booleans","modules","docs","xml", "templates"])
except getopt.GetoptError:
	usage()
	sys.exit(1)

booleans = modules = docsdir = None
templatedir = "templates/"
xmlfile = "policy.xml"

for opt, val in opts:
	if opt in ("-b", "--booleans"):
		booleans = val
	if opt in ("-m", "--modules"):
		modules = val
	if opt in ("-d", "--docs"):
		docsdir = val
	if opt in ("-x", "--xml"):
		xmlfile = val
	if opt in ("-T", "--templates"):
		templatedir = val

doc = read_policy_xml(xmlfile)

if booleans:
	namevalue_list = []
	if os.path.exists(booleans):
		try:
			conf = open(booleans, 'r')
		except:
			error("Could not open booleans file for reading")

		namevalue_list = get_conf(conf)

		conf.close()

	try:
		conf = open(booleans, 'w')
	except:
		error("Could not open booleans file for writing")

	gen_booleans_conf(doc, conf, namevalue_list)
	conf.close()


if modules:
	namevalue_list = []
	if os.path.exists(modules):
		try:
			conf = open(modules, 'r')
		except:
			error("Could not open modules file for reading")
		namevalue_list = get_conf(conf)
		conf.close()

	try:
		conf = open(modules, 'w')
	except:
		error("Could not open modules file for writing")
	gen_module_conf(doc, conf, namevalue_list)
	conf.close()

if docsdir:
	gen_docs(doc, docsdir, templatedir)
