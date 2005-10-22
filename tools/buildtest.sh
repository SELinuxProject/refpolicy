#!/bin/bash

#DISTROS="redhat gentoo debian suse"
DISTROS="redhat"
TYPES="strict strict-mls strict-mcs targeted targeted-mls targeted-mcs"
POLVER="`checkpolicy -V |cut -f 1 -d ' '`"
SETFILES="/usr/sbin/setfiles"
SE_LINK="/usr/bin/semodule_link"

do_test() {
	local OPTS=""

	for i in $TYPES; do
		# Monolithic tests
		OPTS="TYPE=$i QUIET=@ DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		echo "**** Options: $OPTS ****"
		make $OPTS conf || exit 1
		make $OPTS || exit 1
		make $OPTS file_contexts || exit 1
		$SETFILES -q -c policy.$POLVER file_contexts || exit 1
		make $OPTS bare || exit 1

		# Loadable module tests
		OPTS="TYPE=$i MONOLITHIC=n QUIET=@ DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		echo "**** Options: $OPTS ****"
		make $OPTS conf || exit 1
		make $OPTS all || exit 1
		mv base.pp tmp
		$SE_LINK tmp/base.pp *.pp || exit 1
		make $OPTS bare || exit 1
	done
}

make bare || exit 1
make MONOLITHIC=n bare || exit 1

do_test

for i in $DISTROS; do
	do_test $i
done

echo "Completed successfully."
