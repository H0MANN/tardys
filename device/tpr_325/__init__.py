#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


##########################################################################
MODULE_NAME = __name__
DEVICE_NAME = MODULE_NAME.split(".")[-1]


##########################################################################
from taoics.tardys import config_logger
config_logger(MODULE_NAME)
del config_logger


##########################################################################
def build_tpr(loglevel=None):
    import logging

    from taoics.tardys import config, config_mysql
    from taoics.common.device.tpr.tprlib import LS325

    mysql = config_mysql(DEVICE_NAME)
    logger = logging.getLogger(MODULE_NAME)

    if loglevel is not None:
        logger.setLevel(loglevel)

    tpr = LS325(
        tty = config.get(DEVICE_NAME, "tty"),
        baudrate = config.getint(DEVICE_NAME, "serial_baudrate"),
        parity = config.get(DEVICE_NAME, "serial_parity"),
        bytesize = config.getint(DEVICE_NAME, "serial_bytesize"),
        stopbits = config.getint(DEVICE_NAME, "serial_stopbits"),
        timeout = config.getint(DEVICE_NAME, "serial_timeout"),
        rtscts = config.getboolean(DEVICE_NAME, "serial_rtscts"),
        logger = logger,
        mysql = mysql
        )

    return tpr
