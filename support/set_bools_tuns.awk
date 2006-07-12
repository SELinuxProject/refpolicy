# Read booleans.conf and output M4 directives to
# override default settings in global_booleans

BEGIN {
	FS="="
}

/^[[:blank:]]*[[:alpha:]]+/{ 
	gsub(/[[:blank:]]*/,"")
	print "define(`"$1"_conf',`"$2"')"
}
