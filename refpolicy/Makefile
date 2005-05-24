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

# Build compatibility policies 
POLICYCOMPAT = -c 18

# set distribution
#override M4PARAM += -D distro_redhat

# Uncomment this to disable command echoing
#QUIET:=@

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

# determine the policy version and current kernel version if possible
PV := $(shell $(CHECKPOLICY) $(POLICYCOMPAT) -V |cut -f 1 -d ' ')
KV := $(shell cat /selinux/policyvers)

# dont print version warnings if we are unable to determine
# the currently running kernel's policy version
ifeq ($(KV),)
KV := $(PV)
endif

FC := file_contexts
POLVER := policy.$(PV)
TYPE := strict

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
FLASKDIR = $(BASE_MODULE)/flask/
MISCDIR = $(BASE_MODULE)/misc/

DETECTED_DIRS := $(shell find $(wildcard *) -maxdepth 0 -type d)
ALL_MODULES := $(filter-out tmp appconfig,$(DETECTED_DIRS))

PRE_TE_FILES := $(addprefix $(FLASKDIR),security_classes initial_sids access_vectors)
ALL_INTERFACES := $(foreach dir,$(ALL_MODULES),$(wildcard $(dir)/*.if))
ALL_TE_FILES := $(foreach dir,$(ALL_MODULES),$(wildcard $(dir)/*.te))
POST_TE_FILES := $(addprefix $(MISCDIR),users constraints mls initial_sid_contexts fs_use)

ALL_FC_FILES := $(foreach dir,$(ALL_MODULES),$(wildcard $(dir)/*.fc))

POLICY_SECTIONS := tmp/pre_te_files.conf tmp/generated_definitions.conf tmp/all_interfaces.conf tmp/all_attrs_types.conf tmp/only_te_rules.conf tmp/all_post.conf

override M4PARAM += -D monolithic_policy

########################################
#
# default action: build policy locally
#
default: policy

policy: $(POLVER)

install: $(LOADPATH)

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
	$(QUIET) $(CHECKPOLICY) $(POLICYCOMPAT) $^ -o $@

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
	$(QUIET) $(CHECKPOLICY) $(POLICYCOMPAT) $^ -o $@

########################################
#
# Load the binary policy
#
reload tmp/load: $(LOADPATH) $(FCPATH)
	@echo "Loading $(LOADPATH)"
	$(QUIET) $(LOADPOLICY) -q $(LOADPATH)
	@touch tmp/load

load: tmp/load

########################################
#
# Construct a monolithic policy.conf
#
policy.conf: $(POLICY_SECTIONS)
	@echo "Creating policy.conf"
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

tmp/generated_definitions.conf: $(ALL_MODULES) $(ALL_TE_FILES) $(BASE_MODULE)/corenetwork.if $(BASE_MODULE)/corenetwork.te
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
	$(QUIET) grep -E "^network_(interface|node|port)\(.*\)" $(BASE_MODULE)/corenetwork.te \
		| m4 $(M4PARAM) -D interface_pass $(BASE_MODULE)/global.if $(BASE_MODULE)/corenetwork.if - \
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
$(FCPATH): $(FC)
#$(FCPATH): $(FC) $(USERPATH)/system.users 
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
	$(QUIET) echo "<policy>" > $@
	$(QUIET) grep -h -E "^##[[:space:]]" $^ | sed -e 's/^##[[:space:]]//g' >> $@
	$(QUIET) echo "</policy>" >> $@

clean:
	rm -fR tmp
	rm -f policy.xml
	rm -f policy.conf
	rm -f policy.$(PV)
	rm -f $(FC)

.PHONY: default policy install reload enableaudit checklabels restorelabels relabel xml clean
