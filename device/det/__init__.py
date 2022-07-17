#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


##########################################################################
def build_det(module_name, device_name, loglevel=None):
    import logging
    from taoics.swims.device.det.hxrglib import HXRG

    logger = logging.getLogger(module_name)

    if loglevel is not None:
        logger.setLevel(loglevel)

    return HXRG(device_name=device_name, logger=logger)


##########################################################################
def build_det_client(device_name, *args, **kwargs):
    from taoics.swims import config, get_server_address
    from taoics.swims.device.det.det_client import DetClient

    host, port = get_server_address(device_name)
    in_service = config.getboolean(device_name, "in_service")

    return DetClient(device_name=device_name, in_service=in_service, 
                     host=host, port=port, *args, **kwargs)


##########################################################################
def build_det_group_client(device_name, *args, **kwargs):
    import importlib
    import os

    from taoics import APP_NAME
    from taoics.swims import config
    from taoics.swims.device.det.det_client import DetGroupClient

    arrays = [v.strip() for v in config.get(device_name, "arrays").split(",")]

    clis = []
    for name in arrays:
        mod = importlib.import_module("{}.swims.device.{}".format(APP_NAME, name))

        clis.append(getattr(mod, "build_det_client")(*args, **kwargs))

    return DetGroupClient(device_name, clis)


