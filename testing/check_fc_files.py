#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
# Copyright (C) 2019 Nicolas Iooss
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
"""Check the .fc files for some common errors

@author: Nicolas Iooss
@license: GPLv2
"""
import argparse
from pathlib import Path
import re


# Common patterns for ending a file pattern, associated with something to
# replace the pattern with, during the checks.
# Order matters as the first ones are tried before the last ones
#
# Use the infinity symbol to replace "any character", in order to keep a meaning
# of any possible character in the pattern after the reduction operations.
COMMON_FILE_END_PATTERNS = (
    ('/.+', ''),  # Match the children of a directory
    ('/.*', ''),  # Like /.+, but it could be empty
    ('(/.*)', ''),  # Like /.*, but with useless parentheses
    ('/[^/]+', ''),  # Match any filename
    ('/[^/]*', ''),  # Match any filename, but it could be empty
    ('(/[^/]*)', ''),  # Like /[^/]*, but with useless parentheses
    ('(/[^/]*)?', ''),  # Match a directory and its direct children
    ('(/.+)?', ''),  # Match a directory and its children
    ('(/.*)?', ''),  # Match a directory and its children
    ('/(sbin/)?.*', ''),  # Weird pattern for postfix, which would better be (/sbin)?(/.*)?
    ('\\.so(\\.[^/]*)*', '\\.so'),  # Match a .so extension, which is really weird because [^/] matches a dot too, so the final star can be replaced with '?'  # noqa
    ('\\.db(\\.[^/]*)*', '\\.db'),  # Match a .db extension, which is really weird because [^/] matches a dot too, so the final star can be replaced with '?'  # noqa
    ('(\\.[^/]+)?', ''),  # Match a possible file extension
    ('(\\..+)', '\\.∞'),  # Match a dot and anything after
    ('(\\..*)?', '\\.∞'),  # Match a dot and anything after or nothing, or nothing at all
    ('\\..*', '\\.'),  # Match a dot and anything after or nothing
    ('.*', ''),  # Match anything after
    ('.+', '∞'),  # Match anything after, but at least one character
    ('[^/]+', '∞'),  # Match anything after which does not create a new directory level
    ('[^/]*', ''),  # Like [^/]+, but may be empty
    ('[^/-]*', ''),  # Like [^/]*, but do not match files with dashes in their names
    ('[a-z]?', ''),  # Match a possible letter
    ('[a-z]*', ''),  # Match some letters
    ('[0-9]?', ''),  # Match a possible digit
    ('[0-9]*', ''),  # Match some digits
    ('[0-9]+', '0'),  # Match at least one digit
    ('(\\.bin)?', ''),  # Match an optional extension
    ('(-.*)?', ''),  # Match an optional suffix with a minus sign
)

# File types in a .fc file
FILE_TYPES = (None, '--', '-b', '-c', '-d', '-l', '-p', '-s')

NONE_CONTEXT = '<<none>>'

MLS_LEVELS = ('s0', 'mls_systemhigh', 's0-mls_systemhigh')


def analyze_fc_file(fc_path):
    """Analyze a .fc file

    Return False if a warning has been generated
    """
    retval = True

    with fc_path.open('r') as fd:
        for lineno, line in enumerate(fd, start=1):
            line = line.strip()

            # Ignore lines that cannot contain a file context
            if not line or line.startswith(('#', "'", 'ifdef(', 'ifndef(')):
                continue

            prefix = f"{fc_path}:{lineno}: "

            matches = re.match(r'^(?P<path>\S+)\s+(?P<ftype>-.)?\s*(?P<context>.+)$', line)
            if matches is None:
                print(f"{prefix}unable to parse a file context file: {repr(line)}")
                retval = False
                continue

            path, ftype, context = matches.group('path', 'ftype', 'context')

            # Check the file type of the pattern
            if ftype not in FILE_TYPES:
                print(f"{prefix}unexpected file type for {path}: {repr(ftype)}")
                retval = False

            # Check the SELinux context
            if context != NONE_CONTEXT:
                matches = re.match(r'^gen_context\((\S*), ?(\S*)\)$', context)
                if not matches:
                    print(f"{prefix}unknown SELinux context format for {path}: {context}")
                    retval = False
                else:
                    context_label, context_mls = matches.groups()
                    if not context_label.startswith('system_u:object_r:'):
                        print(f"{prefix}SELinux context does not begin with 'system_u:object_r:' for {path}: {context}")  # noqa
                        retval = False
                    elif not re.match(r'^system_u:object_r:[0-9A-Za-z_]+$', context_label):
                        print(f"{prefix}SELinux context type uses unexpected characters for {path}: {context}")  # noqa
                        retval = False
                    elif context_mls not in MLS_LEVELS:
                        print(f"{prefix}SELinux context uses an unexpected MLS label for {path}: {context_mls} (in {context})")  # noqa
                        retval = False

            # Find obviously-wrong patterns
            if '(.*)?' in path:
                # As (.*) can match the empty string, the question mark is redundant
                print(f"{prefix}pattern (.*)? is very likely to be a misspelling for .* or (/.*)?, for {path}")
                retval = False

            if '\\d' in path:
                # In the past, "resource.\d" has already been introduced instead of "resource\.d".
                # Detect such bugs by forbidding the use of \d
                print(f"{prefix}escaping d could be a bug in {path}, please use [0-9] instead")
                retval = False

            if re.search(r'[^/]\(\.\*/\)\?', path):
                print(f"{prefix}using (.*/)? without a previous slash could be a bug in {path} as it can match the empty string, please use /(.*/)? instead")  # noqa
                retval = False

            if re.search(r'[^/]\(\[\^/\]\+/\)\?', path):
                print(f"{prefix}using ([^/]+/)? without a previous slash could be a bug in {path} as it can match the empty string, please use /([^/]+/)? instead")  # noqa
                retval = False

            if re.search(r'[^/]\(\.\*/\)\*', path):
                print(f"{prefix}using (.*/)* without a previous slash could be a bug in {path} as it can match the empty string, please use /(.*/)* instead")  # noqa
                retval = False

            if re.search(r'\(\.\*/\)[^?*+]', path):
                print(f"{prefix}using (.*/) without a ?, * or + symbol could be a bug in {path} as it misleads readers into thinking that this part is optional, please use .*/ instead")  # noqa
                retval = False

            reduced_path = path

            # Using "index`'(...)" is a way to prevent an error message from m4:
            # https://github.com/SELinuxProject/refpolicy/commit/cc1eee120263523c7b79ac16acc698c537a4d25e
            # Let's replace the symbols in the path, for the checks,
            # while keeping "path" untouched in the warning messages
            reduced_path = reduced_path.replace("index`'(", 'index(')
            reduced_path = reduced_path.replace("inde(x)(", 'index(')
            reduced_path = reduced_path.replace("include`'(", 'include(')

            # Check the character set of the path
            invalid_characters = set(re.findall(r'[^-0-9A-Za-z_@./()?+*%{}\[\]^|:~\\]', reduced_path))
            if invalid_characters:
                print(f"{prefix}unexpected characters {' '.join(sorted(invalid_characters))} in {path}")
                retval = False

            # Check the start of the path
            if not path.startswith(('/', 'HOME_DIR/', 'HOME_ROOT/')) and path not in ('HOME_DIR', 'HOME_ROOT'):
                print(f"{prefix}unexpected start of file pattern for {path}")
                retval = False

            # Reduce the path in order to check its sanity (like using a non-buggy end pattern):
            # * Truncating common endings
            while True:
                has_truncated = False
                for (common_end, substitute) in COMMON_FILE_END_PATTERNS:
                    if reduced_path.endswith(common_end):
                        reduced_path = f"{reduced_path[:-len(common_end)]}{substitute}"
                        has_truncated = True
                        break
                if not has_truncated:
                    break

            # * Replace back-slashed characters with special ones
            while '\\' in reduced_path:
                backslash_index = reduced_path.index('\\')
                esc_sequence = reduced_path[backslash_index:backslash_index + 2]
                if esc_sequence == '\\.':
                    # Replace \. with U+00B7 middle dot
                    reduced_path = f"{reduced_path[:backslash_index]}\u00b7{reduced_path[backslash_index + 2:]}"
                elif esc_sequence == '\\+':
                    # Replace \+ with U+2020 dagger
                    reduced_path = f"{reduced_path[:backslash_index]}\u2020{reduced_path[backslash_index + 2:]}"
                elif esc_sequence == '\\d':
                    # Replace \d with U+03B4 delta
                    reduced_path = f"{reduced_path[:backslash_index]}\u03b4{reduced_path[backslash_index + 2:]}"
                else:
                    print(f"{prefix}unexpected escape sequence {esc_sequence} in {path} (reduced to {reduced_path})")
                    retval = False
                    break

            # * Replace variables with place-holders
            if '%' in reduced_path:
                reduced_path = reduced_path.replace('%{USERID}', '_USERID_')
                reduced_path = reduced_path.replace('%{USERNAME}', '_USERNAME_')
                if '%{' in reduced_path:
                    print(f"{prefix}unexpected '%{{' in {path} after reduction to {reduced_path}")
                    retval = False

            # * Detect "??", "**", etc. before more reductions occur
            for bad_pattern in sorted(set(re.findall(r'[?*+][?*+]', reduced_path))):
                print(f"{prefix}unexpected pattern {repr(bad_pattern)} in {path} after reduction to {reduced_path}")
                retval = False

            # Remove optional directories and filename parts
            reduced_path = reduced_path.replace('/([^/]+/)?', '/')
            reduced_path = reduced_path.replace('(/[^/]+)?/', '/')
            reduced_path = reduced_path.replace('[^/]*', '')
            reduced_path = reduced_path.replace('[^/]+', '∞')
            reduced_path = reduced_path.replace('[^/-]+', '∞')
            reduced_path = reduced_path.replace('/(.*/)?', '/')
            reduced_path = reduced_path.replace('(/.*)?', '')
            reduced_path = reduced_path.replace('/.*/', '/')

            # * Remove parenthesese around choices options: ((www)|(web)|(public_html)) -> (www|web|public_html)
            while True:
                new_reduced_path = re.sub(r'([|(])\(([-0-9A-Za-z_]+)\)([|)])', r'\1\2\3', reduced_path)
                if new_reduced_path == reduced_path:
                    break
                reduced_path = new_reduced_path

            # * Detect a pipe directly inside a parenthesis, which is wrong (use symbol ? instead)
            if '|)' in reduced_path or '(|' in reduced_path:
                print(f"{prefix}unexpected pipe-parenthesis pattern in {path} after reduction to {reduced_path}")
                retval = False

            # * Remove optional choices (...|...)?
            while True:
                new_reduced_path = re.sub(r'\([-0-9A-Za-z_|/·]+\)\?', '', reduced_path)
                if new_reduced_path == reduced_path:
                    break
                reduced_path = new_reduced_path

            # * Replace mandatory choices (...|...) with the first option
            while True:
                new_reduced_path = re.sub(r'\(([-0-9A-Za-z_/]+)\|[-0-9A-Za-z_|/]+\)', r'\1', reduced_path)
                if new_reduced_path == reduced_path:
                    break
                reduced_path = new_reduced_path

            # * Remove optional characters like c?
            reduced_path = re.sub(r'[-0-9A-Za-z_@·]\?', '', reduced_path)

            # If the reduced path still ends with a special character, something went wrong.
            # Instead of guessing the possible buggy characters, list the allowed ones.
            if reduced_path and not re.match(r'[-0-9A-Za-z_@\]~·†∞]', reduced_path[-1]):
                if path != '/':
                    if reduced_path == path:
                        print(f"{prefix}unexpected end of file pattern for {path}")
                    else:
                        print(f"{prefix}unexpected end of file pattern for {path} after being reduced to {reduced_path}")  # noqa
                    retval = False

            # Now remove and replace some matching patterns from the path, in order to catch invalid characters
            reduced_path = reduced_path.replace('(-.*)?', '')
            reduced_path = reduced_path.replace('(.*-)?', '')
            reduced_path = reduced_path.replace('(-[0-9])?', '')
            reduced_path = reduced_path.replace('(.*)', '')
            reduced_path = reduced_path.replace('.*', '')
            reduced_path = reduced_path.replace('.+', '∞')
            reduced_path = re.sub(r'\[[-0-9A-Za-z_.^]+\][?*]', '', reduced_path)
            reduced_path = re.sub(r'\[[-0-9A-Za-z_.^]+\](\+)?', '∞', reduced_path)
            reduced_path = reduced_path.replace('/[^/]+/', '/∞/')

            if '.' in reduced_path:
                print(f"{prefix}unescaped dot still present {path} after being reduced to {reduced_path} (suggestion: use \\. to match a dot, or a charset like [^/])")  # noqa
                retval = False

            # Check the remaining symbols in the reduced path.
            # Only show a warning if no other ones were reported, in order to reduce the probability of false-positive.
            invalid_symbols = set(re.findall(r'[^-0-9A-Za-z_@~:·†∞/]', reduced_path))
            if retval and invalid_symbols:
                print(f"{prefix}unexpected symbols {' '.join(sorted(invalid_symbols))} in {path} after being reduced to {reduced_path}. This could be due to an error in the pattern or a missing reduction rule in the checker")  # noqa
                retval = False

    return retval


def analyze_all_fc(policy_dirpath):
    """Analyze all .fc files in the specified directory"""
    retval = True
    for file_path in sorted(policy_dirpath.glob('**/*.fc')):
        if not analyze_fc_file(file_path):
            retval = False
    return retval


def main(argv=None):
    policy_dir = (Path(__file__).parent / '..' / 'policy').resolve()

    parser = argparse.ArgumentParser(description="Find missing file contexts")
    parser.add_argument('fc_files', metavar='FC_FILES', nargs='*', type=Path,
                        help=".fc files to analyze (by default: all in the policy)")
    parser.add_argument('-p', '--policy', metavar='POLICY_DIR', type=Path, default=policy_dir,
                        help="path to the policy directory [{0}]".format(policy_dir))
    args = parser.parse_args(argv)

    if args.fc_files:
        retval = True
        for file_path in args.fc_files:
            if not analyze_fc_file(file_path):
                retval = False
        return retval

    return 0 if analyze_all_fc(args.policy) else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
