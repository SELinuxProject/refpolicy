#!/usr/bin/env python3
# Copyright (C) 2004 Tresys Technology, LLC
# see file 'COPYING' for use and warranty information
#
# genhomedircon - this script is used to generate file context
# configuration entries for user home directories based on their
# default roles and is run when building the policy. Specifically, we
# replace HOME_ROOT, HOME_DIR, and ROLE macros in .fc files with
# generic and user-specific values.
#
# Based off original script by Dan Walsh, <dwalsh@redhat.com>
#
# ASSUMPTIONS:
#
# The file CONTEXTDIR/files/homedir_template exists.  This file is used to
# set up the home directory context for each real user.
#
# If a user has more than one role in CONTEXTDIR/local.users, genhomedircon uses
#  the first role in the list.
#
# If a user is not listed in CONTEXTDIR/local.users, he will default to user_u, role user
#
# "Real" users (as opposed to system users) are those whose UID is greater than
#  or equal STARTING_UID (usually 500) and whose login is not a member of
#  EXCLUDE_LOGINS.  Users who are explicitly defined in CONTEXTDIR/local.users
#  are always "real" (including root, in the default configuration).
#
#
# Old ASSUMPTIONS:
#
# If a user has more than one role in FILECONTEXTDIR/users, genhomedircon uses
#  the first role in the list.
#
# If a user is not listed in FILECONTEXTDIR/users, genhomedircon assumes that
#  the user's home dir will be found in one of the HOME_ROOTs.
#
# "Real" users (as opposed to system users) are those whose UID is greater than
#  or equal STARTING_UID (usually 500) and whose login is not a member of
#  EXCLUDE_LOGINS.  Users who are explicitly defined in FILECONTEXTDIR/users
#  are always "real" (including root, in the default configuration).
#

import sys, pwd, getopt, re, os
from subprocess import getstatusoutput

EXCLUDE_LOGINS=["/sbin/nologin", "/usr/sbin/nologin", "/bin/false", "/usr/bin/false"]


def getStartingUID():
	starting_uid = 99999
	rc=getstatusoutput("grep -h '^UID_MIN' /etc/login.defs")
	if rc[0] == 0:
		uid_min = re.sub("^UID_MIN[^0-9]*", "", rc[1])
		#strip any comment from the end of the line
		uid_min = uid_min.split("#")[0]
		uid_min = uid_min.strip()
		if int(uid_min) < starting_uid:
			starting_uid = int(uid_min)
	rc=getstatusoutput("grep -h '^LU_UIDNUMBER' /etc/libuser.conf")
	if rc[0] == 0:
		lu_uidnumber = re.sub("^LU_UIDNUMBER[^0-9]*", "", rc[1])
		#strip any comment from the end of the line
		lu_uidnumber = re.sub("[ \t].*", "", lu_uidnumber)
		lu_uidnumber = lu_uidnumber.split("#")[0]
		lu_uidnumber = lu_uidnumber.strip()
		if int(lu_uidnumber) < starting_uid:
			starting_uid = int(lu_uidnumber)
	if starting_uid == 99999:
		starting_uid = 500
	return starting_uid

def getDefaultHomeDir():
	ret = []
	if os.path.isfile('/etc/default/useradd'):
		rc=getstatusoutput("grep -h '^HOME' /etc/default/useradd")
		if rc[0] == 0:
			homedir = rc[1].split("=")[1]
			homedir = homedir.split("#")[0]
			homedir = homedir.strip()
			if not homedir in ret:
				ret.append(homedir)
		else:
			#rc[0] == 1 means the file was there, we read it, but the grep didn't match
			if rc[0] != 1:
				sys.stderr.write("(%d): %s\n" % (rc[0], rc[1]))
				sys.stderr.write("You do not have access to /etc/default/useradd HOME=\n")
				sys.stderr.flush()
	if os.path.isfile('/etc/libuser.conf'):
		rc=getstatusoutput("grep -h '^LU_HOMEDIRECTORY' /etc/libuser.conf")
		if rc[0] == 0:
			homedir = rc[1].split("=")[1]
			homedir = homedir.split("#")[0]
			homedir = homedir.strip()
			if not homedir in ret:
				ret.append(homedir)
		else:
			#rc[0] == 1 means the file was there, we read it, but the grep didn't match
			if rc[0] != 1:
				sys.stderr.write("(%d): %s\n" % (rc[0], rc[1]))
				sys.stderr.write("You do not have access to /etc/libuser.conf LU_HOMEDIRECTORY=\n")
				sys.stderr.flush()
	if ret == []:
		ret.append("/home")
	return ret

def getSELinuxType(directory):
	rc=getstatusoutput("grep ^SELINUXTYPE= %s/config" % directory)
	if rc[0]==0:
		return rc[1].split("=")[-1].strip()
	return "targeted"

def usage(error = ""):
	if error != "":
		sys.stderr.write("%s\n" % error)
	sys.stderr.write("Usage: %s [ -d selinuxdir ] [-n | --nopasswd] [-t selinuxtype ]\n" % sys.argv[0])
	sys.stderr.flush()
	sys.exit(1)

def warning(warning = ""):
	sys.stderr.write("%s\n" % warning)
	sys.stderr.flush()

def errorExit(error):
	sys.stderr.write("%s exiting for: " % sys.argv[0])
	sys.stderr.write("%s\n" % error)
	sys.stderr.flush()
	sys.exit(1)

class selinuxConfig:
	def __init__(self, selinuxdir="/etc/selinux", setype="targeted", usepwd=1):
		self.setype=setype
		self.selinuxdir=selinuxdir +"/"
		self.contextdir="/contexts"
		self.filecontextdir=self.contextdir+"/files"
		self.usepwd=usepwd

	def getFileContextDir(self):
		return self.selinuxdir+self.setype+self.filecontextdir

	def getFileContextFile(self):
		return self.getFileContextDir()+"/file_contexts"

	def getHomeDirTemplate(self):
		return self.getFileContextDir()+"/homedir_template"

	def getHomeRootContext(self, homedir):
		rc=getstatusoutput("grep HOME_ROOT  %s | sed -e \"s|^HOME_ROOT|%s|\"" % ( self.getHomeDirTemplate(), homedir))
		if rc[0] != 0:
			errorExit("sed error (" + str(rc[0]) + "): " + rc[1])
		return rc[1]+"\n"

	def getUsersFile(self):
		return self.selinuxdir+self.setype+"/users/local.users"

	def getSystemUsersFile(self):
		return self.selinuxdir+self.setype+"/users/system.users"

	def heading(self):
		ret = "\n#\n#\n# User-specific file contexts, generated via %s\n" % sys.argv[0]
		ret += "# edit %s to change file_context\n#\n#\n" % self.getUsersFile()
		return ret

	def getUsers(self):
		users=""
		rc = getstatusoutput('grep "^user" %s' % self.getSystemUsersFile())
		if rc[0] == 0:
			users+=rc[1]+"\n"
		rc = getstatusoutput("grep ^user %s" % self.getUsersFile())
		if rc[0] == 0:
			users+=rc[1]
		udict = {}
		if users != "":
			ulist = users.split("\n")
			for u in ulist:
				user = u.split()
				try:
					if len(user)==0 or user[1] == "user_u" or user[1] == "system_u":
						continue
					# !!! chooses first role in the list to use in the file context !!!
					role = user[3]
					if role == "{":
						role = user[4]
					role = role.split("_r")[0]
					pwdentry = pwd.getpwnam(user[1])
					home = pwdentry[5]
					if home == "/":
						continue
					prefs = {}
					prefs["role"] = role
					prefs["home"] = home
					prefs["name"] = pwdentry[0]
					prefs["uid"] = pwdentry[2]
					udict[user[1]] = prefs
				except KeyError:
					sys.stderr.write("The user \"%s\" is not present in the passwd file, skipping...\n" % user[1])
		return udict

	def getHomeDirContext(self, seuser, home, role, username, userid):
		ret = "\n\n#\n# Context for user %s\n#\n\n" % seuser
		rc = getstatusoutput("grep -E '^HOME_DIR|%%{USERID}|%%{USERNAME}' %s | sed"
			" -e 's|HOME_DIR|%s|'"
			" -e 's|ROLE|%s|'"
			" -e 's|system_u|%s|'"
			" -e 's|%%{USERID}|%s|'"
			" -e 's|%%{USERNAME}|%s|'"
			% (self.getHomeDirTemplate(), home, role, seuser, userid, username))
		if rc[0] != 0:
			errorExit("sed error (" + str(rc[0]) + "): " + rc[1])
		return ret + rc[1] + "\n"

	def genHomeDirContext(self):
		users = self.getUsers()
		ret=""
		# Fill in HOME and ROLE for users that are defined
		for u in users:
			ret += self.getHomeDirContext (u, users[u]["home"], users[u]["role"], users[u]["name"], users[u]["uid"])
		return ret+"\n"

	def checkExists(self, home):
		if getstatusoutput("grep -E '^%s[^[:alnum:]_-]' %s" % (home, self.getFileContextFile()))[0] == 0:
			return 0
		#this works by grepping the file_contexts for
		# 1. ^/ makes sure this is not a comment
		# 2. prints only the regex in the first column first cut on \t then on space
		rc=getstatusoutput("grep \"^/\" %s | cut -f 1 | cut -f 1 -d \" \" " %  self.getFileContextFile() )
		if rc[0] == 0:
			prefix_regex = rc[1].split("\n")
		else:
			sys.stderr.write("%s\n" % rc[1])
			sys.stderr.write("You do not have access to grep/cut/the file contexts\n")
			sys.stderr.flush()
		exists=1
		for regex in prefix_regex:
			#match a trailing (/*)? which is actually a bug in rpc_pipefs
			regex = re.sub(r"\(/\*\)\?$", "", regex)
			#match a trailing .+
			regex = re.sub(r"\.+$", "", regex)
			#match a trailing .*
			regex = re.sub(r"\.\*$", "", regex)
			#strip a (/.*)? which matches anything trailing to a /*$ which matches trailing /'s
			regex = re.sub(r"\(\/\.\*\)\?", "", regex)
			regex = regex + "/*$"
			if re.search(regex, home, 0):
				exists = 0
				break
		if exists == 1:
			return 1
		return 0


	def getHomeDirs(self):
		homedirs = []
		homedirs = homedirs + getDefaultHomeDir()
		starting_uid=getStartingUID()
		if self.usepwd==0:
			return homedirs
		ulist = pwd.getpwall()
		for u in ulist:
			if u[2] >= starting_uid and \
					not u[6] in EXCLUDE_LOGINS and \
					u[5] != "/" and \
					u[5].count("/") > 1:
				homedir = u[5][:u[5].rfind("/")]
				if not homedir in homedirs:
					if self.checkExists(homedir)==0:
						warning("%s is already defined in %s,\n%s will not create a new context." % (homedir, self.getFileContextFile(), sys.argv[0]))
					else:
						homedirs.append(homedir)

		homedirs.sort()
		return homedirs

	def genoutput(self):
		ret= self.heading()
		for h in self.getHomeDirs():
			ret += self.getHomeDirContext ("user_u" , h+'/[^/]+', "user", "[^/]+", "[0-9]+")
			ret += self.getHomeRootContext(h)
		ret += self.genHomeDirContext()
		return ret

	def write(self):
		try:
			fd = open(self.getFileContextDir()+"/file_contexts.homedirs", "w")
			fd.write(self.genoutput())
			fd.close()
		except IOError as error:
			sys.stderr.write("%s: %s\n" % ( sys.argv[0], error ))



#
# This script will generate home dir file context
# based off the homedir_template file, entries in the password file, and
#
try:
	usepwd=1
	directory="/etc/selinux"
	setype=None
	gopts, cmds = getopt.getopt(sys.argv[1:], 'nd:t:', ['help',
						'type=',
						'nopasswd',
						'dir='])
	for o,a in gopts:
		if o in ('--type', '-t'):
			setype=a
		if o in ('--nopasswd', '-n'):
			usepwd=0
		if o in ('--dir', '-d'):
			directory=a
		if o == '--help':
			usage()


	if setype is None:
		setype=getSELinuxType(directory)

	if len(cmds) != 0:
		usage()
	selconf=selinuxConfig(directory, setype, usepwd)
	selconf.write()

except Exception as error:
	errorExit(error)
