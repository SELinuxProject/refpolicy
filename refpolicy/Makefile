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
#
# Please see build.conf for policy build options.
#

########################################
#
# NO OPTIONS BELOW HERE
#

# Include the local build.conf if it exists, otherwise
# include the configuration of the root directory.
include build.conf

ifdef LOCAL_ROOT
	-include $(LOCAL_ROOT)/build.conf
endif

# refpolicy version
VERSION = $(shell cat VERSION)

ifdef LOCAL_ROOT
BUILDDIR := $(LOCAL_ROOT)/
TMPDIR := $(LOCAL_ROOT)/tmp
TAGS := $(LOCAL_ROOT)/tags
else
TMPDIR := tmp
TAGS := tags
endif

# executable paths
BINDIR := /usr/bin
SBINDIR := /usr/sbin
CHECKPOLICY := $(BINDIR)/checkpolicy
CHECKMODULE := $(BINDIR)/checkmodule
SEMODULE := $(SBINDIR)/semodule
SEMOD_PKG := $(BINDIR)/semodule_package
SEMOD_LNK := $(BINDIR)/semodule_link
SEMOD_EXP := $(BINDIR)/semodule_expand
LOADPOLICY := $(SBINDIR)/load_policy
SETFILES := $(SBINDIR)/setfiles
GENHOMEDIRCON := $(SBINDIR)/genhomedircon
XMLLINT := $(BINDIR)/xmllint
SECHECK := $(BINDIR)/sechecker

# interpreters and aux tools
AWK ?= gawk
GREP ?= egrep
M4 ?= m4
PYTHON ?= python
SED ?= sed
SORT ?= LC_ALL=C sort

CFLAGS += -Wall

# policy source layout
POLDIR := policy
MODDIR := $(POLDIR)/modules
FLASKDIR := $(POLDIR)/flask
SECCLASS := $(FLASKDIR)/security_classes
ISIDS := $(FLASKDIR)/initial_sids
AVS := $(FLASKDIR)/access_vectors

# local source layout
ifdef LOCAL_ROOT
LOCAL_POLDIR := $(LOCAL_ROOT)/policy
LOCAL_MODDIR := $(LOCAL_POLDIR)/modules
endif

# policy building support tools
SUPPORT := support
GENXML := $(PYTHON) $(SUPPORT)/segenxml.py
GENDOC := $(PYTHON) $(SUPPORT)/sedoctool.py
GENPERM := $(PYTHON) $(SUPPORT)/genclassperms.py
FCSORT := $(TMPDIR)/fc_sort
SETBOOLS := $(AWK) -f $(SUPPORT)/set_bools_tuns.awk
get_type_attr_decl := $(SED) -r -f $(SUPPORT)/get_type_attr_decl.sed
comment_move_decl := $(SED) -r -f $(SUPPORT)/comment_move_decl.sed

# documentation paths
DOCS := doc
XMLDTD = $(DOCS)/policy.dtd
LAYERXML = metadata.xml
DOCTEMPLATE = $(DOCS)/templates
DOCFILES = $(DOCS)/Makefile.example $(addprefix $(DOCS)/,example.te example.if example.fc)

ifndef LOCAL_ROOT
POLXML = $(DOCS)/policy.xml
TUNXML = $(DOCS)/global_tunables.xml
BOOLXML = $(DOCS)/global_booleans.xml
HTMLDIR = $(DOCS)/html
else
POLXML = $(LOCAL_ROOT)/doc/policy.xml
TUNXML = $(LOCAL_ROOT)/doc/global_tunables.xml
BOOLXML = $(LOCAL_ROOT)/doc/global_booleans.xml
HTMLDIR = $(LOCAL_ROOT)/doc/html
endif

# config file paths
GLOBALTUN = $(POLDIR)/global_tunables
GLOBALBOOL = $(POLDIR)/global_booleans
TUNABLES = $(POLDIR)/tunables.conf
ROLEMAP = $(POLDIR)/rolemap
USER_FILES := $(POLDIR)/users

# local config file paths
ifndef LOCAL_ROOT
MOD_CONF = $(POLDIR)/modules.conf
BOOLEANS = $(POLDIR)/booleans.conf
else
MOD_CONF = $(LOCAL_POLDIR)/modules.conf
BOOLEANS = $(LOCAL_POLDIR)/booleans.conf
endif

# install paths
PKGNAME ?= refpolicy-$(VERSION)
PREFIX = $(DESTDIR)/usr
TOPDIR = $(DESTDIR)/etc/selinux
INSTALLDIR = $(TOPDIR)/$(NAME)
SRCPATH = $(INSTALLDIR)/src
USERPATH = $(INSTALLDIR)/users
CONTEXTPATH = $(INSTALLDIR)/contexts
FCPATH = $(CONTEXTPATH)/files/file_contexts
SHAREDIR = $(PREFIX)/share/selinux
MODPKGDIR = $(SHAREDIR)/$(NAME)
HEADERDIR = $(MODPKGDIR)/include
DOCSDIR = $(PREFIX)/share/doc/$(PKGNAME)

# compile strict policy if requested.
ifneq ($(findstring strict,$(TYPE)),)
	M4PARAM += -D strict_policy
endif

# compile targeted policy if requested.
ifneq ($(findstring targeted,$(TYPE)),)
	M4PARAM += -D targeted_policy
endif

# enable MLS if requested.
ifneq ($(findstring -mls,$(TYPE)),)
	M4PARAM += -D enable_mls
	CHECKPOLICY += -M
	CHECKMODULE += -M
endif

# enable MLS if MCS requested.
ifneq ($(findstring -mcs,$(TYPE)),)
	M4PARAM += -D enable_mcs
	CHECKPOLICY += -M
	CHECKMODULE += -M
endif

# enable distribution-specific policy
ifneq ($(DISTRO),)
	M4PARAM += -D distro_$(DISTRO)
endif

# rhel4 also implies redhat
ifeq "$(DISTRO)" "rhel4"
	M4PARAM += -D distro_redhat
endif

# enable polyinstantiation
ifeq ($(POLY),y)
	M4PARAM += -D enable_polyinstantiation
endif

ifneq ($(OUTPUT_POLICY),)
	CHECKPOLICY += -c $(OUTPUT_POLICY)
endif

# if not set, use the type as the name.
NAME ?= $(TYPE)

ifeq ($(DIRECT_INITRC),y)
	M4PARAM += -D direct_sysadm_daemon
endif

ifeq ($(QUIET),y)
	verbose = @
endif

M4PARAM += -D hide_broken_symptoms

# we need exuberant ctags; unfortunately it is named
# differently on different distros
ifeq ($(DISTRO),debian)
	CTAGS := ctags-exuberant
endif

ifeq ($(DISTRO),gentoo)
	CTAGS := exuberant-ctags	
endif

CTAGS ?= ctags

# determine the policy version and current kernel version if possible
PV := $(shell $(CHECKPOLICY) -V |cut -f 1 -d ' ')
KV := $(shell cat /selinux/policyvers)

# dont print version warnings if we are unable to determine
# the currently running kernel's policy version
ifeq ($(KV),)
	KV := $(PV)
endif

M4SUPPORT := $(wildcard $(POLDIR)/support/*.spt)
ifdef LOCAL_ROOT
M4SUPPORT += $(wildcard $(LOCAL_POLDIR)/support/*.spt)
endif

APPCONF := config/appconfig-$(TYPE)
SEUSERS := $(APPCONF)/seusers
APPDIR := $(CONTEXTPATH)
APPFILES := $(addprefix $(APPDIR)/,default_contexts default_type initrc_context failsafe_context userhelper_context removable_context dbus_contexts customizable_types) $(CONTEXTPATH)/files/media
CONTEXTFILES += $(wildcard $(APPCONF)/*_context*) $(APPCONF)/media

ALL_LAYERS := $(filter-out $(MODDIR)/CVS,$(shell find $(wildcard $(MODDIR)/*) -maxdepth 0 -type d))
ifdef LOCAL_ROOT
ALL_LAYERS += $(filter-out $(LOCAL_MODDIR)/CVS,$(shell find $(wildcard $(LOCAL_MODDIR)/*) -maxdepth 0 -type d))
endif

GENERATED_TE := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te.in)))
GENERATED_IF := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.if.in)))
GENERATED_FC := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.fc.in)))

# sort here since it removes duplicates, which can happen
# when a generated file is already generated
DETECTED_MODS := $(sort $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te)) $(GENERATED_TE))

# modules.conf setting for base module
MODBASE := base

# modules.conf setting for loadable module
MODMOD := module

# modules.conf setting for unused module
MODUNUSED := off

# test for module overrides from command line
MOD_TEST = $(filter $(APPS_OFF), $(APPS_BASE) $(APPS_MODS))
MOD_TEST += $(filter $(APPS_MODS), $(APPS_BASE))
ifneq ($(strip $(MOD_TEST)),)
        $(error Applications must be base, module, or off, and not in more than one list! $(strip $(MOD_TEST)) found in multiple lists!)
endif

# add on suffix to modules specified on command line
CMDLINE_BASE := $(addsuffix .te,$(APPS_BASE))
CMDLINE_MODS := $(addsuffix .te,$(APPS_MODS))
CMDLINE_OFF := $(addsuffix .te,$(APPS_OFF))

# extract settings from modules.conf
MOD_CONF_BASE := $(addsuffix .te,$(sort $(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODBASE)") print $$1 }' $(MOD_CONF) 2> /dev/null)))
MOD_CONF_MODS := $(addsuffix .te,$(sort $(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODMOD)") print $$1 }' $(MOD_CONF) 2> /dev/null)))
MOD_CONF_OFF := $(addsuffix .te,$(sort $(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODUNUSED)") print $$1 }' $(MOD_CONF) 2> /dev/null)))

BASE_MODS := $(CMDLINE_BASE)
MOD_MODS := $(CMDLINE_MODS)
OFF_MODS := $(CMDLINE_OFF)

BASE_MODS += $(filter-out $(CMDLINE_OFF) $(CMDLINE_BASE) $(CMDLINE_MODS), $(MOD_CONF_BASE))
MOD_MODS += $(filter-out $(CMDLINE_OFF) $(CMDLINE_BASE) $(CMDLINE_MODS), $(MOD_CONF_MODS))
OFF_MODS += $(filter-out $(CMDLINE_OFF) $(CMDLINE_BASE) $(CMDLINE_MODS), $(MOD_CONF_OFF))

# add modules not in modules.conf to the off list
OFF_MODS += $(filter-out $(BASE_MODS) $(MOD_MODS) $(OFF_MODS),$(notdir $(DETECTED_MODS)))

# filesystems to be used in labeling targets
FILESYSTEMS = $(shell mount | grep -v "context=" | egrep -v '\((|.*,)bind(,.*|)\)' | awk '/(ext[23]| xfs| jfs).*rw/{print $$3}';)

########################################
#
# Functions
#

# parse-rolemap modulename,outputfile
define parse-rolemap
	$(verbose) m4 $(M4PARAM) $(ROLEMAP) | \
		awk '/^[[:blank:]]*[A-Za-z]/{ print "gen_require(type " $$3 "; role " $$1 ";)\n$1_per_userdomain_template(" $$2 "," $$3 "," $$1 ")" }' >> $2
endef

# peruser-expansion modulename,outputfile
define peruser-expansion
	$(verbose) echo "ifdef(\`""$1""_per_userdomain_template',\`" > $2
	$(call parse-rolemap,$1,$2)
	$(verbose) echo "')" >> $2
endef

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
# NOTE: There is no "local" version of these files.
#
generate: $(GENERATED_TE) $(GENERATED_IF) $(GENERATED_FC)

$(MODDIR)/kernel/corenetwork.if: $(MODDIR)/kernel/corenetwork.if.m4 $(MODDIR)/kernel/corenetwork.if.in
	@echo "#" > $@
	@echo "# This is a generated file!  Instead of modifying this file, the" >> $@
	@echo "# $(notdir $@).in or $(notdir $@).m4 file should be modified." >> $@
	@echo "#" >> $@
	$(verbose) cat $(MODDIR)/kernel/corenetwork.if.in >> $@
	$(verbose) egrep "^[[:blank:]]*network_(interface|node|port)\(.*\)" $(@:.if=.te).in \
		| m4 -D self_contained_policy $(M4PARAM) $(MODDIR)/kernel/corenetwork.if.m4 - \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@

$(MODDIR)/kernel/corenetwork.te: $(MODDIR)/kernel/corenetwork.te.m4 $(MODDIR)/kernel/corenetwork.te.in
	@echo "#" > $@
	@echo "# This is a generated file!  Instead of modifying this file, the" >> $@
	@echo "# $(notdir $@).in or $(notdir $@).m4 file should be modified." >> $@
	@echo "#" >> $@
	$(verbose) m4 -D self_contained_policy $(M4PARAM) $^ \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@

########################################
#
# Create config files
#
conf: $(MOD_CONF) $(BOOLEANS) $(GENERATED_TE) $(GENERATED_IF) $(GENERATED_FC)

$(MOD_CONF) $(BOOLEANS): $(POLXML)
	@echo "Updating $(MOD_CONF) and $(BOOLEANS)"
	$(verbose) $(GENDOC) -b $(BOOLEANS) -m $(MOD_CONF) -x $(POLXML)

########################################
#
# Generate the fc_sort program
#
$(FCSORT) : $(SUPPORT)/fc_sort.c
	$(verbose) $(CC) $(CFLAGS) $(SUPPORT)/fc_sort.c -o $(FCSORT)

########################################
#
# Documentation generation
#

# minimal dependencies here, because we don't want to rebuild 
# this and its dependents every time the dependencies
# change.  Also use all .if files here, rather then just the
# enabled modules.
xml: $(POLXML)
$(POLXML): $(DETECTED_MODS:.te=.if) $(foreach dir,$(ALL_LAYERS),$(dir)/$(LAYERXML))
	@echo "Creating $(@F)"
	@test -d $(dir $(POLXML)) || mkdir -p $(dir $(POLXML))
	@test -d $(TMPDIR) || mkdir -p $(TMPDIR)
	$(verbose) echo '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>' > $@
	$(verbose) echo '<!DOCTYPE policy SYSTEM "$(notdir $(XMLDTD))">' >> $@
	$(verbose) $(GENXML) -m $(LAYERXML) -t $(GLOBALTUN) -b $(GLOBALBOOL) -o $(DOCS) $(ALL_LAYERS) >> $@
	$(verbose) if test -x $(XMLLINT) && test -f $(XMLDTD); then \
		$(XMLLINT) --noout --path $(dir $(XMLDTD)) --dtdvalid $(XMLDTD) $@ ;\
	fi

$(TUNXML) $(BOOLXML): $(POLXML)

html $(TMPDIR)/html: $(POLXML)
	@echo "Building html interface reference documentation in $(HTMLDIR)"
	@test -d $(HTMLDIR) || mkdir -p $(HTMLDIR)
	@test -d $(TMPDIR) || mkdir -p $(TMPDIR)
	$(verbose) $(GENDOC) -d $(HTMLDIR) -T $(DOCTEMPLATE) -x $(POLXML)
	$(verbose) cp $(DOCTEMPLATE)/*.css $(HTMLDIR)
	@touch $(TMPDIR)/html

########################################
#
# Runtime binary policy patching of users
#
$(USERPATH)/system.users: $(M4SUPPORT) $(TMPDIR)/generated_definitions.conf $(USER_FILES)
	@mkdir -p $(TMPDIR)
	@mkdir -p $(USERPATH)
	@echo "Installing system.users"
	@echo "# " > $(TMPDIR)/system.users
	@echo "# Do not edit this file. " >> $(TMPDIR)/system.users
	@echo "# This file is replaced on reinstalls of this policy." >> $(TMPDIR)/system.users
	@echo "# Please edit local.users to make local changes." >> $(TMPDIR)/system.users
	@echo "#" >> $(TMPDIR)/system.users
	$(verbose) m4 -D self_contained_policy $(M4PARAM) $^ | sed -r -e 's/^[[:blank:]]+//' \
		-e '/^[[:blank:]]*($$|#)/d' >> $(TMPDIR)/system.users
	$(verbose) install -m 644 $(TMPDIR)/system.users $@

$(USERPATH)/local.users: config/local.users
	@mkdir -p $(USERPATH)
	@echo "Installing local.users"
	$(verbose) install -b -m 644 $< $@

########################################
#
# Appconfig files
#
install-appconfig: $(APPFILES)

$(INSTALLDIR)/booleans: $(BOOLEANS)
	@mkdir -p $(TMPDIR)
	@mkdir -p $(INSTALLDIR)
	$(verbose) sed -r -e 's/false/0/g' -e 's/true/1/g' \
		-e '/^[[:blank:]]*($$|#)/d' $(BOOLEANS) | sort > $(TMPDIR)/booleans
	$(verbose) install -m 644 $(TMPDIR)/booleans $@

$(CONTEXTPATH)/files/media: $(APPCONF)/media
	@mkdir -p $(CONTEXTPATH)/files/
	$(verbose) install -m 644 $< $@

$(APPDIR)/default_contexts: $(APPCONF)/default_contexts
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/removable_context: $(APPCONF)/removable_context
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/default_type: $(APPCONF)/default_type
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/userhelper_context: $(APPCONF)/userhelper_context
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/initrc_context: $(APPCONF)/initrc_context
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/failsafe_context: $(APPCONF)/failsafe_context
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/dbus_contexts: $(APPCONF)/dbus_contexts
	@mkdir -p $(APPDIR)
	$(verbose) install -m 644 $< $@

$(APPDIR)/users/root: $(APPCONF)/root_default_contexts
	@mkdir -p $(APPDIR)/users
	$(verbose) install -m 644 $< $@

########################################
#
# Install policy headers
#
install-headers: $(TUNXML) $(BOOLXML)
	@mkdir -p $(HEADERDIR)
	@echo "Installing $(TYPE) policy headers."
	$(verbose) install -m 644 $(TUNXML) $(BOOLXML) $(HEADERDIR)
	$(verbose) m4 $(M4PARAM) $(ROLEMAP) > $(HEADERDIR)/$(notdir $(ROLEMAP))
	$(verbose) mkdir -p $(HEADERDIR)/support
	$(verbose) install -m 644 $(M4SUPPORT) $(word $(words $(GENXML)),$(GENXML)) $(XMLDTD) $(HEADERDIR)/support
	$(verbose) $(GENPERM) $(AVS) $(SECCLASS) > $(HEADERDIR)/support/all_perms.spt
	$(verbose) for i in $(notdir $(ALL_LAYERS)); do \
		mkdir -p $(HEADERDIR)/$$i ;\
		install -m 644 $(MODDIR)/$$i/*.if \
			$(MODDIR)/$$i/metadata.xml \
			$(HEADERDIR)/$$i ;\
	done
	$(verbose) echo "TYPE ?= $(TYPE)" > $(HEADERDIR)/build.conf
	$(verbose) echo "NAME ?= $(NAME)" >> $(HEADERDIR)/build.conf
ifneq "$(DISTRO)" ""
	$(verbose) echo "DISTRO ?= $(DISTRO)" >> $(HEADERDIR)/build.conf
endif
	$(verbose) echo "MONOLITHIC ?= n" >> $(HEADERDIR)/build.conf
	$(verbose) echo "DIRECT_INITRC ?= $(DIRECT_INITRC)" >> $(HEADERDIR)/build.conf
	$(verbose) echo "POLY ?= $(POLY)" >> $(HEADERDIR)/build.conf
	$(verbose) install -m 644 $(SUPPORT)/Makefile.devel $(HEADERDIR)/Makefile

########################################
#
# Install policy documentation
#
install-docs: $(TMPDIR)/html
	@mkdir -p $(DOCSDIR)/html
	@echo "Installing policy documentation"
	$(verbose) install -m 644 $(DOCFILES) $(DOCSDIR)
	$(verbose) install -m 644 $(wildcard $(HTMLDIR)/*) $(DOCSDIR)/html

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
# Generate tags file
#
tags: $(TAGS)
$(TAGS):
	@($(CTAGS) --version | grep -q Exuberant) || (echo ERROR: Need exuberant-ctags to function!; exit 1)
	@LC_ALL=C $(CTAGS) -f $(TAGS) --langdef=te --langmap=te:..te.if.spt \
	 --regex-te='/^type[ \t]+(\w+)(,|;)/\1/t,type/' \
	 --regex-te='/^typealias[ \t]+\w+[ \t+]+alias[ \t]+(\w+);/\1/t,type/' \
	 --regex-te='/^attribute[ \t]+(\w+);/\1/a,attribute/' \
	 --regex-te='/^[ \t]*define\(`(\w+)/\1/d,define/' \
	 --regex-te='/^[ \t]*interface\(`(\w+)/\1/i,interface/' \
	 --regex-te='/^[ \t]*bool[ \t]+(\w+)/\1/b,bool/' policy/modules/*/*.{if,te} policy/support/*.spt

########################################
#
# Filesystem labeling
#
checklabels:
	@echo "Checking labels on filesystem types: ext2 ext3 xfs jfs"
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(verbose) $(SETFILES) -v -n $(FCPATH) $(FILESYSTEMS)

restorelabels:
	@echo "Restoring labels on filesystem types: ext2 ext3 xfs jfs"
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(verbose) $(SETFILES) -v $(FCPATH) $(FILESYSTEMS)

relabel:
	@echo "Relabeling filesystem types: ext2 ext3 xfs jfs"
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(verbose) $(SETFILES) $(FCPATH) $(FILESYSTEMS)

resetlabels:
	@echo "Resetting labels on filesystem types: ext2 ext3 xfs jfs"
	@if test -z "$(FILESYSTEMS)"; then \
		echo "No filesystems with extended attributes found!" ;\
		false ;\
	fi
	$(verbose) $(SETFILES) -F $(FCPATH) $(FILESYSTEMS)

########################################
#
# Clean everything
#
bare: clean
	rm -f $(POLXML)
	rm -f $(TUNXML)
	rm -f $(BOOLXML)
	rm -f $(MOD_CONF)
	rm -f $(BOOLEANS)
	rm -fR $(HTMLDIR)
	rm -f $(TAGS)
# don't remove these files if we're given a local root
ifndef LOCAL_ROOT
	rm -f $(FCSORT)
	rm -f $(SUPPORT)/*.pyc
ifneq ($(GENERATED_TE),)
	rm -f $(GENERATED_TE)
endif
ifneq ($(GENERATED_IF),)
	rm -f $(GENERATED_IF)
endif
ifneq ($(GENERATED_FC),)
	rm -f $(GENERATED_FC)
endif
endif

.PHONY: install-src install-appconfig generate xml conf html bare tags
.SUFFIXES:
.SUFFIXES: .c
