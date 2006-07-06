#!/bin/bash

DISTROS="rhel4 gentoo debian"
TYPES="strict targeted strict-mcs targeted-mcs strict-mls targeted-mls"
POLVER="`checkpolicy -V |cut -f 1 -d ' '`"
SETFILES="/usr/sbin/setfiles"
SE_LINK="time -p /usr/bin/semodule_link"

die() {
	if [ "$1" -eq "1" ]; then
		echo "failed with options: $2"
	fi

	exit 1
}

cleanup_mon() {
	make MONOLITHIC=y bare
}

cleanup_mod() {
	make MONOLITHIC=n bare
}

do_test() {
	local OPTS=""

	for i in $TYPES; do
		# Monolithic tests
		trap cleanup_mon SIGINT SIGQUIT
		OPTS="TYPE=$i MONOLITHIC=y QUIET=y DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		echo "**** Options: $OPTS ****"
		echo -ne "\33]0;mon $i $1\007"
		make $OPTS conf || die "$?" "$OPTS"
		make $OPTS || die "$?" "$OPTS"
		make $OPTS file_contexts || die "$?" "$OPTS"
		$SETFILES -q -c policy.$POLVER file_contexts || die "$?" "$OPTS"
		cleanup_mon

		# Loadable module tests
		trap cleanup_mod SIGINT SIGQUIT
		OPTS="TYPE=$i MONOLITHIC=n QUIET=y DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		echo "**** Options: $OPTS ****"
		echo -ne "\33]0;mod $i $1\007"
		make $OPTS conf || die "$?" "$OPTS"
		make $OPTS base || die "$?" "$OPTS"
		make $OPTS -j2 modules || die "$?" "$OPTS"
		make $OPTS validate || die "$?" "$OPTS"
		cleanup_mod
	done
}

cleanup_mon
cleanup_mod
do_test

for i in $DISTROS; do
	do_test $i
done

echo "Completed successfully."
