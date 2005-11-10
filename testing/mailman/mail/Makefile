# These could be used by sendmail, but are not part of the default install.
# To use them you will have to generate your own sendmail.cf with
#  FEATURE('whatever')
#
POSSIBLE += $(shell test -f bitdomain     && echo bitdomain.db)
POSSIBLE += $(shell test -f uudomain      && echo uudomain.db)
POSSIBLE += $(shell test -f genericstable && echo genericstable.db)
POSSIBLE += $(shell test -f userdb	  && echo userdb.db)
POSSIBLE += $(shell test -f authinfo      && echo authinfo.db)
CFFILES   = sendmail.cf submit.cf


all: ${CFFILES} ${POSSIBLE} virtusertable.db access.db domaintable.db mailertable.db

userdb.db: userdb
	@makemap btree $@ < $<

%.db: %
	@makemap hash $@ < $<

%.cf: %.mc
	@if test -f /usr/share/sendmail-cf/m4/cf.m4; then \
		umask 022; \
		mv -f $@ $@.bak; \
		m4 $< > $@; \
	else \
		echo -e "WARNING: '$<' is modified. Please install package sendmail-cf to update your configuration."; \
	fi

clean:
	rm -f *.db *~

start:
	service sendmail start

stop:
	service sendmail stop

restart:
	service sendmail restart

