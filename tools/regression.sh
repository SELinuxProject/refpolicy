#!/bin/bash

DISTROS="redhat gentoo debian suse"
STRICT_TYPES="strict strict-mls"
TARG_TYPES="targeted targeted-mls"
POLVER="`checkpolicy -V |cut -f 1 -d ' '`"
SETFILES="/usr/sbin/setfiles"

do_test() {
	local OPTS=""

	for i in $STRICT_TYPES; do
		OPTS="TYPE=$i QUIET=@"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		make bare || exit 1
		echo "**** Options: $OPTS ****"
		make $OPTS conf || exit 1
		make $OPTS || exit 1
		make $OPTS file_contexts || exit 1
		$SETFILES -q -c policy.$POLVER file_contexts || exit 1
	done

	# need a specific config for targeted policy
	for i in $TARG_TYPES; do
		OPTS="TYPE=$i QUIET=@"
		[ ! -z "$1" ] && OPTS="$OPTS DISTRO=$1"
		make bare || exit 1
		echo "**** Options: $OPTS ****"
		cp policy/modules.conf.targeted_example policy/modules.conf
		make $OPTS conf || exit 1
		make $OPTS || exit 1
		make $OPTS file_contexts || exit 1
		$SETFILES -q -c policy.$POLVER file_contexts|| exit 1
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
