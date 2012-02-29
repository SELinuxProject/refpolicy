#n
# print out type, role and attribute declarations that
# are not inside require and optional blocks.

/require \{/,/} # end require/b nextline
/optional \{/,/} # end optional/b nextline

/^[[:blank:]]*(attribute(_role)?|type(alias)?|bool) /{
	s/^[[:blank:]]+//
	p
}

/^[[:blank:]]*role[[:blank:]]+[a-zA-Z_]+[[:blank:]]*;/{
	s/^[[:blank:]]+//
	p
}

:nextline
