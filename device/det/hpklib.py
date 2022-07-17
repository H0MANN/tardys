#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import commands
import datetime
import logging
import math
import os
import threading
import time
import astropy
import astropy.time
import astropy.units
import astropy.coordinates

from taoics import APP_NAME
from taoics.swims import config, config_mysql, SWIMSError
from taoics.swims.device.det.ideclient import IDEError
from taoics.swims.device.det.hxrgbase import HXRGBase
from taoics.swims.device.det.fits_header_handler import BasicHeaderHandler
from taoics.swims.device.det.fowler_data_util import FowlerDataWatcher
from taoics.swims.device.det.ramp_data_util import RampDataWatcher


##########################################################################
_LOGGER = logging.getLogger(APP_NAME)
#_LOGGER.setLevel(10)


##########################################################################
class HXRGError(SWIMSError):
    pass


##########################################################################
class HXRG(object):

    T_SET_CONFIG_PARAM = 0.5  ## 'Set configuration parameters' in HXRGLog.txt

    T_CALC_FOWLER = 2.0  ## Fowler CDS calculation
#    T_CALC_RAMP = 20  ## Ramp calculation

    TIMEOUT_MARGIN_ACQUIRE = 60.0 #10.0 ## wait for 't_obs + this' seconds
    # HXRGLog.txt shows that 'CDS calc' would take 5 sec at a maximum.

    def __init__(self, device_name, evt_interrupt=None, logger=None):
        self.name = device_name
        self.rawdir = config.get(self.name, "rawdir")
        self.nfsdir = config.get(self.name, "nfsdir")
        self.inscode = config.get(self.name, "inscode")
        self.inscode_eng = config.get(self.name, "inscode_eng")
        self.frameid_index = config.getint(self.name, "frameid_index")
        self.create_sci_data = config.getboolean(self.name, "create_sci_data")

        self.h2rg_id = config.getint(self.name, "h2rg-id")
        self.asic_id = config.getint(self.name, "asic-id")

        self.rot_ccw = config.getfloat(self.name, "rot_ccw")
        self.flip_x = config.getboolean(self.name, "flip_x")
        self.flip_y = config.getboolean(self.name, "flip_y")

        self.evt_interrupt = evt_interrupt or threading.Event()

        self.logger = logger or logging.getLogger(__name__)

        self.mysql.update_status_values(
            {"CIFS_MOUNT": os.path.exists(self.rawdir)}
            )

        cmd = "/usr/sbin/showmount -e | grep {} | wc -l".format(config.get("hostname", "obcp"))
        errnum, ret = commands.getstatusoutput(cmd)
        if errnum == 0 and ret == "1":
            val = True
        else:
            val = False
        self.mysql.update_status_values(
            {"NFS_MOUNT": val}
            )

        ## HXRG base module
        self.base = HXRGBase(
            device_name = self.name,
            logger = self.logger,
            evt_interrupt = self.evt_interrupt)

        ## shortcuts for HXRGBase methods.
        for key in [
            "ping",
            "initialize",
            "powerup_ASIC", "reset_ASIC", #"powerdown_ASIC", 
            "download_MCD", "download_MCD_file",
#            "get_config", "get_ASIC_power", "get_telemetry",
#            "set_detector",
#            "set_fs_mode",
#            "set_fs_param",
#            "set_ramp_param",
#            "set_win_param",
#            "set_win_mode",
#            "set_gain",
#            "set_warm_test",
#            "set_global_reset",
#            "set_enhanced_clock",
#            "set_preamp_reset_per_row",
#            "set_KTC_removal",
#            "set_buf_current_mode",
#            "set_preamp_input_scheme",
#            "set_preamp_input",
#            "set_idle_mode_option",
#            "set_output_reset_frame",
#            "set_pulse_LED",
#            "set_clock_SCA_in_drop_frame",
#            "stop_acquisition", "halt",
#            "acquire_ramp",
#            "acquire_single_frame",
#            "acquire_CDS",
#            "acquire_CDSNoise",
            "get_system_gain_image",
            "get_MUX_gain",
            "is_fs_mode_fowler",
            "is_win_mode_full"
            ]:

            setattr(self, key, getattr(self.base, key))

        ## shortcuts for HXRGBase.IDEClient methods/properties.
        for key in ["connect", "disconnect", "is_connected", "reconnect"]:
            setattr(self, key, getattr(self.base.ide, key))

        ## upload values defined in config.ini.
        for key in ["opt_arm", "det_ch", "h2rg-id", "asic-id", "jade2-id", "usb-id", "dc5v-id", "sam-id", "crval1", "crval2", "cd1_1", "cd1_2", "cd2_1", "cd2_2", "ctype1", "ctype2", "cunit1", "cunit2", "crpix1", "crpix2", "lonpole", "wcs-orig", "detpxsz1", "detpxsz2", "coadd", "gain", "prd-min1", "prd-rng1", "prd-min2", "prd-rng2", "efp-min1", "efp-rng1", "efp-min2", "efp-rng2", "bin-fct1", "bin-fct2", "bscale", "bzero", "bunit", "detector", "dispaxis", "wav-min", "wav-max", "wavelen"]:
            self.mysql.update_status_values({key.upper(): config.get(self.name, key)})#, update_if_new=False)

        ## update CDELT values.
        cdelt1 = (config.getfloat(self.name, "cd1_1")**2 + config.getfloat(self.name, "cd1_2")**2)**0.5
        cdelt2 = (config.getfloat(self.name, "cd2_1")**2 + config.getfloat(self.name, "cd2_2")**2)**0.5
        self.mysql.update_status_values({"cdelt1": "{:20.8f}".format(cdelt1), "cdelt2": "{:20.8f}".format(cdelt2)})  # "20.8f" comes from Subaru Fits rule.

        return


    def __repr__(self):
        return "<{} object ({}, server=({},{})) at {}>".format(
            self.__class__.__name__,
            self.base.ide.hostname,
            self.base.ide.host,
            self.base.ide.port,
            hex(id(self))
            )


    @property
    def mysql(self):
        mysql = config_mysql(self.name)
        mysql.logger = self.logger
        return mysql


    def load_params(self):
        ## load parameter values.
        try:
            self.get_config()

        except Exception as err:
            self.logger.warn(err)
            self.base.ide.flush_que_err()
            self.base.ide.flush_recv_buffer()

            ## loads the latest parameters saved in SQL.
            for key, val in self.base.ARGNAMES.items():
                row = self.mysql.select_status(where={"NAME": val})
                if len(row) > 0:
                    setattr(self.base, "_{}".format(key), row[0]["value"])

            self.logger.warn("Loaded parameter values from MySQL because 'get_config' failed. Please check if the parameters are identical to those in HxRG.")

        return


    def powerdown_ASIC(self):
        self.base.powerdown_ASIC()
        self.mysql.update_status_values({"POWERDOWN": True})
        self.mysql.update_status_values({"INITIALIZED": False})
        return


    def start_up(self):
        vals = {
            "mux_type": config.getfloat(self.name, "mux_type"),
            "n_output": config.getfloat(self.name, "n_output"),
            "fs_mode": config.getfloat(self.name, "fs_mode"),
            "n_reset": config.getfloat(self.name, "n_reset"),
            "n_read": config.getfloat(self.name, "n_read"),
            "n_drop": config.getfloat(self.name, "n_drop"),
            "n_ramp": config.getfloat(self.name, "n_ramp"),
            "n_group": config.getfloat(self.name, "n_group"),
            "t_exp": config.getfloat(self.name, "t_exp"),
            "win_mode": config.getfloat(self.name, "win_mode"),
            "preamp_gain": config.getfloat(self.name, "preamp_gain"),
            "enhanced_clock": config.getfloat(self.name, "enhanced_clock"),
            "pulse_led": config.getfloat(self.name, "pulse_led"),
            "idle_mode_option": config.getfloat(self.name, "idle_mode_option"),
            "buf_current_mode": config.getfloat(self.name, "buf_current_mode")
            }

        try:
            self.ping()
        except IDEError:
            self.initialize()

        self.get_config()
#        self.load_params()

        self.set_detector(disable_skip=True)

        self.set_fs_mode_to_fowler(disable_skip=True)

        self.set_ramp_param(n_reset=vals["n_reset"], n_read=vals["n_read"],
                            n_group=vals["n_group"], n_ramp=vals["n_ramp"],
                            n_drop=vals["n_drop"], disable_skip=True)

        self.set_fs_param(n_reset=vals["n_reset"], n_read=vals["n_read"],
                          n_group=vals["n_group"], n_ramp=vals["n_ramp"],
                          t_exp=vals["t_exp"], disable_skip=True)

        self.set_win_mode_to_full(disable_skip=True)

        self.set_gain(vals["preamp_gain"], disable_skip=True)

        self.set_enhanced_clock(vals["enhanced_clock"], disable_skip=True)

        self.set_pulse_LED(vals["pulse_led"], disable_skip=True)

        self.set_idle_mode_option(vals["idle_mode_option"], disable_skip=True)

        self.set_buf_current_mode(vals["buf_current_mode"], disable_skip=True)

        self.get_ASIC_power()

        self.get_telemetry()

        ## check if values are correct.
        self.get_config()
        for key, val in vals.items():
            _val = getattr(self.base, key)
            if _val != val:
                _err = "Parameter '{}' should be '{}', not '{}'.".format(key, repr(val), repr(_val))
                self.logger.error(_err)
                raise ValueError(_err)

            self.logger.debug("Parameter '{}' = {}: ok".format(key, val))

        self.mysql.update_status_values({"INITIALIZED": True})
        self.mysql.update_status_values({"POWERDOWN": False})

        return


    ###########################################################
    ##  HXRGBase Commands for getting status
    ###########################################################
    def get_config(self):
        vals = self.base.get_config()
        self.mysql.update_status_values(vals)
        return vals


    def get_ASIC_power(self):
        vals = self.base.get_ASIC_power()
        self.mysql.update_status_values(vals)
        return vals


    def get_telemetry(self):
        vals = self.base.get_telemetry()

        for key, val in vals.items():
            if val =="-NaN":
                vals[key] = 0

        self.mysql.update_status_values(vals)
        return vals


    ###########################################################
    ##  HXRGBase Commands for setting parameters
    ###########################################################
    def ___mysql_update_status_values_for_set_method(self, dict_):
        vals = {}
        for key, val in dict_.items():
            if key in self.base.ARGNAMES.keys():
                vals[self.base.ARGNAMES[key]] = val

        self.mysql.update_status_values(vals)

        return


    def _mysql_update_status_values_for_set_method(self, keys):
        vals = {}
        for key in keys:
            if key in self.base.ARGNAMES.keys():
                vals[self.base.ARGNAMES[key]] = getattr(self.base, key)

        self.mysql.update_status_values(vals)

        return


    def set_detector(self, *args, **kwargs):
        ret = self.base.set_detector(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_detector)

        return ret


    def set_fs_mode(self, *args, **kwargs):
        ret = self.base.set_fs_mode(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_fs_mode)

        if self.base.is_fs_mode_fowler():
            self.update_t_obs_fowler()
        else:
            self.update_t_obs_ramp()

        return ret
    def set_fs_mode_to_fowler(self, *args, **kwargs):
        return self.set_fs_mode(1, *args, **kwargs)
    def set_fs_mode_to_ramp(self, *args, **kwargs):
        return self.set_fs_mode(0, *args, **kwargs)


    def set_fs_param(self, *args, **kwargs):
        ret = self.base.set_fs_param(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_fs_param)

        self.update_t_obs_fowler()

        return ret


    def set_ramp_param(self, *args, **kwargs):
        ret = self.base.set_ramp_param(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_ramp_param)

        self.update_t_obs_ramp()

        return ret


    def set_win_mode(self, *args, **kwargs):
        ret = self.base.set_win_mode(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_win_mode)

        return ret
    def set_win_mode_to_full(self, *args, **kwargs):
        return self.set_win_mode(0, *args, **kwargs)
    def set_win_mode_to_window(self, *args, **kwargs):
        return self.set_win_mode(1, *args, **kwargs)


    def set_win_param(self, *args, **kwargs):
        ret = self.base.set_win_param(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_win_param)

        ## photon collecting time per pixel
        # T.B.D.

        ## overhead for taking raw frames excluding t_pix
        # T.B.D

        return ret


    def set_gain(self, *args, **kwargs):
        ret = self.base.set_gain(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_gain)

        return ret


    def set_warm_test(self, *args, **kwargs):
        ret = self.base.set_warm_test(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_warm_test)

        return ret


    def set_global_reset(self, *args, **kwargs):
        ret = self.base.set_global_reset(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_global_reset)

        return ret


    def set_enhanced_clock(self, *args, **kwargs):
        ret = self.base.set_enhanced_clock(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_enhanced_clock)

        return ret


    def set_preamp_reset_per_row(self, *args, **kwargs):
        ret = self.base.set_preamp_reset_per_row(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_preamp_reset_per_row)

        return ret


    def set_KTC_removal(self, *args, **kwargs):
        ret = self.base.set_KTC_removal(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_KTC_removal)

        return ret


    def set_buf_current_mode(self, *args, **kwargs):
        ret = self.base.set_buf_current_mode(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_buf_current_mode)

        return ret


    def set_preamp_input_scheme(self, *args, **kwargs):
        ret = self.base.set_preamp_input_scheme(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_preamp_input_scheme)

        return ret


    def set_preamp_input(self, *args, **kwargs):
        ret = self.base.set_preamp_input(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_preamp_input)

        return ret


    def set_idle_mode_option(self, *args, **kwargs):
        ret = self.base.set_idle_mode_option(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_idle_mode_option)

        return ret


    def set_output_reset_frame(self, *args, **kwargs):
        ret = self.base.set_output_reset_frame(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_output_reset_frame)

        return ret


    def set_pulse_LED(self, *args, **kwargs):
        ret = self.base.set_pulse_LED(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_pulse_LED)

        return ret


    def set_clock_SCA_in_drop_frame(self, *args, **kwargs):
        ret = self.base.set_clock_SCA_in_drop_frame(*args, **kwargs)

        if ret is not None:
            self._mysql_update_status_values_for_set_method(self.base.keys_set_clock_SCA_in_drop_frame)

        return ret


    def set_h2rg(self, 
                 fs_mode, # 1 ('f'owler) or 0 ('r'amp)
                 t_pix,  # exposure time per pixel
                 n_read=None,  # required in fowler mode
                 n_output=None,  # 1, 4, or 32 ch readout
                 n_reset=None,
                 x_start=None, x_stop=None,
                 y_start=None, y_stop=None,
                 use_default=False
                 ):

        if t_pix is None:
            _err = "'t_pix' must be given, not {}.".format(t_pix)
            self.logger.error(_err)
            raise ValueError(_err)

        ## set_detector (affect to frame time  't_read'.)
        self.set_detector(n_output=n_output, mux_type=None,
                          use_default=use_default)

        ## full/window mode
#        if None in [x_start, x_stop, y_start, y_stop]:
#            if x_start == 0 and x_stop == 2047 and y_start = 0 and y_stop = 2047
            
        ## set_fs_mode
        self.set_fs_mode(fs_mode=fs_mode, use_default=use_default)

        ## set_**_param
        if self.base.is_fs_mode_fowler():
            if n_read is None:
                n_read = self.base.n_read
#                _err = "Fowler mode requires 't_pix' and 'n_read'."
#                self.logger.error(_err)
#                raise ValueError(_err)

            t_exp = self.get_t_exp_in_fowler(t_pix=t_pix, n_read=n_read)
            self.set_fs_param(n_reset=n_reset, n_read=n_read, t_exp=t_exp,
                              use_default=use_default)

        else:  ## ramp
            n_read = int(math.ceil(float(t_pix) / self.base.t_read) + 1)
            self.set_ramp_param(n_reset=n_reset, n_read=n_read,
                                use_default=use_default)

        self.mysql.update_status_values({"T_CMD": t_pix})
        
        return


    def set_h2rg_with_default(self, use_default=True, *args, **kwargs):
        return self.set_h2rg(use_default=use_default, *args, **kwargs)


    def get_t_exp_in_fowler(self, t_pix, n_read=None):
        """
        Get HXRG exposure time in sec in Fowler mode.

        n_read: number of read out
        t_pix: net integration time per pixel in sec.
        """

        if n_read is None:
            n_read = self.base.n_read

        t_exp = float(t_pix) - float(n_read) * self.base.t_read

        if t_exp < 0:
            err = "'n_read={}' and 't_pix={}' result in a negative 't_exp'={}.".format(n_read, t_pix, t_exp)
            self.logger.error(err)
            raise ValueError(err)

        return t_exp


    ###########################################################
    ##  Utility Commands for T_OBS
    ###########################################################
    def update_t_obs_fowler(self):
        ## photon collecting time per pixel
        t_pix = self.base.t_read * self.base.n_read + self.base.t_exp
        self.mysql.update_status_values({"T_PIX": t_pix})

        ## overhead for taking raw frames excluding t_pix
        t_overhead = self.T_SET_CONFIG_PARAM
        t_overhead += self.base.t_read * self.base.n_reset
        t_overhead += self.base.t_read * self.base.n_read
        t_overhead += self.T_CALC_FOWLER  # must be added (acquireramp includes this).
        t_overhead += self.T_SET_CONFIG_PARAM

        self.mysql.update_status_values({"T_OVH": t_overhead})

        ## total observing time
        t_obs = t_pix + t_overhead
        self.mysql.update_status_values({"T_OBS": t_obs})

        self.logger.info("Updated 't_pix', 't_ovh' and 't_obs'.")

        return


    def update_t_obs_ramp(self):
        ## photon collecting time per pixel
        t_pix = self.base.t_read * (self.base.n_read - 1)
        self.mysql.update_status_values({"T_PIX": t_pix})

        ## overhead for taking raw frames
        t_overhead = self.T_SET_CONFIG_PARAM
        t_overhead += self.base.t_read * self.base.n_reset
        t_overhead += self.base.t_read * 1
#        t_overhead += self.T_CALC_RAMP
        t_overhead += self.T_SET_CONFIG_PARAM

        self.mysql.update_status_values({"T_OVH": t_overhead})

        ## total observing time
        t_obs = t_pix + t_overhead
        t_obs *= 1.015  ## margin

        self.mysql.update_status_values({"T_OBS": t_obs})

        self.logger.info("Updated 't_pix', 't_ovh' and 't_obs'.")

        return


    def get_t_obs(self):
        return float(self.mysql.select_status(where={"name": "T_OBS"})[0]["value"])


    def get_pixel_scale(self):
        cd11 = float(self.mysql.select_status(where={"name": "CD1_1"})[0]["value"])
        cd12 = float(self.mysql.select_status(where={"name": "CD1_2"})[0]["value"])
        cd21 = float(self.mysql.select_status(where={"name": "CD2_1"})[0]["value"])
        cd22 = float(self.mysql.select_status(where={"name": "CD2_2"})[0]["value"])

        xscale = (cd11**2 + cd12**2)**0.5  # [deg/pix]
        yscale = (cd21**2 + cd22**2)**0.5  # [deg/pix]

        xscale *= 3600.  # [arcsec/pix]
        yscale *= 3600.  # [arcsec/pix]

        return (xscale + yscale) / 2.


    ###########################################################
    ##  Utility Commands for image acquisition
    ###########################################################
    def get_current_frame_id(self):
        val = self.mysql.select_status(where={"NAME": "FRAMEID_ENG"})

        if len(val) == 0:
            _err = "No 'FRAMEID_ENG' found in the status table '{}'.".format(self.mysql.table_status)
            self.logger.error(_err)
            raise HXRGError(_err)

        return val[0]["value"]


    def get_next_frame_id(self):
        ## Get Frame-id from db (for testing).

        inscode = self.inscode_eng

        current_id = self.get_current_frame_id()

        if inscode in current_id:
            new_id = math.ceil(int(current_id.replace(inscode, "")) / 10.) * 10 + self.frameid_index
            new_id = int(new_id)
        else:
            new_id = self.frameid_index

        frame_id = "{}{:08d}".format(inscode, new_id)

        self.mysql.update_status_values({"FRAMEID_ENG": frame_id})

        return frame_id


    ###########################################################
    ##  IDE Commands for image acquisition
    ###########################################################
    def stop_acquisition(self):
        self.base.stop_acquisition()
#        self.set_idle_mode_option(1)
        return


    halt = stop_acquisition


    def acq_frame(self, frame_id, dset_id=None, dpos_id=None, exp_id=None):

        if frame_id.endswith(".fits"):
            frame_id = frame_id[:-5]

        if os.path.exists(os.path.join(self.nfsdir, frame_id + ".fits")):
            _err = "'{}' already exists in '{}'.".format(frame_id + ".fits", self.nfsdir)
            self.logger.error(_err)
            raise HXRGError(_err)

        self.mysql.update_status_values({"FRAMEID": frame_id})

        if dset_id is not None:
            self.mysql.update_status_values({"DSET-ID": dset_id})

        if dpos_id is not None:
            self.mysql.update_status_values({"DPOS-ID": dpos_id})

        if exp_id is not None:
            self.mysql.update_status_values({"EXP-ID": exp_id})

        ## Header worker thread
        hdr_w = BasicHeaderHandler(name=self.name, logger=self.logger,
                                   evt_interrupt=self.evt_interrupt)
        hdr_w.daemon = True
        self.hdr_w = hdr_w

        ## Data worker thread
        if self.base.is_fs_mode_fowler():
            DataWatcher = FowlerDataWatcher
        else:
            DataWatcher = RampDataWatcher

        dat_w = DataWatcher(nfsdir=self.nfsdir, rootdir=self.rawdir, 
                            logger=self.logger,
                            h2rg_id=self.h2rg_id, asic_id=self.asic_id,
                            evt_interrupt=self.evt_interrupt)
        dat_w.daemon = True
        self.dat_w = dat_w

        try:
            hdr_w.start()

            dat_w.start()

            hdr_w.process_init()

#            self.set_idle_mode_option(0)

            self.acquire_ramp(frame_id, hdr_w, dat_w)

            if self.create_sci_data:
                dat_w.cook(frame_id, hdr_w.cast_values(),
                           rot_ccw=self.rot_ccw,
                           flip_x=self.flip_x,
                           flip_y=self.flip_y)  ## async

        except Exception as err:
            hdr_w.stop()
            dat_w.stop()
            err.message += ". '{}' not created.".format(frame_id)
            raise err

        finally:
            try:
                ## execute when succeeded or error.
                ## not execute when "stop_acquisition" issued
                ## because the similar care is taken in it.
                if not self.base.is_executing_stop_acquisition():
                    self.base.ide.stop_executing()
#                    self.set_idle_mode_option(1)

            except:
                pass

        return (os.path.join(self.nfsdir, frame_id), dat_w.dir)


    def acquire_ramp(self, frame_id, hdr_w, dat_w):
        done_update_sql_mid = False
        done_acquisition = False

        ## 't_obs' is already set by set_**_param.
        t_obs = self.get_t_obs()
        self.logger.info("Start Acquisition (t_obs={})".format(t_obs))

        ## starts acquisition asynchronously.
        self.base.acquire_ramp()
        self.logger.info("Waiting for acquisition done...")

        ## time acuisition started (but uncertainty of a few sec exists due to IDE polling cycle).
        t_str = time.time()

        ## obtains milestone time.
        t_end = t_str + t_obs
        t_mid = (t_str + t_end) / 2.

        for key, t in zip(["MID", "END"], [t_mid, t_end]):
            self.logger.info("Estimated {} time: {}".format(key, datetime.datetime.utcfromtimestamp(t).strftime("%Y%m%d_%H%M%S.%f")[:-3]))

        ## updates STR values.
        hdr_w.process_str_async()

        while 1:
            ## if acquireramp is failed or interrupted, error is raised.
#            self.logger.warn("self.base.ide.catch_que_err start")
            self.base.ide.catch_que_err()
#            self.logger.warn("self.base.ide.catch_que_err done")

#            self.logger.warn("self.base.ide.is_executing start")
            if not self.base.ide.is_executing():
                self.base.ide.wait()
                done_acquisition = True
                break
#            self.logger.warn("self.base.ide.is_executing done")

            t_now = time.time()

            if t_now > t_mid and not done_update_sql_mid:
                done_update_sql_mid = True
                hdr_w.process_mid_async()

            if t_now > t_end + self.TIMEOUT_MARGIN_ACQUIRE:
                _err = "Acquisition not finished in time."
                self.logger.error(_err)

                try:
                    self.base.halt()

                except:
                    pass

                raise HXRGError(_err)

            time.sleep(1e-2)

        if not done_acquisition:
            _err = "Acquisition failed."
            self.logger.error(_err)
            raise HXRGError(_err)

#        self.logger.warn(datetime.datetime.utcfromtimestamp(time.time()).strftime("%Y%m%d_%H%M%S.%f")[:-3])
        self.logger.info("expected_completion_time - actual_time = {:.3f} sec.".format(t_end - time.time()))
#        self.logger.info("Difference between the expected and actual time finished: {:.3f} sec".format(t_end - time.time()))

        self.mysql.update_status_values({"RAWDIR": dat_w.dir})

        ## updates END values.
        hdr_w.process_end()
        hdr_w.stop()  ## just in case

        ## wait for the first raw frame to come.
        timeout_first_frame = 15
        t0 = time.time()
        t1 = t0 + 0.1  # time interval for logging.
        while 1:
            if dat_w.proc.first_frame is not None:
                break

            if time.time() - t0 > timeout_first_frame: 
                _err = "No data has been written into the directory."
                self.logger.error(_err)
                raise HXRGError(_err)

            if time.time() > t1:
                self.logger.warn("still waiting for FITS data to come...")
                t1 = time.time() + 0.1

            time.sleep(1e-2)

        ## stop watching new FITS files.
        dat_w.stop()

        ## read the header of a first raw data.
        hdr_w.process_IDE_Header(dat_w.proc.first_frame.header)

        if hdr_w.data is None:
            _err = "Failed to collect Header data."
            self.logger.error(_err)
            raise HXRGError(_err)

        return


##########################################################################
if __name__ == "__main__":

    det_r2 = HXRG("det_r2", logger=_LOGGER)
#    if det_r2.logger.level == 0:
    det_r2.logger.setLevel(20)
