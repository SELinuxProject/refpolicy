#! /bin/sh

# This will 'publish' the reference policy website.

rsync -r . shell.sf.net:/home/groups/s/se/serefpolicy/htdocs
