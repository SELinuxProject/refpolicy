#!/usr/bin/env python3

#  Author(s): Donald Miner <dminer@tresys.com>
#        Dave Sugar <dsugar@tresys.com>
#        Brian Williams <bwilliams@tresys.com>
#        Caleb Case <ccase@tresys.com>
#
# Copyright (C) 2005 - 2006 Tresys Technology, LLC
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 2.

"""
    This script generates XML documentation information for layers specified
    by the user.
"""

import sys
import re
import logging
import argparse
import xml.etree.ElementTree as ET
from itertools import dropwhile
from pathlib import Path


# Pre compiled regular expressions:

# Matches either an interface or a template declaration. Will give the tuple:
#   ("interface" or "template", name)
# Some examples:
#   "interface(`kernel_read_system_state',`"
#    -> ("interface", "kernel_read_system_state")
#   "template(`base_user_template',`"
#    -> ("template", "base_user_template")
INTERFACE = re.compile(r"^\s*(interface|template)\(`(\w*)'")

# Matches either a gen_bool or a gen_tunable statement. Will give the tuple:
#   ("tunable" or "bool", name, "true" or "false")
# Some examples:
#   "gen_bool(secure_mode, false)"
#    -> ("bool", "secure_mode", "false")
#   "gen_tunable(allow_kerberos, false)"
#    -> ("tunable", "allow_kerberos", "false")
BOOLEAN = re.compile(r"^\s*gen_(tunable|bool)\(\s*\`?\s*(\w*)\s*\'?\s*,\s*(true|false)\s*\)")
TEMPLATE_BOOLEAN = re.compile(
    r"^\s*gen_(tunable|bool)\(\s*\`?\s*([\w\$]*)\s*\'?\s*,\s*(true|false)\s*\)")

# Matches a XML comment in the policy, which is defined as any line starting
#  with two # and at least one character of white space. Will give the single
#  valued tuple:
#   ("comment")
# Some Examples:
#   "## <summary>"
#    -> ("<summary>")
#   "##     The domain allowed access.  "
#    -> ("The domain allowed access.")
XML_COMMENT = re.compile(r"^\s*##\s+(.*?)\s*$")

# Matches a template call in the policy, which is defined as any line having
#  a function call like structure, being a string, followed by a set of
#  arguments between an opening and closing bracket. Regexp cannot deal with
#  unknown number of arguments, so we will split arguments in the code later on.
# Some examples:
#   "userdom_user_access_template(gpg, gpg_t)"
#   "zarafa_domain_template(gateway)"
TEMPLATE_CALL = re.compile(r"^\s*(\w*_template)\(\s*(\w*)\s*(?:,\s*(?:[^,)]*)\s*)*\)")


# FUNCTIONS
def _parse_xml_fragments(fragments: list[str], parent: ET.Element,
                         file_name: str, line_num: int = 0) -> None:
    '''
    Parse collected XML comment lines and append as children of parent.
    '''
    try:
        root = ET.fromstring("<_root>" + "".join(fragments) + "</_root>")
        parent.extend(root)

    except ET.ParseError as err:
        location = f"{file_name}:{line_num}" if line_num else file_name
        raise ValueError(f"{location}: failed to parse XML:\n"
                         f"{''.join(fragments)}") from err


def get_module_xml(module_te: Path, templatedir: str) -> tuple[list[ET.Element], int]:
    '''
    Returns a list containing the XML Element for a module, or an empty list on failure.
    '''

    module_if = module_te.with_suffix(".if")

    warn_count = 0

    # Try to open the file, if it can't, just ignore it.
    try:
        with open(module_if, "r", encoding="utf-8") as module_file:
            module_code = module_file.readlines()
    except OSError:
        logging.warning(f"cannot open file {module_if} for read, skipping")
        return [], 1

    module_elem = ET.Element("module", name=module_te.stem, filename=str(module_if))

    temp_buf: list[str] = []
    interface = None

    # finding_header is a flag to denote whether we are still looking
    #  for the XML documentation at the head of the file.
    finding_header = True

    # Get rid of whitespace at top of file
    module_code = list(dropwhile(str.isspace, module_code))

    # Go line by line and figure out what to do with it.
    for line_num, line in enumerate(module_code, start=1):
        if finding_header:
            # If there is a XML comment, add it to the temp buffer.
            if comment := XML_COMMENT.match(line):
                temp_buf.append(comment.group(1) + "\n")
                continue

            # Once a line that is not an XML comment is reached,
            #  either put the XML out to module buffer as the
            #  module's documentation, or attribute it to an
            #  interface/template.
            elif temp_buf:
                finding_header = False
                interface = INTERFACE.match(line)
                if not interface:
                    _parse_xml_fragments(temp_buf, module_elem,
                                         str(module_if), line_num)
                    temp_buf = []
                    continue

        # Skip over empty lines
        if line.isspace():
            continue

        # Grab a comment and add it to the temporary buffer, if it
        #  is there.
        if comment := XML_COMMENT.match(line):
            temp_buf.append(comment.group(1) + "\n")
            continue

        # Grab the interface information. This is only not true when
        #  the interface is at the top of the file and there is no
        #  documentation for the module.
        if not interface:
            interface = INTERFACE.match(line)
        if interface:
            groups = interface.groups()
            iface_elem = ET.SubElement(module_elem, groups[0],
                                       name=groups[1], lineno=str(line_num))

            # Add all the comments attributed to this interface.
            if temp_buf:
                _parse_xml_fragments(temp_buf, iface_elem,
                                     str(module_if), line_num)
                temp_buf = []

            # Add default summaries and parameters so that the
            #  DTD is happy.
            else:
                logging.warning(f"unable to find XML for {groups[0]} {groups[1]}()")
                warn_count += 1
                ET.SubElement(iface_elem, "summary").text = "Summary is missing!"
                param = ET.SubElement(iface_elem, "param", name="?")
                ET.SubElement(param, "summary").text = "Parameter descriptions are missing!"

            interface = None
            continue

        # If the line is a boolean/tunable definition, ignore it for now (these
        #  lines are processed later on) and dismiss the XML comment received
        #  thus far as it is otherwise attributed to an interface.
        if TEMPLATE_BOOLEAN.match(line):
            temp_buf = []
            continue

    # If the file just had a header, add the comments to the module buffer.
    if finding_header:
        if temp_buf:
            _parse_xml_fragments(temp_buf, module_elem, str(module_if))
    # Otherwise there are some lingering XML comments at the bottom, warn
    #  the user.
    elif temp_buf:
        logging.warning(f"orphan XML comments at bottom of file {module_if}:")
        sys.stderr.write(f">  {'>  '.join(temp_buf)}\n")
        warn_count += 1

    # Process the TE file if it exists.
    te_elems, te_warns = get_tunable_xml(str(module_te), "both", templatedir)
    module_elem.extend(te_elems)
    warn_count += te_warns

    return [module_elem], warn_count


def get_layer_xml(dir_name: str, templatedir: str) -> tuple[list[ET.Element], int]:
    '''
    Return the XML element for a layer and all modules found in it.
    '''

    layer_dir = Path(dir_name)
    if not layer_dir.is_dir():
        raise ValueError(f"{dir_name}: not a layer directory")

    layer_name = layer_dir.name or layer_dir.absolute().name
    layer_elem = ET.Element("layer", name=layer_name)
    warn_count = 0

    metadata_file = layer_dir / "metadata.xml"
    try:
        with open(metadata_file, "r", encoding="utf-8") as metadata:
            _parse_xml_fragments(metadata.readlines(), layer_elem,
                                 str(metadata_file))
    except OSError:
        logging.warning(f"cannot open file {metadata_file} for read")
        warn_count += 1
        ET.SubElement(layer_elem, "summary").text = "Summary is missing!"

    module_files = sorted(layer_dir.glob("*.te"))
    if not module_files:
        raise ValueError(f"{dir_name}: no module .te files found")

    for module_te in module_files:
        module_xml, module_warns = get_module_xml(module_te, templatedir)
        layer_elem.extend(module_xml)
        warn_count += module_warns

    return [layer_elem], warn_count


def _read_policy(file_name: str) -> ET.Element:
    '''
    Read a policy XML document from a file.
    '''

    try:
        root = ET.parse(file_name).getroot()
    except OSError as err:
        raise ValueError(f"cannot open file {file_name} for read") from err
    except ET.ParseError as err:
        raise ValueError(f"{file_name}: failed to parse XML") from err

    if root.tag != "policy":
        raise ValueError(f"{file_name}: expected policy XML")

    return root


def get_policy_xml(layer_dirs: list[str], policy_files: list[str], tunable_file: str,
                   boolean_file: str, templatedir: str) -> tuple[ET.Element, int]:
    '''
    Return a complete policy element from source directories and XML inputs.
    '''

    policy_elem = ET.Element("policy")
    warn_count = 0
    global_elems: list[ET.Element] = []

    for policy_file in policy_files:
        for xml_elem in _read_policy(policy_file):
            if xml_elem.tag == "layer":
                policy_elem.append(xml_elem)
            else:
                global_elems.append(xml_elem)

    for layer_dir in layer_dirs:
        layer_xml, layer_warns = get_layer_xml(layer_dir, templatedir)
        policy_elem.extend(layer_xml)
        warn_count += layer_warns

    if not policy_elem.findall("layer"):
        raise ValueError("policy requires at least one layer")

    policy_elem.extend(global_elems)

    if tunable_file:
        tunable_xml, tunable_warns = get_tunable_xml(tunable_file, "tunable", templatedir)
        policy_elem.extend(tunable_xml)
        warn_count += tunable_warns

    if boolean_file:
        boolean_xml, boolean_warns = get_tunable_xml(boolean_file, "bool", templatedir)
        policy_elem.extend(boolean_xml)
        warn_count += boolean_warns

    for summary_elem in policy_elem.iter("summary"):
        assert summary_elem.text is not None, "summary element text should not be None. segenxml.py bug."
        summary_elem.text = re.sub(r"\s+", " ", summary_elem.text).strip()

    return policy_elem, warn_count


def get_tunable_xml(file_name: str, kind: str, templatedir: str) -> tuple[list[ET.Element], int]:
    '''
    Return all the XML elements for the tunables/bools in the file specified.
    '''

    warn_count = 0

    # Try to open the file, if it can't, just ignore it.
    try:
        with open(file_name, "r", encoding="utf-8") as tunable_file:
            tunable_code = tunable_file.readlines()
    except OSError:
        logging.warning(f"cannot open file {file_name} for read, skipping")
        return [], 1

    tunable_elems: list[ET.Element] = []
    temp_buf: list[str] = []
    tunable_processed_code: list[str] = []

    # We first go through the code and substitute template calls with the
    #  complete template content. This needs to happen iteratively, because
    #  a template can call another template. In order to ensure no cyclic
    #  template calls keep us busy, we max out at 9999 substitutions
    has_changed = True
    subst_threshold = 9999
    while has_changed and subst_threshold > 0:
        has_changed = False
        for line in tunable_code:
            # Get the template call match
            if template_call := TEMPLATE_CALL.match(line):
                # Read template file based on template_call.group(1)
                filename = f"{templatedir}/{template_call.group(1)}.iftemplate"
                try:
                    with open(filename, "r", encoding="utf-8") as template_file:
                        template_code = template_file.readlines()
                except OSError:
                    logging.warning(f"cannot open file {filename}.  Ignoring.")
                    # Do not increase the warning count here, because this is an
                    # optional file.
                    return [], warn_count
                # Substitute content (i.e. $1 for argument 1, $2 for argument 2, etc.)
                template_split = re.findall(r"[\w\" {}]+", line.strip())
                for index, _ in enumerate(template_code):
                    for g in range(1, len(template_split)):
                        template_code[index] = template_code[index].replace(
                            f"${g}", template_split[g].strip())
                # Now 'inject' the code in the tunable_code variable
                tunable_processed_code.extend(template_code)
                has_changed = True
                subst_threshold -= 1
            else:
                tunable_processed_code.append(line)
        # It is a bad practice to try and update lists while in a loop, so we
        # created an intermediate one and are now assigning it back
        tunable_code = tunable_processed_code
        tunable_processed_code = []
    # If subst_threshold is 0 or less we want to know
    if subst_threshold <= 0:
        logging.warning("Detected a possible loop in policy code and template usage")
        warn_count += 1

    # Find tunables and booleans line by line and use the comments above
    # them.
    for line in tunable_code:
        # If it is an XML comment, add it to the buffer and go on.
        if comment := XML_COMMENT.match(line):
            temp_buf.append(comment.group(1) + "\n")
            continue

        # Get the boolean/tunable data.
        if boolean := BOOLEAN.match(line):
            # If we reach a boolean/tunable declaration, attribute all XML
            #  in the temp buffer to it and add XML to the tunable buffer.
            # If there is a gen_bool in a tunable file or a
            # gen_tunable in a boolean file, error and exit.
            # Skip if both kinds are valid.
            if kind != "both":
                if boolean.group(1) != kind:
                    raise ValueError(f"{boolean.group(1)} in a {kind} file.")

            tun_elem = ET.Element(boolean.group(1),
                                  name=boolean.group(2),
                                  dftval=boolean.group(3))
            if temp_buf:
                _parse_xml_fragments(temp_buf, tun_elem, file_name)
                temp_buf = []
            tunable_elems.append(tun_elem)

    # If there are XML comments at the end of the file, they aren't
    # attributed to anything. These are ignored.
    if temp_buf:
        logging.warning(f"orphan XML comments at bottom of file {file_name}")
        sys.stderr.write(f">  {'>  '.join(temp_buf)}\n")
        warn_count += 1

    return tunable_elems, warn_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate policy XML documentation.",
        epilog="examples:\n"
            "  %(prog)s -w -T tmp/templates -t policy/global_tunables "
            "-b policy/global_booleans -o policy.xml policy/modules/*\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-w', '--warn', action='store_true',
        help='show warnings')
    parser.add_argument('-W', '--Werror', action='store_true',
        help='treat warnings as errors')
    parser.add_argument('-t', '--tunable', default='', metavar='FILE',
        help='global tunable source file')
    parser.add_argument('-b', '--boolean', default='', metavar='FILE',
        help='global boolean source file')
    parser.add_argument('-T', '--templates', default='', dest='templatedir',
        help='name of template directory to use')
    parser.add_argument('-o', '--output', required=True,
        help='output file')
    parser.add_argument('--policy-file', action='append', default=[], metavar='FILE',
        help='include layers and globals from an existing policy XML file')
    parser.add_argument('files', nargs='*', metavar='PATH',
        help='layer directories to process')

    args = parser.parse_args()

    if not args.files and not args.policy_file:
        parser.error("at least 1 layer directory or --policy-file is required")

    logging.basicConfig(format=sys.argv[0] + ': %(levelname)s: %(message)s',
        level=logging.WARNING if args.warn or args.Werror else logging.ERROR)

    try:
        policy_element, warnings = get_policy_xml(
            args.files, args.policy_file, args.tunable,
            args.boolean, args.templatedir)

        if args.Werror and warnings:
            raise RuntimeError(f"{sys.argv[0]}: ERROR: Treating warnings as errors.\n")

        ET.indent(policy_element)
        tree = ET.ElementTree(policy_element)
        with open(args.output, "wb") as binary_output:
            binary_output.write(
                b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
                b'<!DOCTYPE policy SYSTEM "policy.dtd">\n')
            tree.write(binary_output, encoding="UTF-8",
                       xml_declaration=False, short_empty_elements=True)
            binary_output.write(b"\n")

    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
