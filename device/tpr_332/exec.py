#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import numpy as np

from taoics.common.device.tpr.tpr_utils import connect_and_close_if_needed


##########################################################################
_col_temp = "CH{:02d}_TEMP"
_col_rate = "CH{:02d}_RATE"
_col_setp = "CH{:02d}_SETP"
_col_hout = "CH{:02d}_HOUT"
_col_mout = "CH{:02d}_MOUT"
_col_ramp = "CH{:02d}_RAMP"
_col_ramp_rate = "CH{:02d}_RAMP_RATE"
_col_pid_p = "CH{:02d}_PID_P"
_col_pid_i = "CH{:02d}_PID_I"
_col_pid_d = "CH{:02d}_PID_D"
_col_name = "CH%_NAME"


##########################################################################
@connect_and_close_if_needed
def read_and_save(tpr):  # 'tpr' is necessary to use this decorator...

    ## Reads each channel.
    temp1 = tpr.read_temp(1)
    temp2 = tpr.read_temp(2)

    setp1 = tpr.read_setp(1)
    setp2 = tpr.read_setp(2)

    hout1 = tpr.read_hout(1)
    hout2 = tpr.read_hout(2)

    mout1 = tpr.mout(1)
    mout2 = tpr.mout(2)

    ramp1, ramp_rate1 = tpr.ramp(1).split(",")
    ramp2, ramp_rate2 = tpr.ramp(2).split(",")

    pid1 = tpr.pid(1).split(",")
    pid2 = tpr.pid(2).split(",")

    hrange = tpr.hrange()

    tpr.logger.info("Read each channel.")


    ## Adds to log table.
    vals_dict_log = collections.OrderedDict(
        (
            (_col_temp.format(1), temp1),
            (_col_temp.format(2), temp2),
            (_col_setp.format(1), setp1),
            (_col_setp.format(2), setp2),
            (_col_hout.format(1), hout1),
            (_col_hout.format(2), hout2),
            )
        )

    names = tpr.mysql.select_status(where={"NAME": _col_name})
    for name in names:
        vals_dict_log[name["name"]] = name["value"]  ## set value for 'CH%_NAME'.

    tpr.mysql.insert_log(vals_dict_log)
    tpr.logger.info("Added to SQL log table.")


    ## Updates status table.
    vals_dict_status = {
        _col_mout.format(1): mout1,
        _col_mout.format(2): mout2,
        _col_ramp.format(1): ramp1,
        _col_ramp.format(2): ramp2,
        _col_ramp_rate.format(1): ramp_rate1,
        _col_ramp_rate.format(2): ramp_rate2,
        _col_pid_p.format(1): pid1[0],
        _col_pid_i.format(1): pid1[1],
        _col_pid_d.format(1): pid1[2],
        _col_pid_p.format(2): pid2[0],
        _col_pid_i.format(2): pid2[1],
        _col_pid_d.format(2): pid2[2],
        "HRANGE": hrange
        }
    vals_dict_status.update(vals_dict_log)

    tpr.mysql.update_status_values(vals_dict_status)
    tpr.logger.info("Updated SQL status table.")


    return vals_dict_status


##########################################################################
def calc_rate(tpr, n=5):
    tpr.logger.setLevel(20)

    vals_dict = collections.OrderedDict()

    log_data = tpr.mysql.select_log(order={"date": "DESC"}, limit=n)

    dates_diff = np.diff(log_data["date"])

    for ch in [1, 2]:
        name = _col_temp.format(ch)
        name_rate = _col_rate.format(ch)
#        print(name, log_data[name])

        vals_diff = np.diff(np.array(log_data[name]))

        vals = []
        for date_diff, val_diff in zip(dates_diff, vals_diff):
            val = val_diff / date_diff.total_seconds() * 60  ## K/min
            vals.append(val)

        vals_dict[name_rate] = "{:+.3f}".format(np.median(vals))

    ## Updates status table.
    tpr.mysql.update_status_values(vals_dict)

    return vals_dict


##########################################################################
if __name__ == "__main__":
    from taoics.swims.device.tpr_332 import build_tpr

    from taoics.common.util.optparse import common_parser
    parser = common_parser()

    from taoics.common.device.tpr.tpr_utils import add_parser_LS33X
    parser = add_parser_LS33X(parser)
    
    args = parser.parse_args()
#    print(args)

    tpr = build_tpr(loglevel=args.loglevel)

    if args.action == "read":
        print(read_and_save(tpr))

    elif args.action == "setp":
        print(tpr.setp(args.ch, args.setp))

    elif args.action == "hrange":
        print(tpr.hrange(args.range))

    elif args.action == "hout":
        print(tpr.read_hout(args.ch))

    elif args.action == "pid":
        print(tpr.pid(args.ch, args.p, args.i, args.d))

    elif args.action == "ramp":
        print(tpr.ramp(args.ch, args.onoff, args.rate))

    elif args.action == "ramp_on":
        print(tpr.ramp_on(args.ch, args.rate))

    elif args.action == "ramp_off":
        print(tpr.ramp_off(args.ch))

    elif args.action == "rampst":
        print(tpr.ramp(args.ch))

    elif args.action == "mout":
        print(tpr.mout(args.ch, args.mout))

    elif args.action == "calc_rate":
        print(calc_rate(tpr, args.n))

    else:
        parser.print_help()
