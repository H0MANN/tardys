#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import sys
#sys.path.append('/home/tardys/')
#print(sys.path)

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


##########################################################################
if __name__ == "__main__":

    from taoics.common.device.vac.vac_utils import exec_TPG261
    from taoics.tardys.device.vac import build_vac

    exec_TPG261(build_vac())
