#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from taoics.tardys import config_mysql


#############################################################################
if __name__ == "__main__":
    import os

    mysql = config_mysql()
    mysql.create_status_table_from_file(infile=os.sys.argv[1], 
                                        drop_if_exists=True)
