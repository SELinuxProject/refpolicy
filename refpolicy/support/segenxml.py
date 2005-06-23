#!/usr/bin/python

#  Author: Donald Miner <dminer@tresys.com>
#
# Copyright (C) 2003 - 2005 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

"""
	This script generates XML documentation information for layers specified
	by the user.
"""

import sys
import os
import glob


# GLOBALS
class dec_style:
	'''
	"Declaration Style"
	Specifies the syntax of a declaration. Intended to be used with
	getParams().
	'''

	# Example of a line: foo(bar,one,two);
	# A style that would fit this: dec_style("foo(",3,",",");")
	#  "foo(" - the opening of it, ends at the begining of the first param.
	#  3 - the number of parameters.
	#  "," - the delimeter to parse apart parameters.
	#  ");" - the end of the declaration statement.

	def __init__(self,open_str,params,delim,close_str):
		self.open_str = open_str
		self.params = params
		self.delim = delim
		self.close_str = close_str


INTERFACE = dec_style("interface(`",1,None,"'")
TUNABLE = dec_style("gen_tunable(",2,",",")")
# boolean FIXME: may have to change in the future.
BOOLEAN = dec_style("gen_bool(",2,",",")")


# Default values of command line arguments.
directory = "./"
warn = False
meta = "metadata"
layers = []
tunable_files = []



# FUNCTIONS
def getFileBase(file_name):
	'''
	Return the file base, the file name without the extension.
	'''

	# Start from the end of the string and stop when the first '.' is
	# encountered, ignores hidden files denoted by a leading ','.
	for i in range(1,len(file_name)-1):
		if file_name[-i] == '.':
			return os.path.basename(file_name[:-i])

	return os.path.basename(file_name)

def getXMLComment(line):
	'''
	Returns the XML comment, (removes "## " from the front of the line).
	Returns False if the line is not an XML comment.
	'''

	for i in range(0,len(line)-1):
		# Check if the first 3 characters are "## "
		if line[i:i+3] in ("## ", "##\t"):
			# The chars before '#' in the line must be whitespace.
			if i > 0 and not line[0:i-1].isspace():
				return False
			else:
				return line[i+3:]

	# No XML comment.
	return False	

def getParams(line, style):
	'''
	Returns a list of items, containing the values of each parameter.
	'''

	# Clean out whitespace.
	temp_line = line.strip()

	# Check to see if the string begins with the specified opening
	# string specified by style.
	if temp_line[0:len(style.open_str)] == style.open_str:
		temp_line = temp_line[len(style.open_str):].strip()
	else:
		return False

	# If there is a delimeter.
	if style.delim:
		temp_line = temp_line.split(style.delim)
	else:
		temp_line = [temp_line]

	# Only interested in a sertain number of tokens, specified by style.
	temp_line = temp_line[:style.params]

	# Remove the end of the declaration, specified by style.
	end = temp_line[len(temp_line)-1].find(style.close_str)
	if end == -1:
		warning("line \"%s\" may be syntactically incorrect"\
			% line.strip())
		return False

	temp_line[len(temp_line)-1] = temp_line[len(temp_line)-1][:end]

	# Remove whitespace
	for i in range(0,len(temp_line)-1):
		temp_line[i] = temp_line[i].strip()

	return temp_line

def getModuleXML(file_name):
	'''
	Returns the XML data for a module in a list, one line per list item.
	'''

	# Try to open the file, if it cant, just ignore it.
	try:
		module_file = open(file_name, "r")
		module_code = module_file.readlines()
		module_file.close()
	except:
		warning("cannot open file %s for read, skipping" % file_name)
		return []

	module_buf = []

	# Infer the module name.
	module_buf.append("<module name=\"%s\">\n" % getFileBase(file_name))

	temp_buf = []

	# Phases:	find header - looking for the header of the file.
	#		get header - get the header comments and stop when first
	#			     whitespace is encountered.
	#		find interface - looking for interfaces to get info for.
	phase = "find header"

	# Go line by line and figure out what to do with it.
	for line in module_code:
		# In this phase, whitespace and stray code is ignored at the
		# top fo the file.
		if phase == "find header":
			if line.isspace():
				continue
			# Once a comment is encountered, start trying to get the
			# header documentation.
			elif getXMLComment(line):
				phase = "get header"
			# If an interface is found, there is no header, and no
			# documentation for the interface.
			elif getParams(line,INTERFACE):
				phase = "find interface"

		# In this phase, XML comments are being retrieved for the file.
		if phase == "get header":
			if getXMLComment(line):
				temp_buf.append(getXMLComment(line))
				continue
			# If the line is whitespace, the file header is over,
			# continue on to find interfaces.
			elif line.isspace():
				module_buf += temp_buf
				temp_buf = []
				phase = "find interface"
				continue
			# Oops! The comments we have been getting weren't part
			# of the header so attribute them to an interface
			# instead.
			elif getParams(line,INTERFACE):
				phase = "find interface"

		# In this phase, XML comments are being attributed
		if phase == "find interface":
			if getXMLComment(line):
				temp_buf.append(getXMLComment(line))
				continue
			# If the line is the declaration of a interface,
			# infer the interface name and add all the comments
			# to the main buffer.
			elif getParams(line,INTERFACE):
				module_buf.append("<interface name=\"%s\">\n"\
					% getParams(line,INTERFACE)[0])
				module_buf += temp_buf
				temp_buf = []
				module_buf.append("</interface>\n")
				continue

	# If there are XML comments at the end of the file, they arn't
	# attributed to anything. These are ignored.
	if len(temp_buf):
		warning("orphan XML comments at bottom of file %s" % file_name)
		
	module_buf.append("</module>\n")

	return module_buf

def getLayerXML(directory):
	'''
	Returns the XML documentation for a layer.
	'''

	layer_buf = []

	# Infer the layer name from the directory name.
	layer_buf.append("<layer name=\"%s\">\n" % os.path.basename(directory))

	# Try to open the metadata file for this directory and if it exists,
	# append the contents to the buffer.
	try:
		layer_meta = open(directory+"/"+meta, "r")
		layer_buf += layer_meta.readlines()
		layer_meta.close()
	except:
		warning("cannot open file %s for read, assuming no data"\
			% meta)

	# For each module file in the layer, add its XML.
	for module in glob.glob("%s/*.if" % directory):
		layer_buf += getModuleXML(module)

	layer_buf.append("</layer>\n")

	return layer_buf

def getTunableXML(file_name):
	'''
	Return all the XML for the tunables in the file specified.
	'''

	# Try to open the file, if it cant, just ignore it.
	try:
		tunable_file = open(file_name, "r")
		tunable_code = tunable_file.readlines()
		tunable_file.close()
	except:
		warning("cannot open file %s for read, skipping" % file_name)
		return []

	tunable_buf = []
	temp_buf = []

	# Find tunables and booleans line by line and use the comments above
	# them.
	for line in tunable_code:
		# If it is an XML comment, add it to the buffer and go on.
		if getXMLComment(line):
			temp_buf.append(getXMLComment(line))
			continue

		# Get the parameters of a TUNABLE style line.
		params = getParams(line,TUNABLE)

		# If the line is not a TUNABLE style declaration, try BOOLEAN.
		if not params:
			params = getParams(line,BOOLEAN)

		# If the line is one of the two styles above, add a tunable tag
		# and give it the data from the temprorary buffer.
		if params:
			tunable_buf.append\
				("<tunable name=\"%s\" dftval=\"%s\">\n"
				% (params[0], params[1]))
			tunable_buf += temp_buf
			temp_buf = []
			tunable_buf.append("</tunable>\n")

	# If there are XML comments at the end of the file, they arn't
	# attributed to anything. These are ignored.
	if len(temp_buf):
		warning("orphan XML comments at bottom of file %s" % file_name)

	return tunable_buf

def getPolicyXML(directory):
	'''
	Return the compelete reference policy XML documentation through a list,
	one line per item.
	'''

	# Keep track of original path so that it will change back at the end.
	old_dir = os.path.abspath(os.path.curdir)

	# Attempt to change directory into the policy directory. If it doesn't
	# exist just return an empty documentation.
	try:
		os.chdir(directory)
	except:
		warning("cannot change directory to %s, ignoring"\
			% directory)
		return []

	policy_buf = []
	policy_buf.append("<policy>\n")

	# Add to the XML each layer specified by the user.
	for layer in layers:
		policy_buf += getLayerXML(layer)

	# Add to the XML each tunable specified by the user.
	for tunable_file in tunable_files:
		policy_buf += getTunableXML(tunable_file)


	policy_buf.append("</policy>\n")

	# Return to old directory.
	try:
		os.chdir(old_dir)
	except:
		error("cannot change directory to %s" % old_dir)

	return policy_buf

def usage():
	"""
	Displays a message describing the proper usage of this script.
	"""

	sys.stdout.write("usage: %s [-w] [-d directory] [-m file] "\
		% sys.argv[0])

	sys.stdout.write("layerdirectory [layerdirectory...]\n\n")

	sys.stdout.write("Options:\n")

	sys.stdout.write("-w --warn		--	"+\
				"show warnings\n")

	sys.stdout.write("-m --meta <file>	--	"+\
				"the filename of the metadata in each layer\n")

	sys.stdout.write("-d --directory <dir>	--	"+\
				"directory where the layers are\n")

	sys.stdout.write("-t --tunable <file>	--	"+\
				"A file containing tunable declarations\n")

def warning(description):
	'''
	Warns the user of a non-critical error.
	'''

	if warn:
		sys.stderr.write("%s: " % sys.argv[0] )
		sys.stderr.write("warning: " + description + "\n")

def error(description):
	'''
	Describes an error and exists the program.
	'''

	sys.stderr.write("%s: " % sys.argv[0] )
        sys.stderr.write("error: " + description + "\n")
        sys.stderr.flush()
        sys.exit(1)



# MAIN PROGRAM
# Check that there are command line arguments.
if len(sys.argv) <= 1:
	usage()
	sys.exit(1)


# Parse the command line arguments
for i in range(1, len(sys.argv)):
	if sys.argv[i-1] in ("-d", "--directory", "-m", "--meta",\
					"-t", "--tunable"):
		continue
	elif sys.argv[i] in ("-w", "--warn"):
		warn = True
	elif sys.argv[i] in ("-d", "--directory"):
		if i < len(sys.argv)-1:
			directory = sys.argv[i+1]
		else:
			usage()
	elif sys.argv[i] in ("-m", "--meta"):
		if i < len(sys.argv)-1:
			meta = sys.argv[i+1]
		else:
			usage()
	elif sys.argv[i] in ("-t", "--tunable"):
		if i < len(sys.argv)-1:
			tunable_files.append(sys.argv[i+1])
		else:
			usage()
	else:
		layers.append(sys.argv[i])


# Generate the XML and output it to a file
lines = getPolicyXML(directory)
for s in lines:
	sys.stdout.write(s)
