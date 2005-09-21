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
#
# The default target is 'policy'.
#

########################################
#
# Configurable portions of the Makefile
#

# Policy version
# By default, checkpolicy will create the highest
# version policy it supports.  Setting this will
# override the version.
#OUTPUT_POLICY = 18

# Policy Type
# strict, targeted,
# strict-mls, targeted-mls,
# strict-mcs, targeted-mcs
TYPE = strict

# Policy Name
# If set, this will be used as the policy
# name.  Otherwise the policy type will be
# used for the name.
NAME = refpolicy

# Distribution
# Some distributions have portions of policy
# for programs or configurations specific to the
# distribution.  Setting this will enable options
# for the distribution.
# redhat, gentoo, debian, and suse are current options.
# Fedora users should enable redhat.
#DISTRO = redhat

# Direct admin init
# Setting this will allow sysadm to directly
# run init scripts, instead of requring run_init.
# This is a build option, as role transitions do
# not work in conditional policy.
DIRECT_INITRC=n

# Build monolithic policy.  Putting n here
# will build a loadable module policy.
MONOLITHIC=y

# Uncomment this to disable command echoing
#QUIET:=@

########################################
#
# NO OPTIONS BELOW HERE
#

# executable paths
PREFIX := /usr
BINDIR := $(PREFIX)/bin
SBINDIR := $(PREFIX)/sbin
CHECKPOLICY := $(BINDIR)/checkpolicy
CHECKMODULE := $(BINDIR)/checkmodule
SEMOD_PKG := $(BINDIR)/semodule_package
LOADPOLICY := $(SBINDIR)/load_policy
SETFILES := $(SBINDIR)/setfiles
GENHOMEDIRCON := $(SBINDIR)/genhomedircon
XMLLINT := $(BINDIR)/xmllint

CFLAGS := -Wall

# policy source layout
POLDIR := policy
MODDIR := $(POLDIR)/modules
FLASKDIR := $(POLDIR)/flask
SECCLASS := $(FLASKDIR)/security_classes
ISIDS := $(FLASKDIR)/initial_sids
AVS := $(FLASKDIR)/access_vectors

# policy building support tools
SUPPORT := support
GENXML := $(SUPPORT)/segenxml.py
GENDOC := $(SUPPORT)/sedoctool.py
GENPERM := $(SUPPORT)/genclassperms.py
FCSORT := $(SUPPORT)/fc_sort
SETTUN := $(SUPPORT)/set_tunables

# documentation paths
DOCS = doc
POLXML = $(DOCS)/policy.xml
XMLDTD = $(DOCS)/policy.dtd
LAYERXML = metadata.xml
HTMLDIR = $(DOCS)/html
DOCTEMPLATE = $(DOCS)/templates

# config file paths
GLOBALTUN := $(POLDIR)/global_tunables
MOD_CONF := $(POLDIR)/modules.conf
TUNABLES := $(POLDIR)/tunables.conf

# install paths
TOPDIR = $(DESTDIR)/etc/selinux
INSTALLDIR = $(TOPDIR)/$(NAME)
SRCPATH = $(INSTALLDIR)/src
USERPATH = $(INSTALLDIR)/users
CONTEXTPATH = $(INSTALLDIR)/contexts

# enable MLS if requested.
ifneq ($(findstring -mls,$(TYPE)),)
	override M4PARAM += -D enable_mls
	CHECKPOLICY += -M
	CHECKMODULE += -M
endif

# enable MLS if MCS requested.
ifneq ($(findstring -mcs,$(TYPE)),)
	override M4PARAM += -D enable_mcs
	CHECKPOLICY += -M
	CHECKMODULE += -M
endif

# compile targeted policy if requested.
ifneq ($(findstring targeted,$(TYPE)),)
	override M4PARAM += -D targeted_policy
endif

# enable distribution-specific policy
ifneq ($(DISTRO),)
	override M4PARAM += -D distro_$(DISTRO)
endif

ifneq ($(OUTPUT_POLICY),)
	CHECKPOLICY += -c $(OUTPUT_POLICY)
endif

ifeq ($(NAME),)
	NAME := $(TYPE)
endif

ifeq ($(DIRECT_INITRC),y)
	override M4PARAM += -D direct_sysadm_daemon
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

M4SUPPORT = $(wildcard $(POLDIR)/support/*.spt)

APPCONF := config/appconfig-$(TYPE)
APPDIR := $(CONTEXTPATH)
APPFILES := $(addprefix $(APPDIR)/,default_contexts default_type initrc_context failsafe_context userhelper_context removable_context dbus_contexts customizable_types) $(CONTEXTPATH)/files/media $(INSTALLDIR)/booleans
CONTEXTFILES += $(wildcard $(APPCONF)/*_context*) $(APPCONF)/media
USER_FILES := $(POLDIR)/systemuser $(POLDIR)/users

ALL_LAYERS := $(filter-out $(MODDIR)/CVS,$(shell find $(wildcard $(MODDIR)/*) -maxdepth 0 -type d))

GENERATED_TE := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te.in)))
GENERATED_IF := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.if.in)))
GENERATED_FC := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.fc.in)))

# sort here since it removes duplicates, which can happen
# when a generated file is already generated
DETECTED_MODS := $(sort $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te)) $(GENERATED_TE))

# modules.conf setting for base module
MODBASE := base

# modules.conf setting for module
MODMOD := module

# extract settings from modules.conf
BASE_MODS := $(foreach mod,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODBASE)") print $$1 }' $(MOD_CONF) 2> /dev/null),$(subst ./,,$(shell find -iname $(mod).te)))
MOD_MODS := $(foreach mod,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODMOD)") print $$1 }' $(MOD_CONF) 2> /dev/null),$(subst ./,,$(shell find -iname $(mod).te)))

HOMEDIR_TEMPLATE = tmp/homedir_template

########################################
#
# Load appropriate rules
#

ifeq ($(MONOLITHIC),y)
	include Rules.monolithic
else
	include Rules.modular
endif

########################################
#
# Generated files
#
$(MODDIR)/kernel/corenetwork.if: $(MODDIR)/kernel/corenetwork.if.m4 $(MODDIR)/kernel/corenetwork.if.in
	@echo "#" > $@
	@echo "# This is a generated file!  Instead of modifying this file, the" >> $@
	@echo "# $(notdir $@).in or $(notdir $@).m4 file should be modified." >> $@
	@echo "#" >> $@
	$(QUIET) cat $(MODDIR)/kernel/corenetwork.if.in >> $@
	$(QUIET) egrep "^[[:blank:]]*network_(interface|node|port)\(.*\)" $(@:.if=.te).in \
		| m4 -D self_contained_policy $(M4PARAM) $(M4SUPPORT) $(MODDIR)/kernel/corenetwork.if.m4 - \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@

$(MODDIR)/kernel/corenetwork.te: $(MODDIR)/kernel/corenetwork.te.m4 $(MODDIR)/kernel/corenetwork.te.in
	@echo "#" > $@
	@echo "# This is a generated file!  Instead of modifying this file, the" >> $@
	@echo "# $(notdir $@).in or $(notdir $@).m4 file should be modified." >> $@
	@echo "#" >> $@
	$(QUIET) m4 -D self_contained_policy $(M4PARAM) $(M4SUPPORT) $^ \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@

########################################
#
# Create config files
#
conf: $(MOD_CONF) $(TUNABLES) $(GENERATED_TE) $(GENERATED_IF) $(GENERATED_FC)

$(MOD_CONF) $(TUNABLES): $(POLXML)
	@echo "Updating $(MOD_CONF) and $(TUNABLES)"
	$(QUIET) cd $(DOCS) && ../$(GENDOC) -t ../$(TUNABLES) -m ../$(MOD_CONF) -x ../$(POLXML)

########################################
#
# Documentation generation
#

# minimal dependencies here, because we don't want to rebuild 
# this and its dependents every time the dependencies
# change.  Also use all .if files here, rather then just the
# enabled modules.
$(POLXML): $(DETECTED_MODS:.te=.if) $(foreach dir,$(ALL_LAYERS),$(dir)/$(LAYERXML))
	@echo "Creating $@"
	@mkdir -p tmp
	$(QUIET) echo '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>' > $@
	$(QUIET) echo '<!DOCTYPE policy SYSTEM "$(notdir $(XMLDTD))">' >> $@
	$(QUIET) $(GENXML) -w -m $(LAYERXML) -t $(GLOBALTUN) $(ALL_LAYERS) >> $@
	$(QUIET) if test -x $(XMLLINT) && test -f $(XMLDTD); then \
		$(XMLLINT) --noout --dtdvalid $(XMLDTD) $@ ;\
	fi

html: $(POLXML)
	@mkdir -p $(HTMLDIR)
	$(QUIET) cd $(DOCS) && ../$(GENDOC) -d ../$(HTMLDIR) -T ../$(DOCTEMPLATE) -x ../$(POLXML)
	$(QUIET) cp $(DOCTEMPLATE)/*.css $(HTMLDIR)

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
	$(QUIET) m4 -D self_contained_policy $(M4PARAM) tmp/generated_definitions.conf $(USER_FILES) | \
		egrep -v "^[[:space:]]*($$|#)" >> tmp/system.users
	$(QUIET) install -m 644 tmp/system.users $@

$(USERPATH)/local.users: config/local.users
	@mkdir -p $(USERPATH)
	@echo "Installing local.users"
	$(QUIET) install -b -m 644 $< $@

########################################
#
# Appconfig files
#
install-appconfig: $(APPFILES)

$(INSTALLDIR)/booleans: $(TUNABLES)
	@mkdir -p $(INSTALLDIR)
	$(QUIET) egrep '^[[:blank:]]*[[:alpha:]]' $(TUNABLES) \
		| sed -e 's/false/0/g' -e 's/true/1/g' > tmp/booleans
	$(QUIET) install -m 644 tmp/booleans $@

$(CONTEXTPATH)/files/media: $(APPCONF)/media
	@mkdir -p $(CONTEXTPATH)/files/
	$(QUIET) install -m 644 $< $@

$(APPDIR)/default_contexts: $(APPCONF)/default_contexts
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/removable_context: $(APPCONF)/removable_context
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/customizable_types: policy.conf
	@mkdir -p $(APPDIR)
	$(QUIET) grep "^type .*customizable" $< | cut -d',' -f1 | cut -d' ' -f2 > tmp/customizable_types
	$(QUIET) install -m 644 tmp/customizable_types $@ 

$(APPDIR)/default_type: $(APPCONF)/default_type
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/userhelper_context: $(APPCONF)/userhelper_context
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/initrc_context: $(APPCONF)/initrc_context
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/failsafe_context: $(APPCONF)/failsafe_context
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/dbus_contexts: $(APPCONF)/dbus_contexts
	@mkdir -p $(APPDIR)
	$(QUIET) install -m 644 $< $@

$(APPDIR)/users/root: $(APPCONF)/root_default_contexts
	@mkdir -p $(APPDIR)/users
	$(QUIET) install -m 644 $< $@

########################################
#
# Install policy sources
#
install-src:
	rm -rf $(SRCPATH)/policy.old
	-mv $(SRCPATH)/policy $(SRCPATH)/policy.old
	mkdir -p $(SRCPATH)/policy
	cp -R . $(SRCPATH)/policy

########################################
#
# Clean everything
#
bare: clean
	rm -f $(POLXML)
	rm -f $(SUPPORT)/*.pyc
	rm -f $(FCSORT)
	rm -f $(MOD_CONF)
	rm -f $(TUNABLES)
	rm -fR $(HTMLDIR)
ifneq ($(GENERATED_TE),)
	rm -f $(GENERATED_TE)
endif
ifneq ($(GENERATED_IF),)
	rm -f $(GENERATED_IF)
endif
ifneq ($(GENERATED_FC),)
	rm -f $(GENERATED_FC)
endif

.PHONY: install-src install-appconfig conf html bare
