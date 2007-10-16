PYTHON ?= python

# flask needs to know where to export the libselinux headers.
LIBSELINUX_D ?= ../../libselinux

# flask needs to know where to export the kernel headers.
LINUX_D ?= ../../../linux-2.6

ACCESS_VECTORS_F = access_vectors
INITIAL_SIDS_F = initial_sids
SECURITY_CLASSES_F = security_classes

USER_D = userspace
KERN_D = kernel

LIBSELINUX_INCLUDE_H = flask.h av_permissions.h
LIBSELINUX_SOURCE_H = class_to_string.h av_inherit.h common_perm_to_string.h av_perm_to_string.h

FLASK_H = class_to_string.h flask.h initial_sid_to_string.h
ACCESS_VECTORS_H = av_inherit.h common_perm_to_string.h av_perm_to_string.h av_permissions.h
ALL_H = $(FLASK_H) $(ACCESS_VECTORS_H)

USER_H = $(addprefix $(USER_D)/, $(ALL_H))
KERN_H = $(addprefix $(KERN_D)/, $(ALL_H))

FLASK_NOWARNINGS = --nowarnings

all:  $(USER_H) $(KERN_H)

$(USER_H): flask.py $(ACCESS_VECTORS_F) $(INITIAL_SIDS_F) $(SECURITY_CLASSES_F)
	mkdir -p $(USER_D)
	$(PYTHON) flask.py -a $(ACCESS_VECTORS_F) -i $(INITIAL_SIDS_F) -s $(SECURITY_CLASSES_F) -o $(USER_D) -u $(FLASK_NOWARNINGS)

$(KERN_H): flask.py $(ACCESS_VECTORS_F) $(INITIAL_SIDS_F) $(SECURITY_CLASSES_F)
	mkdir -p $(KERN_D) 
	$(PYTHON) flask.py -a $(ACCESS_VECTORS_F) -i $(INITIAL_SIDS_F) -s $(SECURITY_CLASSES_F) -o $(KERN_D) -k $(FLASK_NOWARNINGS)

tolib: all
	install -m 644 $(addprefix $(USER_D)/, $(LIBSELINUX_INCLUDE_H)) $(LIBSELINUX_D)/include/selinux
	install -m 644 $(addprefix $(USER_D)/, $(LIBSELINUX_SOURCE_H)) $(LIBSELINUX_D)/src

tokern: all
	install -m 644 $(KERN_H) $(LINUX_D)/security/selinux/include

install: all

relabel:

clean:  
	rm -fr userspace
	rm -fr kernel
