#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import logging

from taoics.common import TAOICSError, load_config, CONFIG_FILENAME


##########################################################################
MODULE_NAME = __name__
logging.getLogger(MODULE_NAME)


##########################################################################
class SWIMSError(TAOICSError):
    pass
del TAOICSError


##########################################################################
## Loads config file.
_CONFIG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), CONFIG_FILENAME)
config = load_config(_CONFIG_FILE)
del load_config, CONFIG_FILENAME, _CONFIG_FILE


##########################################################################
def get_server_address(device_name):
    import socket
    from taoics.common import get_server_address
    hostname, port = get_server_address(device_name, config)
    ipaddr = socket.gethostbyname_ex(hostname)[-1][-1]
    return ipaddr, port


##########################################################################
def get_pidfile_path(device_name):
    from taoics.common import get_pidfile_path
    return get_pidfile_path(device_name, config)


##########################################################################
def get_hbfile_path(device_name):
    from taoics.common import get_hbfile_path
    return get_hbfile_path(device_name, config)


##########################################################################
def config_logger(module_name):
    from taoics.common.util.loggerlib import config_logger
    return config_logger(module_name=module_name, config=config)


##########################################################################
def config_mysql(device_name=None):
    from taoics.common import config_mysql
    return config_mysql(device_name, config)


##########################################################################
def config_clientfordm(device_name, *args, **kwargs):
    from taoics.common.util.clientlib import ClientForDM
    host, port = get_server_address(device_name)
    return ClientForDM(host=host, port=port, *args, **kwargs)


##########################################################################
def config_clientwithint(device_name, *args, **kwargs):
    from taoics.common.util.clientlib import ClientWithINT
    host, port = get_server_address(device_name)
    return ClientWithINT(host=host, port=port, dm_name=device_name, *args, **kwargs)


##########################################################################
del os, logging


##########################################################################
class ColdHead(object):
    def __init__(self, loglevel=10):
        from taoics.swims.device.pdu_b import build_pdu
        pdu_b = build_pdu(loglevel=loglevel)
        self.MAIN = pdu_b.COLDHEAD_MAIN
        self.MOSU = pdu_b.COLDHEAD_MOSU

        return


##########################################################################
def load_ics_modules(loglevel=20):
    class ICS(object):
        pass

    import logging
    logger = logging.getLogger(MODULE_NAME)

    ics = ICS()
    ics.config = config
    ics.config_mysql = config_mysql


    ## PDU
    """
    from taoics.swims.device.pdu_a import build_pdu
    ics.pdu_a = build_pdu(loglevel=loglevel)
    setattr(ics, ics.pdu_a._host.split(".")[0], ics.pdu_a)

    from taoics.swims.device.pdu_b import build_pdu
    ics.pdu_b = build_pdu(loglevel=loglevel)
    setattr(ics, ics.pdu_b._host.split(".")[0], ics.pdu_b)
    
    from taoics.swims.device.pdu_c import build_pdu
    ics.pdu_c = build_pdu(loglevel=loglevel)
    setattr(ics, ics.pdu_c._host.split(".")[0], ics.pdu_b)
    """    
    from taoics.swims.device.pdu import build_pdus
    ics.pdu = build_pdus(loglevel=loglevel)

    
    ## Wheel system
    from taoics.swims.device.wheel import build_wheel_client
    ics.wheel = build_wheel_client(loglevel=loglevel)


    ## MOSU
    from taoics.swims.device.mosu import build_mosu_client
    ics.mosu = build_mosu_client(loglevel=loglevel)


    ## TEXIO
    from taoics.swims.device.texio import build_texio
    ics.texio = build_texio(loglevel=loglevel)


    ## detctors
#    try:
    from taoics.swims.device.det_b import build_det_group_client
    ics.det_b = build_det_group_client(loglevel=loglevel)
#    except:
#        logger.warn("Blue detector (det_b) arrays not in service.")
#        ics.det_b = None

#    try:
    from taoics.swims.device.det_r import build_det_group_client
    ics.det_r = build_det_group_client(loglevel=loglevel)
#    except:
#        logger.warn("Red detector (det_r) arrays not in service.")
#        ics.det_r = None


    ## Coldhead
    from taoics.swims.device.cooler.cooler import Cooler
    ics.cooler = Cooler() #ColdHead(loglevel=loglevel)


    ## MESOffset
    from plugins.MESOffset_client import Client
    ics.mesoffset = Client()


    return ics
