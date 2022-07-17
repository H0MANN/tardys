#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


##########################################################################
MODULE_NAME = __name__
DEVICE_NAME = MODULE_NAME.split(".")[-1]


##########################################################################
from taoics.swims import config_logger
logger = config_logger(MODULE_NAME)
del config_logger


##########################################################################
from taoics.swims import config_mysql
mysql = config_mysql(DEVICE_NAME)
del config_mysql


##########################################################################
from taoics.swims import config
from taoics.common.device.vac.vaclib import TPG262

vac = TPG262(
    tty = config.get(DEVICE_NAME, "tty"),
    baudrate = config.getint(DEVICE_NAME, "serial_baudrate"),
    parity = config.get(DEVICE_NAME, "serial_parity"),
    bytesize = config.getint(DEVICE_NAME, "serial_bytesize"),
    stopbits = config.getint(DEVICE_NAME, "serial_stopbits"),
    timeout = config.getint(DEVICE_NAME, "serial_timeout"),
    logger = logger,
    mysql = mysql
    )
del config, TPG262
