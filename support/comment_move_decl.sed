# comment out lines that are moved by the build
# process, so line numbers provided by m4 are preserved.

# lines in require and optional blocks are not moved
/require \{/,/} # end require/b nextline
/optional \{/,/} # end optional/b nextline

/^[[:blank:]]*(attribute|type(alias)?) /s/^/# this line was moved by the build process: &/
/^[[:blank:]]*(port|node|netif|genfs)con /s/^/# this line was moved by the build process: &/
/^[[:blank:]]*fs_use_(xattr|task|trans) /s/^/# this line was moved by the build process: &/
/^[[:blank:]]*sid /s/^/# this line was moved by the build process: &/
/^[[:blank:]]*bool /s/^/# this line was moved by the build process: &/

:nextline
