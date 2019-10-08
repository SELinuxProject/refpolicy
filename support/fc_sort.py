#!/usr/bin/env python3

"""Sort file context definitions

The original setfiles sorting algorithm did not take into
account regular expression specificity. With the current
strict and targeted policies this is not an issue because
the file contexts are partially hand sorted and concatenated
in the right order so that the matches are generally correct.
The way reference policy and loadable policy modules handle
file contexts makes them come out in an unpredictable order
and therefore setfiles (or this standalone tool) need to sort
the regular expressions in a deterministic and stable way.
"""

import sys
import argparse
from pathlib import Path
import re


class FileContext():
    """ Container class for file context defintions
    """

    def __init__(self, context_line):
        """ Constructor
        """

        matches = re.match(r'^(?P<path>\S+)\s+(?P<type>-.)?\s*(?P<context>.+)$', context_line)
        if matches is None:
            raise ValueError

        self.path, self.file_type, self.context = matches.group('path', 'type', 'context')

        self.compute_diffdata()

    def compute_diffdata(self):
        """ Compute the interal values needed for comparing two file context definitions
        """

        self.meta = False
        self.stem_len = 0
        self.str_len = 0

        skip_escaped = False

        for char in self.path:
            if skip_escaped:
                skip_escaped = False
                continue

            if char in ('.', '^', '$', '?', '*', '+', '|', '[', '(', '{',):
                self.meta = True
            if char == '\\':
                skip_escaped = True

            if not self.meta:
                self.stem_len += 1

            self.str_len += 1

    @staticmethod
    def _compare(a, b):
        """ Compare two file context definitions

        Returns:
          -1 if a is less specific than b
           0 if a and be are equally specific
           1 if a is more specific than b
        The comparison is based on the following statements,
        in order from most important to least important, given a and b:
           If a is a regular expression and b is not,
            -> a is less specific than b.
           If a's stem length is shorter than b's stem length,
            -> a is less specific than b.
           If a's string length is shorter than b's string length,
            -> a is less specific than b.
           If a does not have a specified type and b does,
            -> a is less specific than b.
        """

        # Check to see if either a or b have meta characters and the other doesn't
        if a.meta and not b.meta:
            return -1
        if b.meta and not a.meta:
            return 1

        # Check to see if either a or b have a shorter stem length than the other
        if a.stem_len < b.stem_len:
            return -1
        if b.stem_len < a.stem_len:
            return 1

        # Check to see if either a or b have a shorter string length than the other
        if a.str_len < b.str_len:
            return -1
        if b.str_len < a.str_len:
            return 1

        # Check to see if either a or b has a specified type and the other doesn't
        if not a.file_type and b.file_type:
            return -1
        if not b.file_type and a.file_type:
            return 1

        # If none of the above conditions were satisfied, then a and b are equally specific
        return 0

    def __lt__(self, other):
        return self._compare(self, other) == -1

    def __str__(self):
        if self.file_type:
            return '{}\t\t{}\t{}'.format(self.path, self.file_type, self.context)
        else:
            return '{}\t\t{}'.format(self.path, self.context)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Sort file context definitions')
    parser.add_argument('infile', metavar='INFILE', type=Path,
                        help='input file of the original file context definitions')
    parser.add_argument('outfile', metavar='OUTFILE', nargs='?', type=Path, default=None,
                        help='output file for the sorted file context definitions')
    args = parser.parse_args()

    file_context_definitions = []

    # Parse the input file
    with args.infile.open('r') as fd:
        for lineno, line in enumerate(fd, start=1):
            line = line.strip()

            # Ignore comments and empty lines
            if not line or line.startswith('#'):
                continue

            try:
                file_context_definitions.append(FileContext(line))
            except ValueError:
                print('{}:{}: unable to parse a file context line: {}'.format(args.infile, lineno, line))
                exit(1)

    # Sort
    file_context_definitions.sort()

    # Print output, either to file or if no output file given to stdout

    with args.outfile.open('w') if args.outfile else sys.stdout as fd:
        for fcd in file_context_definitions:
            print(fcd, file=fd)
