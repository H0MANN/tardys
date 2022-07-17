#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os


##########################################################################
def main(infile):
    outfile = os.path.splitext(infile)[0] + ".tsv"
    with open(outfile, "w") as fp:

        for i, line in enumerate(open(infile, "r")):
            if i < 3:
                continue

            line = line.replace('"', '')
            line = line.strip()
            if line.endswith(","):
                line = line[:-1]

            line = line.split(":")

            if len(line) != 2:
                continue

            print("\t".join(line), file=fp)

    return


##########################################################################
if __name__ == "__main__":
    main(os.sys.argv[1])

