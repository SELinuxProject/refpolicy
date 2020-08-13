#!/usr/bin/env python3

#  Author(s): Donald Miner <dminer@tresys.com>
#	     Dave Sugar <dsugar@tresys.com>
#	     Brian Williams <bwilliams@tresys.com>
#	     Caleb Case <ccase@tresys.com>
#
# Copyright (C) 2005 - 2006 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

"""
	This script generates XML documentation information for layers specified
	by the user.
"""

import sys
import os
import re
import getopt

# GLOBALS

# Default values of command line arguments:
output_dir = ""

# Pre compiled regular expressions:

# Matches either an interface or a template declaration. Will give the tuple:
#	("interface" or "template", name)
# Some examples:
#	"interface(`kernel_read_system_state',`"
#	 -> ("interface", "kernel_read_system_state")
#	"template(`base_user_template',`"
#	 -> ("template", "base_user_template")
INTERFACE = re.compile(r"^\s*(interface|template)\(`(\w*)'")

# Matches either a gen_bool or a gen_tunable statement. Will give the tuple:
#	("tunable" or "bool", name, "true" or "false")
# Some examples:
#	"gen_bool(secure_mode, false)"
#	 -> ("bool", "secure_mode", "false")
#	"gen_tunable(allow_kerberos, false)"
#	 -> ("tunable", "allow_kerberos", "false")
BOOLEAN = re.compile(r"^\s*gen_(tunable|bool)\(\s*\`?\s*(\w*)\s*\'?\s*,\s*(true|false)\s*\)")
TEMPLATE_BOOLEAN = re.compile(r"^\s*gen_(tunable|bool)\(\s*\`?\s*([\w\$]*)\s*\'?\s*,\s*(true|false)\s*\)")

# Matches a XML comment in the policy, which is defined as any line starting
#  with two # and at least one character of white space. Will give the single
#  valued tuple:
#	("comment")
# Some Examples:
#	"## <summary>"
#	 -> ("<summary>")
#	"##		The domain allowed access.	"
#	 -> ("The domain allowed access.")
XML_COMMENT = re.compile(r"^\s*##\s+(.*?)\s*$")

# Matches a template call in the policy, which is defined as any line having
#  a function call like structure, being a string, followed by a set of
#  arguments between an opening and closing bracket. Regexp cannot deal with
#  unknown number of arguments, so we will split arguments in the code later on.
# Some examples:
#	"userdom_user_access_template(gpg, gpg_t)"
#	"zarafa_domain_template(gateway)"
TEMPLATE_CALL = re.compile(r"^\s*(\w*_template)\(\s*(\w*)\s*(?:,\s*(?:[^,)]*)\s*)*\)")

# FUNCTIONS
def getModuleXML(file_name):
	'''
	Returns the XML data for a module in a list, one line per list item.
	'''

	# Gather information.
	module_dir = os.path.dirname(file_name)
	module_name = os.path.basename(file_name)
	module_te = "%s/%s.te" % (module_dir, module_name)
	module_if = "%s/%s.if" % (module_dir, module_name)

	# Try to open the file, if it can't, just ignore it.
	try:
		module_file = open(module_if, "r")
		module_code = module_file.readlines()
		module_file.close()
	except OSError:
		warning("cannot open file %s for read, skipping" % file_name)
		return []

	module_buf = []

	# Infer the module name, which is the base of the file name.
	module_buf.append("<module name=\"%s\" filename=\"%s\">\n"
		% (os.path.splitext(os.path.split(file_name)[-1])[0], module_if))

	temp_buf = []
	interface = None

	# finding_header is a flag to denote whether we are still looking
	#  for the XML documentation at the head of the file.
	finding_header = True

	# Get rid of whitespace at top of file
	while(module_code and module_code[0].isspace()):
		module_code = module_code[1:]

	# Go line by line and figure out what to do with it.
	line_num = 0
	for line in module_code:
		line_num += 1
		if finding_header:
			# If there is a XML comment, add it to the temp buffer.
			comment = XML_COMMENT.match(line)
			if comment:
				temp_buf.append(comment.group(1) + "\n")
				continue

			# Once a line that is not an XML comment is reached,
			#  either put the XML out to module buffer as the
			#  module's documentation, or attribute it to an
			#  interface/template.
			elif temp_buf:
				finding_header = False
				interface = INTERFACE.match(line)
				if not interface:
					module_buf += temp_buf
					temp_buf = []
					continue

		# Skip over empty lines
		if line.isspace():
			continue

		# Grab a comment and add it to the temporary buffer, if it
		#  is there.
		comment = XML_COMMENT.match(line)
		if comment:
			temp_buf.append(comment.group(1) + "\n")
			continue

		# Grab the interface information. This is only not true when
		#  the interface is at the top of the file and there is no
		#  documentation for the module.
		if not interface:
			interface = INTERFACE.match(line)
		if interface:
			# Add the opening tag for the interface/template
			groups = interface.groups()
			module_buf.append("<%s name=\"%s\" lineno=\"%s\">\n" % (groups[0], groups[1], line_num))

			# Add all the comments attributed to this interface to
			#  the module buffer.
			if temp_buf:
				module_buf += temp_buf
				temp_buf = []

			# Add default summaries and parameters so that the
			#  DTD is happy.
			else:
				warning ("unable to find XML for %s %s()" % (groups[0], groups[1]))
				module_buf.append("<summary>\n")
				module_buf.append("Summary is missing!\n")
				module_buf.append("</summary>\n")
				module_buf.append("<param name=\"?\">\n")
				module_buf.append("<summary>\n")
				module_buf.append("Parameter descriptions are missing!\n")
				module_buf.append("</summary>\n")
				module_buf.append("</param>\n")

			# Close the interface/template tag.
			module_buf.append("</%s>\n" % interface.group(1))

			interface = None
			continue

		# If the line is a boolean/tunable definition, ignore it for now (these
		#  lines are processed later on) and dismiss the XML comment received
		#  thus far as it is otherwise attributed to an interface.
		tunable = TEMPLATE_BOOLEAN.match(line)
		if tunable:
			temp_buf = []
			continue

	# If the file just had a header, add the comments to the module buffer.
	if finding_header:
		module_buf += temp_buf
	# Otherwise there are some lingering XML comments at the bottom, warn
	#  the user.
	elif temp_buf:
		warning("orphan XML comments at bottom of file %s" % file_name)

	# Process the TE file if it exists.
	module_buf = module_buf + getTunableXML(module_te, "both")

	module_buf.append("</module>\n")

	return module_buf

def getTunableXML(file_name, kind):
	'''
	Return all the XML for the tunables/bools in the file specified.
	'''

	# Try to open the file, if it can't, just ignore it.
	try:
		tunable_file = open(file_name, "r")
		tunable_code = tunable_file.readlines()
		tunable_file.close()
	except OSError:
		warning("cannot open file %s for read, skipping" % file_name)
		return []

	tunable_buf = []
	temp_buf = []
	tunable_processed_code = []

	# We first go through the code and substitute template calls with the
	#  complete template content. This needs to happen iteratively, because
	#  a template can call another template. In order to ensure no cyclic
	#  template calls keep us busy, we max out at 9999 substitutions
	has_changed = True
	subst_threshold = 9999
	while (has_changed and (subst_threshold > 0)):
		has_changed = False
		for line in tunable_code:
			# Get the template call match
			template_call = TEMPLATE_CALL.match(line)
			# If we reach a template call, read in the template data
			#  from the template directory, but substitute all $1 with
			#  the second match, $2 with the third match, etc.
			if template_call:
				# Read template file based on template_call.group(1)
				try:
					template_file = open(templatedir + "/" + template_call.group(1) + ".iftemplate", "r")
					template_code = template_file.readlines()
					template_file.close()
				except OSError:
					warning("cannot open file %s for read, bailing out" % (templatedir + "/" + template_call.group(1) + ".iftemplate"))
					return []
				# Substitute content (i.e. $1 for argument 1, $2 for argument 2, etc.)
				template_split = re.findall(r"[\w\" {}]+", line.strip())
				for index, item in enumerate(template_code):
					for group in range(1, len(template_split)):
						template_code[index] = template_code[index].replace("$" + str(group), template_split[group].strip())
				# Now 'inject' the code in the tunable_code variable
				tunable_processed_code.extend(template_code)
				has_changed = True
				subst_threshold -= 1
			else:
				tunable_processed_code.append(line)
		# It is a bad practice to try and update lists while in a loop, so we
		# created an intermediate one and are now assigning it back
		tunable_code = tunable_processed_code
		tunable_processed_code = []
	# If subst_threshold is 0 or less we want to know
	if (subst_threshold <= 0):
		warning("Detected a possible loop in policy code and template usage")

	# Find tunables and booleans line by line and use the comments above
	# them.
	for line in tunable_code:
		# If it is an XML comment, add it to the buffer and go on.
		comment = XML_COMMENT.match(line)
		if comment:
			temp_buf.append(comment.group(1) + "\n")
			continue

		# Get the boolean/tunable data.
		boolean = BOOLEAN.match(line)

		# If we reach a boolean/tunable declaration, attribute all XML
		#  in the temp buffer to it and add XML to the tunable buffer.
		if boolean:
			# If there is a gen_bool in a tunable file or a
			# gen_tunable in a boolean file, error and exit.
			# Skip if both kinds are valid.
			if kind != "both":
				if boolean.group(1) != kind:
					error("%s in a %s file." % (boolean.group(1), kind))

			tunable_buf.append("<%s name=\"%s\" dftval=\"%s\">\n" % boolean.groups())
			tunable_buf += temp_buf
			temp_buf = []
			tunable_buf.append("</%s>\n" % boolean.group(1))

	# If there are XML comments at the end of the file, they aren't
	# attributed to anything. These are ignored.
	if len(temp_buf):
		warning("orphan XML comments at bottom of file %s" % file_name)


	# If the caller requested a the global_tunables and global_booleans to be
	# output to a file output them now
	if len(output_dir) > 0:
		xmlfile = os.path.split(file_name)[1] + ".xml"

		try:
			xml_outfile = open(output_dir + "/" + xmlfile, "w")
			for tunable_line in tunable_buf:
				xml_outfile.write (tunable_line)
			xml_outfile.close()
		except OSError:
			warning ("cannot write to file %s, skipping creation" % xmlfile)

	return tunable_buf

def usage():
	"""
	Displays a message describing the proper usage of this script.
	"""

	sys.stdout.write("usage: %s [-w] [-T <templatedir>] [-mtb] <file>\n\n" % sys.argv[0])
	sys.stdout.write("-w --warn\t\t\tshow warnings\n"+\
	"-m --module <file>\t\tname of module to process\n"+\
	"-t --tunable <file>\t\tname of global tunable file to process\n"+\
	"-b --boolean <file>\t\tname of global boolean file to process\n"+\
	"-T --templates <dir>\t\tname of template directory to use\n\n")

	sys.stdout.write("examples:\n")
	sys.stdout.write("> %s -w -T tmp/templates -m policy/modules/apache\n" % sys.argv[0])
	sys.stdout.write("> %s -t policy/global_tunables\n" % sys.argv[0])

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

# Defaults
warn = False
module = False
tunable = False
boolean = False
templatedir = ''

# Check that there are command line arguments.
if len(sys.argv) <= 1:
	usage()
	sys.exit(1)

# Parse command line args
try:
	opts, args = getopt.getopt(sys.argv[1:], 'whm:t:b:T:', ['warn', 'help', 'module=', 'tunable=', 'boolean=', 'templates='])
except getopt.GetoptError:
	usage()
	sys.exit(2)
for o, a in opts:
	if o in ('-w', '--warn'):
		warn = True
	elif o in ('-h', '--help'):
		usage()
		sys.exit(0)
	elif o in ('-m', '--module'):
		module = a
	elif o in ('-t', '--tunable'):
		tunable = a
	elif o in ('-b', '--boolean'):
		boolean = a
	elif o in ('-T', '--templates'):
		templatedir = a
	else:
		usage()
		sys.exit(2)

if module:
	sys.stdout.writelines(getModuleXML(module))
elif tunable:
	sys.stdout.writelines(getTunableXML(tunable, "tunable"))
elif boolean:
	sys.stdout.writelines(getTunableXML(boolean, "bool"))
else:
	usage()
	sys.exit(2)
