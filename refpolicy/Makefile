#
# Makefile for the security policy.
#
# Targets:
# 
# install       - compile and install the policy configuration, and context files.
# load          - compile, install, and load the policy configuration.
# reload        - compile, install, and load/reload the policy configuration.
# relabel       - relabel filesystems based on the file contexts configuration.
# checklabels   - check filesystems against the file context configuration
# restorelabels - check filesystems against the file context configuration
#                 and restore the label of files with incorrect labels
# policy        - compile the policy configuration locally for testing/development.
# xml           - create a XML file from in-policy documentation
#
# The default target is 'policy'.
#

########################################
#
# Configurable portions of the Makefile
#

# Build compatibility policies 
POLICYCOMPAT = 18

# Build MLS policies
MLS=n

# set distribution
override M4PARAM += -D distro_redhat

# Uncomment this to disable command echoing
#QUIET:=@

# Policy type (strict, targeted, etc)
TYPE := strict

########################################
#
# Invariant portions of the Makefile
#

# executable paths
PREFIX := /usr
BINDIR := $(PREFIX)/bin
SBINDIR := $(PREFIX)/sbin
CHECKPOLICY := $(BINDIR)/checkpolicy
LOADPOLICY := $(SBINDIR)/load_policy
SETFILES := $(SBINDIR)/setfiles

XMLLINT := $(BINDIR)/xmllint
XMLDTD := policy.dtd

# enable MLS if requested.
ifeq ($(MLS),y)
	override M4PARAM += -D enable_mls
	CHECKPOLICY += -M
endif

ifneq ($(POLICYCOMPAT),)
	CHECKPOLICY += -c $(POLICYCOMPAT)
endif

# determine the policy version and current kernel version if possible
PV := $(shell $(CHECKPOLICY) -V |cut -f 1 -d ' ')
KV := $(shell cat /selinux/policyvers)

# dont print version warnings if we are unable to determine
# the currently running kernel's policy version
ifeq ($(KV),)
	KV := $(PV)
endif

FC := file_contexts
POLVER := policy.$(PV)

# install paths
TOPDIR = $(DESTDIR)/etc/selinux
INSTALLDIR = $(TOPDIR)/$(TYPE)
POLICYPATH = $(INSTALLDIR)/policy
SRCPATH = $(INSTALLDIR)/src
USERPATH = $(INSTALLDIR)/users
CONTEXTPATH = $(INSTALLDIR)/contexts
LOADPATH = $(POLICYPATH)/$(POLVER)
FCPATH = $(CONTEXTPATH)/files/file_contexts
HOMEDIRPATH = $(CONTEXTPATH)/files/homedir_template

BASE_MODULE = kernel
FLASKDIR = flask
APPCONF = appconfig

APPDIR := $(CONTEXTPATH)
APPFILES := $(addprefix $(APPDIR)/,default_contexts default_type initrc_context failsafe_context userhelper_context removable_context dbus_contexts customizable_types) $(CONTEXTPATH)/files/media
CONTEXTFILES += $(wildcard $(APPCONF)/*_context*) $(APPCONF)/media
USER_FILES := users 

DETECTED_DIRS := $(shell find $(wildcard *) -maxdepth 0 -type d)
ALL_LAYERS := $(filter-out tmp CVS $(APPCONF) $(FLASKDIR),$(DETECTED_DIRS))

PRE_TE_FILES := $(addprefix $(FLASKDIR)/,security_classes initial_sids access_vectors) mls
ALL_INTERFACES := $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.if))
ALL_TE_FILES := $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te))
POST_TE_FILES := users constraints initial_sid_contexts fs_use

ALL_FC_FILES := $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.fc))

POLICY_SECTIONS := tmp/pre_te_files.conf tmp/generated_definitions.conf tmp/all_interfaces.conf tmp/all_attrs_types.conf tmp/only_te_rules.conf tmp/all_post.conf

########################################
#
# default action: build policy locally
#
default: policy

policy: $(POLVER)

install: $(LOADPATH) $(FCPATH) $(USERPATH)/local.users

load: tmp/load

########################################
#
# Build a binary policy locally
#
$(POLVER): policy.conf
	@echo "Compiling $(POLVER)"
ifneq ($(PV),$(KV))
	@echo
	@echo "WARNING: Policy version mismatch!  Is your POLICYCOMPAT set correctly?"
	@echo
endif
	$(QUIET) $(CHECKPOLICY) $^ -o $@

########################################
#
# Install a binary policy
#
$(LOADPATH): policy.conf
	@mkdir -p $(POLICYPATH)
	@echo "Compiling and installing $(LOADPATH)"
ifneq ($(PV),$(KV))
	@echo
	@echo "WARNING: Policy version mismatch!  Is your POLICYCOMPAT set correctly?"
	@echo
endif
	$(QUIET) $(CHECKPOLICY) $^ -o $@

########################################
#
# Load the binary policy
#
reload tmp/load: $(LOADPATH) $(FCPATH)
	@echo "Loading $(LOADPATH)"
	$(QUIET) $(LOADPOLICY) -q $(LOADPATH)
	@touch tmp/load

########################################
#
# Construct a monolithic policy.conf
#
policy.conf: $(POLICY_SECTIONS)
	@echo "Creating policy.conf"
# checkpolicy can use the #line directives provided by -s for error reporting:
	$(QUIET) m4 $(M4PARAM) -D monolithic_policy -s $^ > tmp/$@.tmp
	$(QUIET) sed -e /^portcon/d -e /^nodecon/d -e /^netifcon/d < tmp/$@.tmp > $@
# the ordering of these ocontexts matters:
	$(QUIET) grep ^portcon tmp/$@.tmp >> $@ || true
	$(QUIET) grep ^netifcon tmp/$@.tmp >> $@ || true
	$(QUIET) grep ^nodecon tmp/$@.tmp >> $@ || true

tmp/pre_te_files.conf: $(PRE_TE_FILES)
	@test -d tmp || mkdir -p tmp
	$(QUIET) cat $^ > $@

tmp/generated_definitions.conf: $(ALL_LAYERS) $(ALL_TE_FILES) $(BASE_MODULE)/corenetwork.if $(BASE_MODULE)/corenetwork.te
	@test -d tmp || mkdir -p tmp
	$(QUIET) echo "define(\`per_userdomain_templates',\`" > $@
	$(QUIET) for i in $(patsubst %.te,%,$(notdir $(ALL_TE_FILES))); do \
		echo "ifdef(\`""$$i""_per_userdomain_template',\`""$$i""_per_userdomain_template("'$$1'")')" \
			>> $@ ;\
	done
	$(QUIET) echo "')" >> $@
	$(QUIET) for i in $(notdir $(ALL_TE_FILES)); do \
		echo "define(\`$$i')" >> $@ ;\
	done
	$(QUIET) egrep "^network_(interface|node|port)\(.*\)" $(BASE_MODULE)/corenetwork.te \
		| m4 $(M4PARAM) -D monolithic_policy -D interface_pass $(BASE_MODULE)/global.if $(BASE_MODULE)/corenetwork.if - \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@
# this is so the xml works:
	$(QUIET) echo "## </module>" >> $@

tmp/all_interfaces.conf: $(ALL_INTERFACES)
	@test -d tmp || mkdir -p tmp
	$(QUIET) cat $^ > $@

tmp/all_te_files.conf: $(ALL_TE_FILES)
	@test -d tmp || mkdir -p tmp
	$(QUIET) cat $^ > $@

tmp/post_te_files.conf: $(POST_TE_FILES)
	@test -d tmp || mkdir -p tmp
	$(QUIET) cat $^ > $@

# extract attributes and put them first. extract post te stuff
# like genfscon and put last.  portcon, nodecon, and netifcon
# is delayed since they are generated by m4
tmp/all_attrs_types.conf tmp/only_te_rules.conf tmp/all_post.conf: tmp/all_te_files.conf tmp/post_te_files.conf
	$(QUIET) grep ^attribute tmp/all_te_files.conf > tmp/all_attrs_types.conf || true
	$(QUIET) grep '^type ' tmp/all_te_files.conf >> tmp/all_attrs_types.conf
	$(QUIET) cat tmp/post_te_files.conf > tmp/all_post.conf
	$(QUIET) grep ^genfscon tmp/all_te_files.conf >> tmp/all_post.conf || true
	$(QUIET) sed -e /^attribute/d -e '/^type /d' -e /^genfscon/d < tmp/all_te_files.conf > tmp/only_te_rules.conf

########################################
#
# Remove the dontaudit rules from the policy.conf
#
enableaudit: policy.conf
	@test -d tmp || mkdir -p tmp
	@echo "Removing dontaudit rules from policy.conf"
	$(QUIET) grep -v dontaudit policy.conf > tmp/policy.audit
	$(QUIET) mv tmp/policy.audit policy.conf

########################################
#
# Construct file_contexts
#
$(FC): kernel/global.if $(ALL_FC_FILES)
	@test -d tmp || mkdir -p tmp
	$(QUIET) m4 $(M4PARAM) $^ > $@

########################################
#
# Install file_contexts
#
$(FCPATH): $(FC) $(USERPATH)/system.users 
	@mkdir -p $(CONTEXTPATH)/files
	$(QUIET) install -m 644 $(FC) $(FCPATH)
#	$(QUIET) install -m 644 $(HOMEDIR_TEMPLATE) $(HOMEDIRPATH)
#	$(QUIET) $(GENHOMEDIRCON) -d $(TOPDIR) -t $(TYPE) $(USEPWD)

########################################
#
# Filesystem labeling
#
FILESYSTEMS := `mount | grep -v "context=" | egrep -v '\((|.*,)bind(,.*|)\)' | awk '/(ext[23]| xfs| jfs).*rw/{print $$3}';`

checklabels: $(FC) $(SETFILES)
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(QUIET) $(SETFILES) -v -n $(FC) $(FILESYSTEMS)

restorelabels: $(FC) $(SETFILES)
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(QUIET) $(SETFILES) -v $(FC) $(FILESYSTEMS)

relabel:  $(FC) $(SETFILES)
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(QUIET) $(SETFILES) $(FC) $(FILESYSTEMS)

########################################
#
# Documentation generation
#

xml: policy.xml

policy.xml: $(ALL_INTERFACES) tmp/generated_definitions.conf
	@echo "Creating $@"
	$(QUIET) echo '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>' > $@
	$(QUIET) echo '<!DOCTYPE policy SYSTEM "policy.dtd">' >> $@
	$(QUIET) echo "<policy>" >> $@
# process this through m4 to eliminate the generated definitions.
# currently these are only in corenetwork.if
	$(QUIET) m4 $^ | egrep -h "^##[[:blank:]]" | sed -e 's/^##[[:blank:]]//g' >> $@
	$(QUIET) echo "</policy>" >> $@
	$(QUIET) if test -x $(XMLLINT) && test -f $(XMLDTD); then \
		$(XMLLINT) --noout --dtdvalid $(XMLDTD) $@ ;\
	fi

########################################
#
# Runtime binary policy patching of users
#
$(USERPATH)/system.users: $(USER_FILES) tmp/generated_definitions.conf
	@mkdir -p $(USERPATH)
	@echo "Installing system.users"
	@echo "# " > tmp/system.users
	@echo "# Do not edit this file. " >> tmp/system.users
	@echo "# This file is replaced on reinstalls of this policy." >> tmp/system.users
	@echo "# Please edit local.users to make local changes." >> tmp/system.users
	@echo "#" >> tmp/system.users
	$(QUIET) m4 $(M4PARAM) tmp/generated_definitions.conf $(USER_FILES) | \
		egrep -v "^[[:space:]]*($$|#)" >> tmp/system.users
	$(QUIET) install -m 644 tmp/system.users $@

$(USERPATH)/local.users: local.users
	@mkdir -p $(USERPATH)
	@echo "Installing local.users"
	$(QUIET) install -C -b -m 644 $< $@

########################################
#
# Appconfig files
#
install-appconfig: $(APPFILES)

$(CONTEXTPATH)/files/media: $(APPCONF)/media
	mkdir -p $(CONTEXTPATH)/files/
	install -m 644 $< $@

$(APPDIR)/default_contexts: $(APPCONF)/default_contexts
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/removable_context: $(APPCONF)/removable_context
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/customizable_types: policy.conf
	mkdir -p $(APPDIR)
	@grep "^type .*customizable" $< | cut -d',' -f1 | cut -d' ' -f2 > tmp/customizable_types
	install -m 644 tmp/customizable_types $@ 

$(APPDIR)/default_type: $(APPCONF)/default_type
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/userhelper_context: $(APPCONF)/userhelper_context
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/initrc_context: $(APPCONF)/initrc_context
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/failsafe_context: $(APPCONF)/failsafe_context
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/dbus_contexts: $(APPCONF)/dbus_contexts
	mkdir -p $(APPDIR)
	install -m 644 $< $@

$(APPDIR)/users/root: $(APPCONF)/root_default_contexts
	mkdir -p $(APPDIR)/users
	install -m 644 $< $@

clean:
	rm -fR tmp
	rm -f policy.xml
	rm -f policy.conf
	rm -f policy.$(PV)
	rm -f $(FC)

.PHONY: default policy install reload enableaudit checklabels restorelabels relabel xml clean
