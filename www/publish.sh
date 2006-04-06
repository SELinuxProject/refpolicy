#! /bin/sh

# This will 'publish' the reference policy website.

#cp ../refpolicy/Changelog html/Changelog.txt
rsync -rv --exclude .svn . shell.sf.net:/home/groups/s/se/serefpolicy/htdocs
