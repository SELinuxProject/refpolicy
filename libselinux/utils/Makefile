# Installation directories.
PREFIX ?= $(DESTDIR)/usr
BINDIR ?= $(PREFIX)/sbin

CFLAGS ?= -Wall
override CFLAGS += -I../include -D_GNU_SOURCE
LDLIBS += -L../src -lselinux 

TARGETS=$(patsubst %.c,%,$(wildcard *.c))

all: $(TARGETS)

install: all
	-mkdir -p $(BINDIR)
	install -m 755 $(TARGETS) $(BINDIR)

clean:
	rm -f $(TARGETS) *.o 

relabel:

