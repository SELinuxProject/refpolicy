#!/bin/bash

DISTROS="redhat gentoo debian suse"
TYPES="strict strict-mls strict-mcs targeted targeted-mls targeted-mcs"
POLVER="`checkpolicy -V |cut -f 1 -d ' '`"
SETFILES="/usr/sbin/setfiles"

do_test() {
	local OPTS=""

	for i in $TYPES; do
		OPTS="TYPE=$i QUIET=y DIRECT_INITRC=y"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		make bare || exit 1
		echo "**** Options: $OPTS ****"
		echo -ne "\33]0;$i $1\007"
		make $OPTS conf || exit 1
		make $OPTS || exit 1
		make $OPTS file_contexts || exit 1
		$SETFILES -q -c policy.$POLVER file_contexts || exit 1
	done
}

# first to generic test
do_test

# now distro-specitic test
for i in $DISTROS; do
	do_test $i
done

# clean up
make bare
echo "Completed successfully."
