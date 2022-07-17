#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from taoics.common.device.vac.vacbase import connect_and_close_if_needed
from taoics.swims.device.vac import vac


##########################################################################
@connect_and_close_if_needed
def read_and_save(vac):
    _col_value = "CH{:02d}_VALUE"
    _col_name = "CH%_NAME"

    ## Reads each channel.
    val1 = vac.read(1)
    val2 = vac.read(2)
    vac.logger.info("Read each channel.")

    vals_dict = {
        _col_value.format(1): val1,
        _col_value.format(2): val2
        }


    ## Updates status table.
    vac.mysql.update_status_values(vals_dict)
    vac.logger.info("Updated SQL status table.")


    ## Adds to log table.
    names = vac.mysql.select_status(where={"NAME": _col_name})
    for name in names:
        vals_dict[name["name"]] = name["value"]

    vac.mysql.insert_log(vals_dict)
    vac.logger.info("Added to SQL log table.")

    return vals_dict



##########################################################################
if __name__ == "__main__":
    from taoics.common.util.optparse import common_parser
    parser = common_parser()

    from taoics.common.device.vac.vac_utils import add_parser_TPG262
    parser = add_parser_TPG262(parser)

    args = parser.parse_args()

    if args.loglevel:
        vac.logger.setLevel(args.loglevel)

    if args.action == "read":
        print(read_and_save(vac))
    elif args.action == "unit":
        print(vac.unit(args.val))
    elif args.action == "digit":
        print(vac.digit(args.val))
    else:
        parser.print_help()
