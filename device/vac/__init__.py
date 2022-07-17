#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


##########################################################################
MODULE_NAME = __name__
DEVICE_NAME = MODULE_NAME.split(".")[-1]

if not MODULE_NAME.startswith("taoics"):
    raise ImportError("Load from 'taoics' package level, like 'from taoics.*** import ***.")


##########################################################################
from taoics.tardys import config_logger
config_logger(MODULE_NAME)
del config_logger


##########################################################################
def build_vac(loglevel=None):
    import logging

    from taoics.tardys import config, config_mysql
    from taoics.common.device.vac.vaclib import TPG261

    mysql = config_mysql(DEVICE_NAME)
    logger = logging.getLogger(MODULE_NAME)

    if loglevel is not None:
        logger.setLevel(loglevel)

    vac = TPG261(
        tty = config.get(DEVICE_NAME, "tty"),
        baudrate = config.getint(DEVICE_NAME, "serial_baudrate"),
        parity = config.get(DEVICE_NAME, "serial_parity"),
        bytesize = config.getint(DEVICE_NAME, "serial_bytesize"),
        stopbits = config.getint(DEVICE_NAME, "serial_stopbits"),
        timeout = config.getint(DEVICE_NAME, "serial_timeout"),
        logger = logger,
        mysql = mysql
        )

    return vac
