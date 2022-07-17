#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                                                unicode_literals)

from taoics.swims import config_mysql


#############################################################################
if __name__ == "__main__":
    import os

    if len(os.sys.argv) < 3:
        print("\nUsage: {} table_name field_name [new_value]\n".format(os.path.basename(os.sys.argv[0])))
        os.sys.exit()

    table_name = os.sys.argv[1]
    key = os.sys.argv[2]
    if len(os.sys.argv) == 4:
        val = os.sys.argv[3]

    else:
        ret = config_mysql(table_name).select_status(where={"NAME": key})
	print("{}: {}: {}".format(table_name, key, ret[0]["value"]))
        os.sys.exit()

    tsv_dir = "/home/anir/taoics/swims/util/mysql/setting/status"
    tsv_file = "{}.tsv".format(table_name)
    tsv_file = os.path.join(tsv_dir, tsv_file)
    tsv_file_old = tsv_file + "_old"
    tsv_file_new = tsv_file + "_new"

    with open(tsv_file, "r") as fp:
        lines = fp.readlines()

    with open(tsv_file_new, "w") as fp:
        for line in lines:
            line = line.strip()
            keyval = line.split("\t")
            if keyval[0] != key:
#                print(line)
                fp.write(line + os.linesep)

            else:
		print("{}: {}: {} ==> {}".format(table_name, key, keyval[1], val))
                keyval[1] = val
                fp.write("\t".join(keyval) + os.linesep)


    config_mysql(table_name).update_status_values({key: val})

    if os.path.exists(tsv_file_old):
        os.remove(tsv_file_old)

    os.rename(tsv_file, tsv_file_old)
    os.rename(tsv_file_new, tsv_file)
