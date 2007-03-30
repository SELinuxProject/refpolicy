#n
# print out type and attribute declarations that
# are not inside require and optional blocks.

/require \{/,/} # end require/b nextline
/optional \{/,/} # end optional/b nextline

/^[[:blank:]]*(attribute|type(alias)?|bool) /{
	s/^[[:blank:]]+//
	p
}

:nextline
