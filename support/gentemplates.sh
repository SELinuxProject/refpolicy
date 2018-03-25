#!/bin/sh

showHelp() {
  echo "Usage: $(basename $0) --generate --sourcedir=<sourcedir> --targetdir=<targetdir>"
  echo "       $(basename $0) -g -s <sourcedir> -t <targetdir>"
  echo "";
  echo "The $(basename $0) script will fetch all template definitions from the interface files"
  echo "located in the selected source directory, and write one file per template into the"
  echo "target directory."
  echo "";
  echo "Supported options:"
  echo "  --generate (-g)	Generate template files"
  echo "  --sourcedir=<sourcedir> (-s <sourcedir>)"
  echo "			Source directory to recursively search for interfaces/templates"
  echo "  --targetdir=<targetdir> (-t <targetdir>)"
  echo "			Target directory to store template definitions in"
}

flagGenerate=0;
SOURCEDIR="";
TARGETDIR="";

params=$(getopt -n $(basename $0) -s sh -o gs:t: --long generate,sourcedir:,targetdir: -- "$@")
if [ $? -ne 0 ] ; then
  showHelp;
  exit 1;
fi

eval set -- "${params}"
while [ $# -gt 0 ] ; do
  case "$1" in
    (-g) flagGenerate=1;;
    (-s) SOURCEDIR="$2"; shift;;
    (-t) TARGETDIR="$2"; shift;;
    (--) break;;
    (-*) echo "$(basename $0): error: Unrecognized option $1" 1>&2; exit 1;;
    (*) break;;
  esac
  shift;
done

if [ ${flagGenerate} -ne 1 ] || [ -z "${SOURCEDIR}" ] || [ -z "${TARGETDIR}" ] ; then
  showHelp;
  exit 1;
fi

if [ ! -d "${SOURCEDIR}" ] ; then
  echo "Directory ${SOURCEDIR} does not exist"
  exit 2;
fi

if [ ! -d "${TARGETDIR}" ] ; then
  echo "Directory ${TARGETDIR} does not exist"
  exit 3;
fi

for ifile in $(find ${SOURCEDIR} -type f -name '*.if'); do
  for interface in $(grep -E '^template\(' ${ifile} | sed -e 's:^template(`\([^'\'']*\)'\''\s*,\s*`:\1:g'); do
    # Generate the interface
    sed -n "/^template(\`${interface}',\`/,/^')/p" ${ifile} | grep -v "^template" | grep -v "^')" > ${TARGETDIR}/${interface}.iftemplate;
  done
done
