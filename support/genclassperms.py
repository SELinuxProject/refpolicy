#!/usr/bin/python

# Author: Donald Miner <dminer@tresys.com>
#
# Copyright (C) 2005 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.


"""
	This script generates an object class perm definition file.
"""

import sys

USERSPACE_CLASS = "userspace"

class Class:
	"""
	This object stores an access vector class.
	"""

	def __init__(self, name, perms, common):
		# The name of the class.
		self.name = name

		# A list of permissions the class contains.
		self.perms = perms

		# True if the class is declared as common, False if not.
		self.common = common

def get_perms(name, av_db, common):
	"""
	Returns the list of permissions contained within an access vector
	class that is stored in the access vector database av_db.
	Returns an empty list if the object name is not found.
	Specifiy whether get_perms is to return the class or the
	common set of permissions with the boolean value 'common',
	which is important in the case of having duplicate names (such as
	class file and common file).
	"""

	# Traverse through the access vector database and try to find the
	#  object with the name passed.
	for obj in av_db:
		if obj.name == name and obj.common == common:
			return obj.perms

	return []

def get_av_db(file_name):
	"""
	Returns an access vector database generated from the file file_name.
	"""
	# This function takes a file, reads the data, parses it and returns
	#  a list of access vector classes.
	# Reading into av_data:
	#  The file specified will be read line by line. Each line will have
	#   its comments removed. Once comments are removed, each 'word' (text
	#   seperated by whitespace) and braces will be split up into seperate
	#   strings and appended to the av_data list, in the order they were
	#   read.
	# Parsing av_data:
	#  Parsing is done using a queue implementation of the av_data list.
	#   Each time a word is used, it is dequeued afterwards. Each loop in
	#   the while loop below will read in key words and dequeue expected
	#   words and values. At the end of each loop, a Class containing the
	#   name, permissions and whether it is a common or not will be appended
	#   to the database. Lots of errors are caught here, almost all checking
	#   if a token is expected but EOF is reached.
	# Now the list of Class objects is returned.

	av_file = open(file_name, "r")
	av_data = []
	# Read the file and strip out comments on the way.
	# At the end of the loop, av_data will contain a list of individual
	#  words. i.e. ['common', 'file', '{', ...]. All comments and whitespace
	#  will be gone.
	while True:
		av_line = av_file.readline()

		# If EOF has been reached:
		if not av_line:
			break

		# Check if there is a comment, and if there is, remove it.
		comment_index = av_line.find("#")
		if comment_index != -1:
			av_line = av_line[:comment_index]

		# Pad the braces with whitespace so that they are split into
		#  their own word. It doesn't matter if there will be extra
		#  white space, it'll get thrown away when the string is split.
		av_line.replace("{"," { ")
		av_line.replace("}"," } ")		

		# Split up the words on the line and add it to av_data.
		av_data += av_line.split()

	av_file.close()

	# Parsing the file:
	# The implementation of this parse is a queue. We use the list of words
	#  from av_data and use the front element, then dequeue it. Each
	#  loop of this while is a common or class declaration. Several
	#  expected tokens are parsed and dequeued out of av_data for each loop.
	# At the end of the loop, database will contain a list of Class objects.
	#  i.e. [Class('name',['perm1','perm2',...],'True'), ...]
	# Dequeue from the beginning of the list until av_data is empty:
	database = []
	while len(av_data) != 0:
		# At the beginning of every loop, the next word should be
		#  "common" or "class", meaning that each loop is a common
		#  or class declaration.
		# av_data = av_data[1:] removes the first element in the
		#  list, this is what is dequeueing data.

		# Figure out whether the next class will be a common or a class.
		if av_data[0] == "class":
			common = False
		elif av_data[0] == "common":
			common = True
		else:
			error("Unexpected token in file " + file_name + ": "\
				+ av_data[0] + ".")

		# Dequeue the "class" or "common" key word.
		av_data = av_data[1:]

		if len(av_data) == 0:
			error("Missing token in file " + file_name + ".")

		# Get and dequeue the name of the class or common.
		name = av_data[0]
		av_data = av_data[1:]

		# Retrieve the permissions inherited from a common set:
		perms = []
		# If the object we are working with is a class, since only
		#  classes inherit:
		if common == False:
			if len(av_data) == 0:
				error("Missing token in file " + file_name + ".")

			# If the class inherits from something else:
			if av_data[0] == "inherits":
				# Dequeue the "inherits" key word.
				av_data = av_data[1:]

				if len(av_data) == 0:
					error("Missing token in file "\
						+ file_name + " for " +\
						keyword + " " + name + ".")

				# av_data[0] is the name of the parent.
				# Append the permissions of the parent to
				#  the current class' permissions.
				perms += get_perms(av_data[0], database, True)

				# Dequeue the name of the parent.
				av_data = av_data[1:]

		# Retrieve the permissions defined with this set.
		if len(av_data) > 0 and av_data[0] == "{":
			# Dequeue the "{"
			av_data = av_data[1:]

			# Keep appending permissions until a close brace is
			#  found.
			while av_data[0] != "}":
				if av_data[0] == "{":
					error("Extra '{' in file " +\
						 file_name + ".")

				# Add the permission name.
				perms.append(av_data[0])

				# Dequeue the permission name.
				av_data = av_data[1:]

				if len(av_data) == 0:
					error("Missing token '}' in file "\
						+ file_name + ".")

			# Dequeue the "}"
			av_data = av_data[1:]

		# Add the new access vector class to the database.
		database.append(Class(name, perms, common))

	return database

def get_sc_db(file_name):
	"""
	Returns a security class database generated from the file file_name.
	"""

	# Read the file then close it.
	sc_file = open(file_name)
	sc_data = sc_file.readlines()
	sc_file.close()

	# For each line in the security classes file, add the name of the class
	#  and whether it is a userspace class or not to the security class
	#  database.
	database = []
	for line in sc_data:
		line = line.lstrip()
		# If the line is empty or the entire line is a comment, skip.
		if line == "" or line[0] == "#":
			continue

		# Check if the comment to the right of the permission matches
		#  USERSPACE_CLASS.
		comment_index = line.find("#")
		if comment_index != -1 and line[comment_index+1:].strip() == USERSPACE_CLASS:
			userspace = True
		else:
			userspace = False

		# All lines should be in the format "class NAME", meaning
		#  it should have two tokens and the first token should be
		#  "class".
		split_line = line.split()
		if len(split_line) < 2 or split_line[0] != "class":
			error("Wrong syntax: " + line)

		# Add the class's name (split_line[1]) and whether it is a
		#  userspace class or not to the database.
		# This is appending a tuple of (NAME,USERSPACE), where NAME is
		#  the name of the security class and USERSPACE is True if
		#  if it has "# USERSPACE_CLASS" on the end of the line, False
		#  if not.
		database.append((split_line[1], userspace))

	return database

def gen_class_perms(av_db, sc_db):
	"""
	Generates a class permissions document and returns it.
	"""

	# Define class template:
	class_perms_line = "define(`all_%s_perms',`{ %s}')\n"

	# Generate the defines for the individual class permissions.
	class_perms = ""
	for obj in av_db:
		# Don't output commons
		if obj.common == True:
			continue

		# Get the list of permissions from the specified class.
		perms = get_perms(obj.name, av_db, False)

		# Merge all the permissions into one string with one space
		#  padding.
		perm_str = ""
		for perm in perms:
			perm_str += perm + " "

		# Add the line to the class_perms
		class_perms += class_perms_line % (obj.name, perm_str)
	class_perms += "\n"

	# Generate the kernel_class_perms and userspace_class_perms sets.
	class_line = "\tclass %s all_%s_perms;\n"
	kernel_class_perms = "define(`all_kernel_class_perms',`\n"
	userspace_class_perms = "define(`all_userspace_class_perms',`\n"
	# For each (NAME,USERSPACE) tuple, add the class to the appropriate
	# class permission set.
	for name, userspace in sc_db:
		if userspace:
			userspace_class_perms += class_line % (name, name)
		else:
			kernel_class_perms += class_line % (name, name)
	kernel_class_perms += "')\n\n"
	userspace_class_perms += "')\n"

	# Throw all the strings together and return the string.
	return class_perms + kernel_class_perms + userspace_class_perms

def error(error):
	"""
	Print an error message and exit.
	"""

	sys.stderr.write("%s exiting for: " % sys.argv[0])
	sys.stderr.write("%s\n" % error)
	sys.stderr.flush()
	sys.exit(1)

# MAIN PROGRAM
app_name = sys.argv[0]

if len(sys.argv) != 3:
	error("Incorrect input.\nUsage: " + sys.argv[0] + " access_vectors security_classes" )

# argv[1] is the access vector file.
av_file = sys.argv[1]

# argv[2] is the security class file.
sc_file = sys.argv[2]

# Output the class permissions document.
sys.stdout.write(gen_class_perms(get_av_db(av_file), get_sc_db(sc_file)))
