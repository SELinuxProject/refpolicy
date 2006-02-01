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

include build.conf

# refpolicy version
VERSION = $(shell cat VERSION)

# executable paths
BINDIR := /usr/bin
SBINDIR := /usr/sbin
CHECKPOLICY := $(BINDIR)/checkpolicy
CHECKMODULE := $(BINDIR)/checkmodule
SEMODULE := $(SBINDIR)/semodule
SEMOD_PKG := $(BINDIR)/semodule_package
LOADPOLICY := $(SBINDIR)/load_policy
SETFILES := $(SBINDIR)/setfiles
GENHOMEDIRCON := $(SBINDIR)/genhomedircon
XMLLINT := $(BINDIR)/xmllint
SECHECK := $(BINDIR)/sechecker

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
DEVMAKEFILE = $(SUPPORT)/Makefile.devel
EXAMPLEMOD = $(addprefix $(DOCS)/,example.te example.if example.fc)

# config file paths
GLOBALTUN = $(POLDIR)/global_tunables
GLOBALBOOL = $(POLDIR)/global_booleans
MOD_CONF = $(POLDIR)/modules.conf
TUNABLES = $(POLDIR)/tunables.conf
BOOLEANS = $(POLDIR)/booleans.conf
ROLEMAP = $(POLDIR)/rolemap

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
HEADERDIR = $(SHAREDIR)/refpolicy/include
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

M4SUPPORT = $(wildcard $(POLDIR)/support/*.spt)

APPCONF := config/appconfig-$(TYPE)
APPDIR := $(CONTEXTPATH)
APPFILES := $(addprefix $(APPDIR)/,default_contexts default_type initrc_context failsafe_context userhelper_context removable_context dbus_contexts customizable_types) $(CONTEXTPATH)/files/media
CONTEXTFILES += $(wildcard $(APPCONF)/*_context*) $(APPCONF)/media
USER_FILES := $(POLDIR)/users

ALL_LAYERS := $(filter-out $(MODDIR)/CVS,$(shell find $(wildcard $(MODDIR)/*) -maxdepth 0 -type d))

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

# extract settings from modules.conf
BASE_MODS := $(addsuffix .te,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODBASE)") print $$1 }' $(MOD_CONF) 2> /dev/null))
MOD_MODS := $(addsuffix .te,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODMOD)") print $$1 }' $(MOD_CONF) 2> /dev/null))
OFF_MODS := $(addsuffix .te,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODUNUSED)") print $$1 }' $(MOD_CONF) 2> /dev/null))

# filesystems to be labeled
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
	$(verbose) cd $(DOCS) && ../$(GENDOC) -t ../$(BOOLEANS) -m ../$(MOD_CONF) -x ../$(POLXML)

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
	$(verbose) echo '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>' > $@
	$(verbose) echo '<!DOCTYPE policy SYSTEM "$(notdir $(XMLDTD))">' >> $@
	$(verbose) $(GENXML) -w -m $(LAYERXML) -t $(GLOBALTUN) -b $(GLOBALBOOL) $(ALL_LAYERS) >> $@
	$(verbose) if test -x $(XMLLINT) && test -f $(XMLDTD); then \
		$(XMLLINT) --noout --dtdvalid $(XMLDTD) $@ ;\
	fi

html tmp/html: $(POLXML)
	@echo "Building html interface reference documentation in $(HTMLDIR)"
	@mkdir -p $(HTMLDIR)
	$(verbose) cd $(DOCS) && ../$(GENDOC) -d ../$(HTMLDIR) -T ../$(DOCTEMPLATE) -x ../$(POLXML)
	$(verbose) cp $(DOCTEMPLATE)/*.css $(HTMLDIR)
	@touch tmp/html

########################################
#
# Runtime binary policy patching of users
#
$(USERPATH)/system.users: $(M4SUPPORT) tmp/generated_definitions.conf $(USER_FILES)
	@mkdir -p $(USERPATH)
	@echo "Installing system.users"
	@echo "# " > tmp/system.users
	@echo "# Do not edit this file. " >> tmp/system.users
	@echo "# This file is replaced on reinstalls of this policy." >> tmp/system.users
	@echo "# Please edit local.users to make local changes." >> tmp/system.users
	@echo "#" >> tmp/system.users
	$(verbose) m4 -D self_contained_policy $(M4PARAM) $^ | sed -r -e 's/^[[:blank:]]+//' \
		-e '/^[[:blank:]]*($$|#)/d' >> tmp/system.users
	$(verbose) install -m 644 tmp/system.users $@

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
	@mkdir -p $(INSTALLDIR)
	$(verbose) sed -r -e 's/false/0/g' -e 's/true/1/g' \
		-e '/^[[:blank:]]*($$|#)/d' $(BOOLEANS) | sort > tmp/booleans
	$(verbose) install -m 644 tmp/booleans $@

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
install-headers: $(DETECTED_MODS:.te=.if) $(ROLEMAP) $(M4SUPPORT)
	@mkdir -p $(HEADERDIR)
	@echo "Installing policy headers"
	$(verbose) install -m 644 $^ $(HEADERDIR)
	$(verbose) $(GENPERM) $(AVS) $(SECCLASS) > $(HEADERDIR)/all_perms.spt

########################################
#
# Install policy documentation
#
install-docs: $(DEVMAKEFILE) $(EXAMPLEMOD) build.conf tmp/html
	@mkdir -p $(DOCSDIR)/html
	@echo "Installing policy documentation"
	$(verbose) install -m 644 $(DEVMAKEFILE) $(EXAMPLEMOD) $(DOCSDIR)
	$(verbose) install -m 644 build.conf $(DOCSDIR)/build.conf.example
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
tags:
	@($(CTAGS) --version | grep -q Exuberant) || (echo ERROR: Need exuberant-ctags to function!; exit 1)
	@LC_ALL=C $(CTAGS) --langdef=te --langmap=te:..te.if.spt \
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
	rm -f $(SUPPORT)/*.pyc
	rm -f $(FCSORT)
	rm -f $(MOD_CONF)
	rm -f $(BOOLEANS)
	rm -fR $(HTMLDIR)
	rm -f tags
ifneq ($(GENERATED_TE),)
	rm -f $(GENERATED_TE)
endif
ifneq ($(GENERATED_IF),)
	rm -f $(GENERATED_IF)
endif
ifneq ($(GENERATED_FC),)
	rm -f $(GENERATED_FC)
endif

.PHONY: install-src install-appconfig conf html bare tags
.SUFFIXES:
.SUFFIXES: .c
