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

# Override default policy version
#OUTPUT_POLICY = 18

# Policy Type
# strict, targeted, strict-mls, targeted-mls
# strict and strict-mls are currently supported.
TYPE = strict

# If set, this will be used as the policy
# name.  Otherwise the policy type will be
# used for the name.
NAME = refpolicy

# Build monolithic policy.  Putting n here
# will build a loadable module policy.
# Only monolithic policies are currently supported.
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
LOADPOLICY := $(SBINDIR)/load_policy
SETFILES := $(SBINDIR)/setfiles
GENHOMEDIRCON := $(SBINDIR)/genhomedircon

CFLAGS := -Wall

SUPPORT := support
GENXML := $(SUPPORT)/segenxml.py
GENDOC := $(SUPPORT)/sedoctool.py
FCSORT := $(SUPPORT)/fc_sort
SETTUN := $(SUPPORT)/set_tunables

XMLLINT := $(BINDIR)/xmllint

# enable MLS if requested.
ifneq ($(findstring mls,$(TYPE)),)
	override M4PARAM += -D enable_mls
	CHECKPOLICY += -M
endif

# compile targeted policy if requested.
ifneq ($(findstring targeted,$(TYPE)),)
	override M4PARAM += -D targeted_policy
endif

ifeq ($(MONOLITHIC),y)
	override M4PARAM += -D monolithic_policy
endif

ifneq ($(OUTPUT_POLICY),)
	CHECKPOLICY += -c $(OUTPUT_POLICY)
endif

ifeq ($(NAME),)
	NAME := $(TYPE)
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
INSTALLDIR = $(TOPDIR)/$(NAME)
POLICYPATH = $(INSTALLDIR)/policy
SRCPATH = $(INSTALLDIR)/src
USERPATH = $(INSTALLDIR)/users
CONTEXTPATH = $(INSTALLDIR)/contexts
LOADPATH = $(POLICYPATH)/$(POLVER)
FCPATH = $(CONTEXTPATH)/files/file_contexts
HOMEDIRPATH = $(CONTEXTPATH)/files/homedir_template

POLDIR = policy
MODDIR = $(POLDIR)/modules

BASE_MODULE = $(MODDIR)/kernel
FLASKDIR = $(POLDIR)/flask
APPCONF = config/appconfig
M4SUPPORT = $(wildcard $(POLDIR)/support/*.spt)

GLOBALTUN := $(POLDIR)/global_tunables
MOD_CONF := $(POLDIR)/modules.conf
TUNABLES := $(POLDIR)/tunables.conf

APPDIR := $(CONTEXTPATH)
APPFILES := $(addprefix $(APPDIR)/,default_contexts default_type initrc_context failsafe_context userhelper_context removable_context dbus_contexts customizable_types) $(CONTEXTPATH)/files/media $(INSTALLDIR)/booleans
CONTEXTFILES += $(wildcard $(APPCONF)/*_context*) $(APPCONF)/media
USER_FILES := $(POLDIR)/users 

ALL_LAYERS := $(filter-out $(MODDIR)/CVS,$(shell find $(wildcard $(MODDIR)/*) -maxdepth 0 -type d))

GENERATED_TE := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te.in)))
GENERATED_IF := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.if.in)))
GENERATED_FC := $(basename $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.fc.in)))

# sort here since it removes duplicates, which can happen
# when a generated file is already generated
DETECTED_MODS := $(sort $(foreach dir,$(ALL_LAYERS),$(wildcard $(dir)/*.te)) $(GENERATED_TE))

MODBASE := base
MODMOD := module
BASE_MODS := $(foreach mod,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODBASE)") print $$1 }' $(MOD_CONF) 2> /dev/null),$(subst ./,,$(shell find -iname $(mod).te)))
MOD_MODS := $(foreach mod,$(shell awk '/^[[:blank:]]*[[:alpha:]]/{ if ($$3 == "$(MODMOD)") print $$1 }' $(MOD_CONF) 2> /dev/null),$(subst ./,,$(shell find -iname $(mod).te)))

# for monolithic policy use all base and module to create policy
# for modular policy, use only base
ifeq ($(MONOLITHIC),y)
	ENABLEMOD := $(BASE_MODS) $(MOD_MODS)
else
	ENABLEMOD := $(BASE_MODS)
endif

ALL_MODULES := $(filter $(ENABLEMOD),$(DETECTED_MODS))

PRE_TE_FILES := $(addprefix $(FLASKDIR)/,security_classes initial_sids access_vectors) $(M4SUPPORT) $(POLDIR)/mls
ALL_INTERFACES := $(ALL_MODULES:.te=.if)
ALL_TE_FILES := $(ALL_MODULES)
POST_TE_FILES := $(POLDIR)/users $(POLDIR)/constraints

ALL_FC_FILES := $(ALL_MODULES:.te=.fc)
HOMEDIR_TEMPLATE = tmp/homedir_template

POLICY_SECTIONS := tmp/pre_te_files.conf tmp/generated_definitions.conf tmp/all_interfaces.conf tmp/all_attrs_types.conf $(GLOBALTUN) tmp/only_te_rules.conf tmp/all_post.conf

DOCS = doc
POLXML = $(DOCS)/policy.xml
XMLDTD = $(DOCS)/policy.dtd
LAYERXML = metadata.xml
HTMLDIR = $(DOCS)/html
DOCTEMPLATE = $(DOCS)/templates

########################################
#
# default action: build policy locally
#
default: policy

policy: $(POLVER)

install: $(LOADPATH) $(FCPATH) $(APPFILES) $(USERPATH)/local.users

load: tmp/load

########################################
#
# Build a binary policy locally
#
$(POLVER): policy.conf
	@echo "Compiling $(NAME) $(POLVER)"
ifneq ($(PV),$(KV))
	@echo
	@echo "WARNING: Policy version mismatch!  Is your OUTPUT_POLICY set correctly?"
	@echo
endif
	$(QUIET) $(CHECKPOLICY) $^ -o $@

########################################
#
# Install a binary policy
#
$(LOADPATH): policy.conf
	@mkdir -p $(POLICYPATH)
	@echo "Compiling and installing $(NAME) $(LOADPATH)"
ifneq ($(PV),$(KV))
	@echo
	@echo "WARNING: Policy version mismatch!  Is your OUTPUT_POLICY set correctly?"
	@echo
endif
	$(QUIET) $(CHECKPOLICY) $^ -o $@

########################################
#
# Load the binary policy
#
reload tmp/load: $(LOADPATH) $(FCPATH)
	@echo "Loading $(NAME) $(LOADPATH)"
	$(QUIET) $(LOADPOLICY) -q $(LOADPATH)
	@touch tmp/load

########################################
#
# Construct a monolithic policy.conf
#
policy.conf: $(POLICY_SECTIONS)
	@echo "Creating $(NAME) policy.conf"
# checkpolicy can use the #line directives provided by -s for error reporting:
	$(QUIET) m4 $(M4PARAM) -s $^ > tmp/$@.tmp
	$(QUIET) sed -e /^portcon/d -e /^nodecon/d -e /^netifcon/d < tmp/$@.tmp > $@
# the ordering of these ocontexts matters:
	$(QUIET) grep ^portcon tmp/$@.tmp >> $@ || true
	$(QUIET) grep ^netifcon tmp/$@.tmp >> $@ || true
	$(QUIET) grep ^nodecon tmp/$@.tmp >> $@ || true

tmp/pre_te_files.conf: $(PRE_TE_FILES)
	@test -d tmp || mkdir -p tmp
	$(QUIET) cat $^ > $@

tmp/generated_definitions.conf: $(ALL_LAYERS) $(ALL_TE_FILES)
# per-userdomain templates:
	@test -d tmp || mkdir -p tmp
	$(QUIET) echo "define(\`per_userdomain_templates',\`" > $@
	$(QUIET) for i in $(patsubst %.te,%,$(notdir $(ALL_MODULES))); do \
		echo "ifdef(\`""$$i""_per_userdomain_template',\`""$$i""_per_userdomain_template("'$$1'")')" \
			>> $@ ;\
	done
	$(QUIET) echo "')" >> $@
# define foo.te
	$(QUIET) for i in $(notdir $(ALL_MODULES)); do \
		echo "define(\`$$i')" >> $@ ;\
	done
	$(QUIET) $(SETTUN) $(TUNABLES) >> $@

tmp/all_interfaces.conf: $(M4SUPPORT) $(ALL_INTERFACES)
ifeq ($(ALL_INTERFACES),)
	$(error No enabled modules! $(notdir $(MOD_CONF)) may need to be generated by using "make conf")
endif
	@test -d tmp || mkdir -p tmp
	$(QUIET) m4 $^ | sed -e s/dollarsstar/\$$\*/g > $@

tmp/all_te_files.conf: $(ALL_TE_FILES)
ifeq ($(ALL_TE_FILES),)
	$(error No enabled modules! $(notdir $(MOD_CONF)) may need to be generated by using "make conf")
endif
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
	$(QUIET) grep '^sid ' tmp/all_te_files.conf >> tmp/all_post.conf || true
	$(QUIET) egrep '^fs_use_(xattr|task|trans)' tmp/all_te_files.conf >> tmp/all_post.conf || true
	$(QUIET) grep ^genfscon tmp/all_te_files.conf >> tmp/all_post.conf || true
	$(QUIET) sed -r -e /^attribute/d -e '/^type /d' -e /^genfscon/d \
			-e '/^sid /d' -e '/^fs_use_(xattr|task|trans)/d' \
			< tmp/all_te_files.conf > tmp/only_te_rules.conf

$(MODDIR)/kernel/corenetwork.if: $(MODDIR)/kernel/corenetwork.if.m4 $(MODDIR)/kernel/corenetwork.if.in
	@echo "#" > $@
	@echo "# This is a generated file!  Instead of modifying this file, the" >> $@
	@echo "# $(notdir $@).in or $(notdir $@).m4 file should be modified." >> $@
	@echo "#" >> $@
	$(QUIET) cat $(MODDIR)/kernel/corenetwork.if.in >> $@
	$(QUIET) egrep "^[[:blank:]]*network_(interface|node|port)\(.*\)" $(@:.if=.te).in \
		| m4 $(M4PARAM) $(M4SUPPORT) $(MODDIR)/kernel/corenetwork.if.m4 - \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@

$(MODDIR)/kernel/corenetwork.te: $(MODDIR)/kernel/corenetwork.te.m4 $(MODDIR)/kernel/corenetwork.te.in
	@echo "#" > $@
	@echo "# This is a generated file!  Instead of modifying this file, the" >> $@
	@echo "# $(notdir $@).in or $(notdir $@).m4 file should be modified." >> $@
	@echo "#" >> $@
	$(QUIET) m4 $(M4PARAM) $(M4SUPPORT) $^ \
		| sed -e 's/dollarsone/\$$1/g' -e 's/dollarszero/\$$0/g' >> $@

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
$(FC): $(M4SUPPORT) tmp/generated_definitions.conf $(ALL_FC_FILES) $(FCSORT) $(POLVER)
ifeq ($(ALL_FC_FILES),)
	$(error No enabled modules! $(notdir $(MOD_CONF)) may need to be generated by using "make conf")
endif
	@test -d tmp || mkdir -p tmp
	$(QUIET) m4 $(M4PARAM) $(M4SUPPORT) tmp/generated_definitions.conf $(ALL_FC_FILES) > tmp/$@.tmp
	$(QUIET) grep -e HOME -e ROLE tmp/$@.tmp > $(HOMEDIR_TEMPLATE)
	$(QUIET) sed -i -e /HOME/d -e /ROLE/d tmp/$@.tmp
	$(QUIET) $(FCSORT) tmp/$@.tmp $@
	@echo "Validating file_contexts."
	$(SETFILES) -q -c $(POLVER) $(FC)

########################################
#
# Install file_contexts
#
$(FCPATH): $(FC) $(USERPATH)/system.users
	@mkdir -p $(CONTEXTPATH)/files
	$(QUIET) install -m 644 $(FC) $(FCPATH)
	$(QUIET) install -m 644 $(HOMEDIR_TEMPLATE) $(HOMEDIRPATH)
	$(QUIET) $(GENHOMEDIRCON) -d $(TOPDIR) -t $(NAME) $(USEPWD)

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
	$(QUIET) m4 $(M4PARAM) tmp/generated_definitions.conf $(USER_FILES) | \
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
# Clean the sources
#
clean:
	rm -fR tmp
	rm -f policy.conf
	rm -f policy.$(PV)
	rm -f $(FC)

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

.PHONY: default policy install load reload enableaudit checklabels restorelabels relabel conf clean bare
