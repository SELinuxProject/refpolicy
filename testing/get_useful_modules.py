#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
# Copyright (C) 2014-2019 Nicolas Iooss
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
"""
Parse .fc files and find those which may be useful, considering the installed
software.

The result is quite inaccurate and does not handle module dependencies, but it
may help admins who have already chosen some modules and are wondering whether
other modules are be needed to correctly label the files.

@author: Nicolas Iooss
@license: GPLv2
"""
import argparse
import glob
import os.path
from pathlib import Path
import subprocess
import sys


# Types used for nodes of the custom syntax tree of .fc patterns
NODE_TEXT = 't'  # Raw text, without special symbols
NODE_DOT = '.'  # Any character
NODE_CHARSET = '['  # A set of characters
NODE_CHARSET_COMP = '[^'  # The complement of a set of characters
NODE_QUESTION = '?'  # Zero or one appearance of the children nodes
NODE_PLUS = '+'  # At least one appearance of the children nodes
NODE_STAR = '*'  # Maybe repeated appearances of the children nodes
NODE_OR = '|'  # A choice between children nodes
NODE_PAREN = '('  # A parenthesed expression


REPEATING_SYMBOLS = {
    '?': NODE_QUESTION,
    '+': NODE_PLUS,
    '*': NODE_STAR,
}


class FilePatternParserError(Exception):
    """Error in a .fc file.

    This exception is raised with only a message, and the buggy pattern gets
    automatically added when it bubbles up.
    """

    def __init__(self, message):
        super(FilePatternParserError, self).__init__()
        self.message = message
        self.pattern = None


class FcTreeNode:
    """A node in a tree created from a .fc pattern"""
    def __init__(self, node_type):
        self.node_type = node_type


class FcNodeText(FcTreeNode):
    """A FcTreeNode holding text"""
    def __init__(self, text):
        super().__init__(NODE_TEXT)
        self.text = text

    def __hash__(self):
        return hash((self.node_type, self.text))

    def __eq__(self, other):
        return self.node_type == other.node_type and self.text == other.text

    def __repr__(self):
        return 'FcNodeText({})'.format(repr(self.text))


class FcNodeDot(FcTreeNode):
    """A FcTreeNode holding a dot (for any character)"""
    def __init__(self):
        super().__init__(NODE_DOT)

    def __hash__(self):
        return hash(self.node_type)

    def __eq__(self, other):
        return self.node_type == other.node_type

    def __repr__(self):
        return 'FcNodeDot()'


class FcNodeCharset(FcTreeNode):
    """A FcTreeNode for a set of characters"""
    def __init__(self, charset):
        super().__init__(NODE_CHARSET)
        self.charset = charset

    def __hash__(self):
        return hash((self.node_type, self.charset))

    def __eq__(self, other):
        return self.node_type == other.node_type and self.charset == other.charset

    def __repr__(self):
        return 'FcNodeCharset({})'.format(repr(self.charset))


class FcNodeCompCharset(FcTreeNode):
    """A FcTreeNode for the complementary of a set of characters"""
    def __init__(self, comp_charset):
        super().__init__(NODE_CHARSET_COMP)
        self.comp_charset = comp_charset

    def __hash__(self):
        return hash((self.node_type, self.comp_charset))

    def __eq__(self, other):
        return self.node_type == other.node_type and self.comp_charset == other.comp_charset

    def __repr__(self):
        return 'FcNodeCompCharset({})'.format(repr(self.comp_charset))


class FcNodeRepeat(FcTreeNode):
    """A FcTreeNode for a repeatition of a child node (symbols ?, + and *)"""
    def __init__(self, node_type, child):
        assert node_type in (NODE_QUESTION, NODE_PLUS, NODE_STAR)
        super().__init__(node_type)
        self.child = child

    def __hash__(self):
        return hash((self.node_type, self.child))

    def __eq__(self, other):
        return self.node_type == other.node_type and self.child == other.child

    def __repr__(self):
        return 'FcNodeRepeat({}, {})'.format(repr(self.node_type), repr(self.child))


class FcNodeOr(FcTreeNode):
    """A FcTreeNode for a choice between children nodes"""
    def __init__(self, children):
        super().__init__(NODE_OR)
        self.children = children

    def __hash__(self):
        return hash((self.node_type, self.children))

    def __eq__(self, other):
        return self.node_type == other.node_type and self.children == other.children

    def __repr__(self):
        return 'FcNodeOr({})'.format(repr(self.children))


class FcNodeParen(FcTreeNode):
    """A FcTreeNode for the concatenation of children nodes (that were in parentheses)"""
    def __init__(self, children):
        super().__init__(NODE_PAREN)
        self.children = children

    def __hash__(self):
        return hash((self.node_type, self.children))

    def __eq__(self, other):
        return self.node_type == other.node_type and self.children == other.children

    def __repr__(self):
        return 'FcNodeparn({})'.format(repr(self.children))


def parse_filepattern(pattern):
    """Build a syntax tree out of a string pattern for a file path

    The result tree is a list of nodes. For example "/etc(/.*)?" gets parsed to:

        [
            (NODE_TEXT, '/etc'),
            (NODE_QUESTION,
                (NODE_PAREN, [
                    (NODE_TEXT, '/'),
                    (NODE_STAR,
                        (NODE_DOT, None)
                    )
                ])
            )
        ]

    In order to generate such a tree, a stack is built following the depth of
    parentheses.
    """
    # Use a state machine for each character
    is_backslashed = False
    is_in_charset = False
    current_buffer = ''
    stack = [[]]
    for cpat in str(pattern):
        if is_backslashed:
            # Add a backslahed character to the buffer
            current_buffer += cpat
            is_backslashed = False
        elif cpat == '\\':
            is_backslashed = True
        elif is_in_charset:
            if cpat == ']':
                # Close a character set
                if current_buffer:
                    if current_buffer[0] == '^':
                        stack[-1].append(FcNodeCompCharset(current_buffer[1:]))
                    else:
                        stack[-1].append(FcNodeCharset(current_buffer))
                current_buffer = ''
                is_in_charset = False
            else:
                # Add the current character of the pattern to the buffer
                current_buffer += cpat
        elif cpat == '[':
            # Flush the buffer and create a new node for a character set
            if current_buffer:
                stack[-1].append(FcNodeText(current_buffer))
                current_buffer = ''
            is_in_charset = True
        elif cpat == '.':
            if current_buffer:
                stack[-1].append(FcNodeText(current_buffer))
                current_buffer = ''
            stack[-1].append(FcNodeDot())
        elif cpat == '(':
            # Increase the parenthesis depth
            if current_buffer:
                stack[-1].append(FcNodeText(current_buffer))
                current_buffer = ''
            stack.append([])
        elif cpat == ')':
            # Close a parenthesed expression
            if len(stack) == 1:
                raise FilePatternParserError("missing '('")
            if current_buffer:
                stack[-1].append(FcNodeText(current_buffer))
                current_buffer = ''
            content = stack.pop()
            # If there has been a | in the content, fill it
            if len(stack[-1]) == 1 and stack[-1][0].node_type == NODE_OR:
                stack.pop()
                content = [FcNodeOr(content)]
            stack[-1].append(FcNodeParen(content))
        elif cpat in REPEATING_SYMBOLS:
            # Modifier affects the last character.
            # Right now, put everything on the stack, it'll be simplified later.
            if len(current_buffer) >= 2:
                # Split out the last character of the buffer:
                # abc? => push "ab" and "c" and create a NODE_QUESTION node with c
                stack[-1].append(FcNodeText(current_buffer[:-1]))
                stack[-1].append(FcNodeText(current_buffer[-1]))
            elif current_buffer:
                stack[-1].append(FcNodeText(current_buffer))
            elif not stack[-1]:
                raise FilePatternParserError("nothing before '{}'".format(cpat))
            current_buffer = ''
            # Change the last item of the stack
            stack[-1][-1] = FcNodeRepeat(REPEATING_SYMBOLS[cpat], stack[-1][-1])
        elif cpat == '|':
            if current_buffer:
                stack[-1].append(FcNodeText(current_buffer))
                current_buffer = ''
            # Add a level in the stack before the last, if it doesn't exist
            if len(stack) <= 2 or stack[-2] == [] or stack[-2][0].node_type != NODE_OR:
                stack.insert(-1, [FcNodeOr(None)])
        else:
            current_buffer += cpat

    if is_backslashed:
        raise FilePatternParserError("missing character after '\\'")
    if is_in_charset:
        raise FilePatternParserError("missing ']'")

    # Close opened things
    assert len(stack) >= 1
    if current_buffer:
        stack[-1].append(FcNodeText(current_buffer))

    if len(stack) >= 2:
        raise FilePatternParserError("missing ')'")
    return stack[0]


def expand_syn_tree_node(node):
    """Expand one node in the syntax tree of a pattern"""
    if node.node_type == NODE_QUESTION:
        # Replace (xyz)? with ()|(xyz)
        return FcNodeOr([
            FcNodeText(''),
            expand_syn_tree_node(node.child)
        ])

    if node.node_type == NODE_CHARSET:
        # Replace [xyz] with x|y|z
        char_range = node.charset
        char_range = char_range.replace('0-9', '0123456789')
        char_range = char_range.replace('a-z', 'abcdefghijklmnopqrstuvwxyz')
        char_range = char_range.replace('A-Z', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        return FcNodeOr([
            FcNodeText(c) for c in char_range])

    if node.node_type == NODE_PAREN:
        # Recurse into the children nodes for parenthesese
        content = expand_syntax_tree(node.children)
        if len(content) == 1:
            return content[0]
        return FcNodeParen(content)

    if node.node_type == NODE_OR:
        # Recurse into the children nodes for OR
        return FcNodeOr([
            expand_syn_tree_node(subnode) for subnode in node.children])

    return node


def expand_syntax_tree(node_list):
    """Expand the syntax tree of a pattern to make it use less kinds of special symbols.

    NB: this function is recursive with expand_syn_tree_node
    """
    # Iterate at most 10 times
    for _ in range(10):
        # Expand each node
        result = []
        for node in node_list:
            node = expand_syn_tree_node(node)

            # Destroy parenthesis in the nodes
            if node.node_type == NODE_PAREN:
                result += node.children
            else:
                result.append(node)
        node_list = result

        # 2nd pass, merge text
        result = []
        need_another_pass = False
        for node in node_list:
            if not result:
                # Don't do anything with the first node
                result.append(node)
            elif node.node_type == NODE_TEXT and result[-1].node_type == NODE_TEXT:
                # Merge text and text
                result[-1] = FcNodeText(result[-1].text + node.text)
            elif node.node_type == NODE_TEXT and result[-1].node_type == NODE_OR:
                # Merge with alternatives, creating parenthesis at a higher level
                result[-1] = FcNodeOr([FcNodeParen([x, node]) for x in result[-1].children])
                need_another_pass = True
            elif node.node_type == NODE_OR and result[-1].node_type == NODE_TEXT:
                result[-1] = FcNodeOr([FcNodeParen([result[-1], x]) for x in node.children])
                need_another_pass = True
            elif node.node_type == NODE_OR and result[-1].node_type == NODE_OR:
                result[-1] = FcNodeOr([
                    FcNodeParen([x, y]) for x in result[-1].children for y in node.children
                ])
                need_another_pass = True
            else:
                result.append(node)
        node_list = result
        if not need_another_pass:
            return node_list
    raise FilePatternParserError("Infinite loop while expanding the pattern")


def parse_pattern_into_node_list(pattern):
    """Transform a path pattern into a list of FcTreeNode objects describing it"""
    try:
        node_list = parse_filepattern(pattern)
        assert node_list
        return expand_syntax_tree(node_list)
    except FilePatternParserError as exc:
        # Add the pattern to the exception and raise it again
        exc.pattern = pattern
        raise exc


def check_parse_pattern_into_node_list():
    """Verify that parse_pattern_into_node_list() is not broken"""
    checks = (
        ('/etc/shadow.*', [
            FcNodeText('/etc/shadow'),
            FcNodeRepeat(NODE_STAR, FcNodeDot()),
        ]),
        (r'/etc/rc\.d/init\.d/(snmpd|snmptrapd)', [
            FcNodeOr([
                FcNodeText('/etc/rc.d/init.d/snmpd'),
                FcNodeText('/etc/rc.d/init.d/snmptrapd'),
            ]),
        ]),
        (r'/srv/([^/]*/)?ftp', [
            FcNodeOr([
                FcNodeText('/srv/ftp'),
                FcNodeParen([
                    FcNodeText('/srv/'),
                    FcNodeRepeat(NODE_STAR, FcNodeCompCharset('/')),
                    FcNodeText('/ftp'),
                ]),
            ]),
        ]),
    )
    for pattern, expected in checks:
        node_list = parse_pattern_into_node_list(pattern)
        if node_list != expected:
            sys.stderr.write(
                "Internal self-test error: pattern {} -> tree {}\nExpected {}"
                .format(pattern, repr(node_list), repr(expected)))
            raise RuntimeError("Internal test failed")


def exists_treefile(node_list):
    """Test whether an expanded syntax tree of a pattern refers to an existing file.

    Returns:
    * True if an existing file matches the pattern
    * False if no file matches the pattern
    * None if the pattern is too complex
    """
    if len(node_list) != 1:
        # Pattern is too complex
        return None

    # node_list may be a file...
    if node_list[0].node_type == NODE_TEXT:
        return os.path.exists(node_list[0].text)

    # ... or a list of files
    if node_list[0].node_type == NODE_OR:
        are_all_pathes = True
        for choice in node_list[0].children:
            if choice.node_type != NODE_TEXT:
                are_all_pathes = False
                break
            elif os.path.exists(choice.text):
                return True
        # If the list of file contains only non-existing files, return False
        return False if are_all_pathes else None

    raise FilePatternParserError("Unexpected root node type {}".format(repr(node_list[0].node_type)))


def get_globs_from_tree(node_list):
    """Transform a pattern syntax tree to a list of patterns suitable for glob()"""
    glob_patterns = ['']

    # List of translations
    patterns_from_glob = (
        (FcNodeCompCharset('/'), '?'),  # [^/] => ?
        (FcNodeRepeat(NODE_STAR, FcNodeCompCharset('/')), '*'),  # [^/]* => *
        (FcNodeRepeat(NODE_PLUS, FcNodeCompCharset('/')), '*?'),  # [^/]+ => *?
        # "." can match "/" in the pattern, contrary to the resulting glob.
        # This is a limitation of the translation
        (FcNodeDot(), '?'),  # . => ?
        (FcNodeRepeat(NODE_STAR, FcNodeDot()), '*'),  # .* => *
        (FcNodeRepeat(NODE_PLUS, FcNodeDot()), '*?'),  # .+ => *?
    )

    for node in node_list:
        if node.node_type == NODE_TEXT:
            # Add a static part to every globs
            for i in range(len(glob_patterns)):
                glob_patterns[i] += node.text

        elif node.node_type == NODE_PAREN:
            globs_paren = get_globs_from_tree(node.children)
            # If the pattern is too complex, return None
            if globs_paren is None:
                return None
            glob_patterns += [x + y for x in glob_patterns for y in globs_paren]

        elif node.node_type == NODE_OR:
            new_glob_patterns = []
            for choice in node.children:
                globs_choice = get_globs_from_tree([choice])
                # If the pattern is too complex, return None
                if globs_choice is None:
                    return None
                new_glob_patterns += [x + y for x in glob_patterns for y in globs_choice]
            glob_patterns = new_glob_patterns
        else:
            # Translate leafs
            has_matched = False
            for known_node, known_glob in patterns_from_glob:
                if node == known_node:
                    has_matched = True
                    for i in range(len(glob_patterns)):
                        glob_patterns[i] += known_glob
                    break
            # If the pattern is too complex, return None
            if not has_matched:
                return None
    return glob_patterns


def has_file_for_fcfile(file_path):
    """Test whether some file patterns in the given .fc file are applicable

    Returns:
    * True if an existing file matches the pattern
    * False if no file matches the pattern or if the pattern is too complex for this simple analyzer
    """
    patterns_after_first_pass = []
    with file_path.open('r') as fd:
        for line in fd:
            line = line.strip()
            if not line or line[0] == '#' or line.startswith(('ifdef(`', 'ifndef(`', '\', `', '\')')):
                continue
            pattern = line.split()[0]
            if not pattern:
                continue

            # Remove m4-escaping trick using an empty list
            pattern = pattern.replace("`'", "")

            # Trim the end of the pattern before the analysis
            for ending in ('(/.*)?', '/.*'):
                if pattern.endswith(ending):
                    pattern = pattern[:-len(ending)]
                    if not pattern:
                        # The pattern maches the whole filesystem
                        return True

            # HOME_DIR always exists
            if pattern == 'HOME_DIR':
                return True
            # Files in HOME_DIR are never assumed to exist
            if pattern.startswith('HOME_DIR'):
                continue

            # Build a node tree for the pattern
            node_list = parse_pattern_into_node_list(pattern)
            existing_state = exists_treefile(node_list)

            # If an existing file matches the pattern, return True.
            if existing_state:
                return True
            # If the pattern is more complex, add it to all_patterns.
            if existing_state is None:
                patterns_after_first_pass.append((pattern, node_list))

    # If no pattern remains after the first pass, no matching file exists on this system
    if not patterns_after_first_pass:
        return False

    # Second pass: try glob() patterns
    patterns_after_second_pass = []
    for pattern, node_list in patterns_after_first_pass:
        glob_patterns = get_globs_from_tree(node_list)
        if glob_patterns is None:
            # The pattern is too complex
            patterns_after_second_pass.append((pattern, node_list))
            continue

        for gpat in glob_patterns:
            if glob.glob(gpat):
                return True

        # The pattern has been translated into a list of globs and nothing matched: drop it and continue the loop

    # If no pattern remains after the second pass, no matching file exists on this system
    if not patterns_after_second_pass:
        return False

    # By default, ignore too strange patterns where nothing else matches
    return False


def get_base_modules(policy_path):
    """Yield modules in base.pp from the modules.conf file in policypath"""
    with (policy_path / 'modules.conf').open('r') as fd_modules_conf:
        for line in fd_modules_conf:
            if '=' in line:
                modname, category = line.split('=', 1)
                if category.strip() == 'base':
                    yield modname.strip()


def get_policy_name(policy_path):
    """Read the policy name from build.conf"""
    buildconf = policy_path / '..' / 'build.conf'
    try:
        with open(buildconf, 'r') as fd_build_conf:
            for line in fd_build_conf:
                line = line.strip()
                if line.startswith('NAME'):
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        pass
    return None


def main(argv=None):
    # Perform some sanity checks
    check_parse_pattern_into_node_list()

    policy_dir = (Path(__file__).parent / '..' / 'policy').resolve()
    parser = argparse.ArgumentParser(description="Get a list of SELinux modules that may be useful on this system")
    parser.add_argument('-p', '--path', type=Path, default=policy_dir,
                        help="path to the policy directory [{}]".format(policy_dir))
    parser.add_argument('-b', '--base', action='store_true',
                        help="include base modules in the result")
    parser.add_argument('-c', '--cmdline', action='store_true',
                        help="print a semodule command line to load modules")
    parser.add_argument('-d', '--diff', action='store_true',
                        help="compare the list of modules with the result of semodule -l")
    args = parser.parse_args(argv)

    # Compute the base modules if -b is not present
    base_modules = frozenset([] if args.base else get_base_modules(args.path))

    # Initialize the list with the default user modules
    modules = ['staff', 'sysadm', 'unprivuser']
    # application module is also a dependency of many modules, but does not have any file context pattern
    modules.append('application')
    # xdg module is also a dependency of many modules, but all its file context patterns are for HOME_DIR
    modules.append('xdg')

    # Browser the file context files
    for file_path in args.path.glob('**/*.fc'):
        assert file_path.name.endswith('.fc')
        module_name = file_path.name[:-3]
        if module_name in base_modules:
            continue
        try:
            if has_file_for_fcfile(file_path):
                modules.append(module_name)
        except FilePatternParserError as exc:
            sys.stderr.write(
                "Pattern parser error: {} (pattern: {}, file: {})\n"
                .format(exc.message, exc.pattern, file_path))
            return 1

    if args.diff:
        # Remove the active modules from the list of useful modules
        semodule_output = subprocess.check_output(['semodule', '-l'])
        current_modules = frozenset(semodule_output.decode().splitlines())
        modules_set = set(modules)
        # print("Unnecessary modules: {}".format(current_modules - modules_set))
        modules = list(modules_set - current_modules)
        if not modules:
            print("{}All the required modules have already been loaded.".format("# " if args.cmdline else ""))
            return 0

    modules.sort()
    if args.cmdline:
        cmdline = 'semodule -v -i base.pp'
        # Read the policy name
        pol_name = get_policy_name(args.path)
        if pol_name:
            cmdline += ' -s ' + pol_name
        cmdline += ''.join(' -i {}.pp'.format(modname) for modname in modules)
        print(cmdline)
    else:
        for modname in modules:
            print(modname)
    return 0


if __name__ == '__main__':
    sys.exit(main())
