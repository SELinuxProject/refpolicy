#n
# print out type and attribute declarations that
# are not inside require blocks.

/require \{/,/} # end require/b nextline

/^[[:blank:]]*(attribute|type(alias)?) /{
	s/^[[:blank:]]+//
	p
}

:nextline
