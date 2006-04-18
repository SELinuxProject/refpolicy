#!/bin/bash

TYPES="strict targeted-mcs strict-mls"
POLVER="`checkpolicy -V |cut -f 1 -d ' '`"
SETFILES="/usr/sbin/setfiles"
SE_LINK="/usr/bin/semodule_link"

die() {
	if [ "$1" -eq "1" ]; then
		echo "failed with options: $2"
	fi

	exit 1
}

cleanup() {
	make bare
	make MONOLITHIC=n bare
}

do_test() {
	local OPTS=""

	trap cleanup SIGINT SIGQUIT

	for i in $TYPES; do
		# Monolithic tests
		OPTS="TYPE=$i MONOLITHIC=y QUIET=y DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		echo "**** Options: $OPTS ****"
		echo -ne "\33]0;mon $i $1\007"
		make $OPTS conf || die "$?" "$OPTS"
		make $OPTS || die "$?" "$OPTS"
		make $OPTS file_contexts || die "$?" "$OPTS"
		$SETFILES -q -c policy.$POLVER file_contexts || die "$?" "$OPTS"
		make $OPTS bare || die "$?" "$OPTS"

		# Loadable module tests
		OPTS="TYPE=$i MONOLITHIC=n QUIET=y DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		echo "**** Options: $OPTS ****"
		echo -ne "\33]0;mod $i $1\007"
		make $OPTS conf || die "$?" "$OPTS"
		make $OPTS base || die "$?" "$OPTS"
		make $OPTS -j2 modules || die "$?" "$OPTS"
		mv base.pp tmp
		############# FIXME
		rm dmesg.pp
		$SE_LINK tmp/base.pp *.pp || die "$?" "$OPTS"
		make $OPTS bare || die "$?" "$OPTS"
	done
}

cleanup
do_test

echo "Completed successfully."
