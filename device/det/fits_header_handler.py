#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import logging
import math
import queue as Queue
import threading
import time

import astropy
import astropy.time
import astropy.units
import astropy.coordinates
import astropy.io.fits
import numpy as np

from taoics import APP_NAME
from taoics.tardys import config, config_mysql


##########################################################################
_LOGGER = logging.getLogger(APP_NAME)
_LOGGER.setLevel(10)


##########################################################################
class FormattedFloat(float):
    def __new__(cls, value, formatstr=None):
        return float.__new__(cls, value)

    def __init__(self, value, formatstr=None):
        float.__init__(self)
        self.formatstr = formatstr

    def __str__(self):
        return self.formatstr % self


def my_format_float(value):
    if isinstance(value, FormattedFloat):
        value_str = str(value).upper()
    else:
        value_str = "%.16G" % value

    if "." not in value_str and "E" not in value_str:
        value_str += ".0"
    elif "E" in value_str:
        # On some Windows builds of Python (and possibly other platforms?) the
        # exponent is zero-padded out to, it seems, three digits.  Normalize
        # the format to pad only to two digits.
        significand, exponent = value_str.split("E")
        if exponent[0] in ("+", "-"):
            sign = exponent[0]
            exponent = exponent[1:]
        else:
            sign = ""
        value_str = "%sE%s%02d" % (significand, sign, int(exponent))

    # Limit the value string to at most 20 characters.
    str_len = len(value_str)
    if str_len > 20:
        idx = value_str.find("E")

        if idx < 0:
            value_str = value_str[:20]
        else:
            value_str = value_str[:20 - (str_len - idx)] + value_str[idx:]

    return value_str


astropy.io.fits.card._format_float = my_format_float


##########################################################################
class BaseHandler(threading.Thread):
    def __init__(self,
                 name,
                 que_err=None,
                 evt_interrupt=None,
                 evt_init=None, evt_str=None, evt_mid=None, evt_end=None,
                 logger=None,
                 *args, **kwargs):

        super(BaseHandler, self).__init__(*args, **kwargs)

        self.name = name

        self.que_err = que_err or Queue.Queue()

        self.evt_interrupt = evt_interrupt or threading.Event()
        self.evt_init = evt_init or threading.Event()
        self.evt_str = evt_str or threading.Event()
        self.evt_mid = evt_mid or threading.Event()
        self.evt_end = evt_end or threading.Event()

        self.logger = logger or _LOGGER
        if self.logger.level == 0:
            self.logger.setLevel(10)

        self._done = {"INIT": False, "STR": False, "MID": False, "END": False}
        self._evt = {"INIT": self.evt_init,
                     "STR": self.evt_str,
                     "MID": self.evt_mid,
                     "END": self.evt_end}

        self.timings = ("INIT", "STR", "MID", "END")

        self._stop_loop  = False

        return


    @property
    def mysql(self):
        mysql = config_mysql(self.name)
        mysql.logger = self.logger
        return mysql


    @property
    def data(self):
        return self._fetch_data()


    def run(self):
        try:
            #infinite loop
            while 1:
                if self.evt_interrupt.is_set() or self._stop_loop:
                    break

                if not self._done["INIT"] and self._evt["INIT"].is_set():
                    self.process_init()

                if not self._done["STR"] and self._evt["STR"].is_set():
                    self.process_str()

                if not self._done["MID"] and self._evt["MID"].is_set():
                    self.process_mid()

                if not self._done["END"] and self._evt["END"].is_set():
                    self.process_end()
                    break

                time.sleep(1e-2)

        except Exception as err:
            self.logger.error(err)
            self.que_err.put(err)
            raise err

        return


    def stop(self):
        self._stop_loop = True
        return


    def process_init(self):
        #header_table(det)を消す
        self.mysql.drop_header_table()
        #tar_header.detをtar_header.det_masterからコピーしてくる
        self.mysql.copy_from_header_master()

        self.logger.info("Initialized header table '{}'.".format(self.mysql.table_header))

        self._update_table("INIT")

        return
    def process_init_async(self):
        self.evt_init.set()
        return


    def process_str(self):
        self._update_table("STR")
        return
    def process_str_async(self):
        self.evt_str.set()
        return


    def process_mid(self):
        self._update_table("MID")
        return
    def process_mid_async(self):
        self.evt_mid.set()
        return


    def process_end(self):
        if not self._done["MID"]:
            self.process_mid()
        self._update_table("END")
        self.stop()
        return
    def process_end_async(self):
        self.evt_end.set()
        return


    def process_IDE_Header(self, hdr_ide):
        self.update_via_IDE_Header(hdr_ide)
        return


    def update_table(self, timing):
        raise NotImplementedError


    def _update_table(self, timing):
        self._validate_timing(timing)

        if self._done[timing]:
            return

        self.logger.info("Updating '{}'.".format(timing.upper()))

        self._done[timing] = True

        self.update_table(timing)

#        self._done[timing] = True  # DB sometimes becomes slow and thus flagging would be late and more '_update_table' call would happen.

        self.logger.info("Updated '{}'.".format(timing.upper()))

        return


    def _validate_timing(self, timing):
        if not timing in self.timings:
            _err = "'timing' must be any of {}.: {}".format(", ".join(self.timings), timing)
            raise ValueError(_err)
        return


    def _fetch_data(self):
        return self.mysql.select_header(order={"ID": "ASC"})


##########################################################################
class BasicHeaderHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(BasicHeaderHandler, self).__init__(*args, **kwargs)
        return


    def update_table(self, timing):
        self.update_via_inst_tables(timing)
        self.update_via_python_methods(timing)
        return


    def update_via_inst_tables(self, timing):

        """
        query = "SELECT Distinct(inst_table_name) FROM {}.{} WHERE fetch_timing = '{}' AND inst_table_name != '';".format(self.mysql.db_header, self.mysql.table_header, timing)
        lines = self.mysql.execute(query)
        table_list = []
        for line in lines:
            table_list.append(line[0])

        for table in table_list:
            query = "SELECT * from {}.{} WHERE NAME IN (SELECT inst_table_column_name FROM {}.{} WHERE fetch_timing = '{}' AND inst_table_name = '{}');".format(self.mysql.db_status, table, self.mysql.db_header, self.mysql.table_header, timing, table)
            lines = self.mysql.execute(query)
        """

        #fetch_timingがtimeingに一致し、かつ、inst_table_column_nameがからでないところを選んで、  
        lines = self.mysql.select_header(where={"fetch_timing": timing,
                                                "inst_table_column_name": "!"})

        d = {}
        for line in lines:
            d.update(self.update_via_inst_table(line))

        self.mysql.update_header_values(d)

        return


    def update_via_inst_table(self, record):
        vals = self.mysql.select_status(
            table = record["inst_table_name"], 
            where = {"NAME": record["inst_table_column_name"]}
            ) #inst_table_name=det, #inst_table_column_name=EXP-ID

        if len(vals) == 0:
            _err = "No such a keyword ({}) in status table ({}).".format(
                                record["inst_table_column_name"],
                                record["inst_table_name"])
            raise ValueError(_err)

        vals = vals[0]

#        self.mysql.update_header_values({record["header_keyword"]: vals["value"]})

        return {record["header_keyword"]: vals["value"]}


    def update_via_python_methods(self, timing):
        lines = self.mysql.select_header(where={"fetch_timing": timing,
                                                "updater": "python",
                                                "python_method": "!"})

        d = {}
        for line in lines:
            d.update(self.update_via_python_method(line))

        self.mysql.update_header_values(d)

        return


    def update_via_python_method(self, record):
        method = record["python_method"]
        if not hasattr(self, method):
            _err = "No such a method: {}".format(method)
            raise ValueError(_err)

        val = getattr(self, method)()

#        self.mysql.update_header_values({record["header_keyword"]: val})

        return {record["header_keyword"]: val}


    def update_via_IDE_Header(self, hdr_ide):
        lines = self.mysql.select_header(where={"updater": "IDE_Header"})

        d = {}
        XY_START_STOP = {"XSTART": 1, "XSTOP": hdr_ide["NAXIS1"],
                         "YSTART": 1, "YSTOP": hdr_ide["NAXIS2"]}
        for line in lines:
            if line["ide_header_keyword"] in XY_START_STOP.keys():
                if line["ide_header_keyword"] not in hdr_ide.keys():
                    val = XY_START_STOP[line["ide_header_keyword"]]
                else:
                    val = hdr_ide[line["ide_header_keyword"]]

            elif line["ide_header_keyword"] == "EXTEND":
                val = False  # raw frame should have EXTEND=False.

            else:
                val = hdr_ide[line["ide_header_keyword"]]

            d[line["header_keyword"]] = val

        self.mysql.update_header_values(d)

        return


    def get_UT(self, dt=None):
        dt = dt or datetime.datetime.utcnow()
        return dt.strftime("%H:%M:%S.%f")[:-3]


    def get_CLT(self, dt=None):
        dt = dt or datetime.datetime.utcnow()
        dt -= datetime.timedelta(hours=-4)  # UT -> HST
        return dt.strftime("%H:%M:%S.%f")[:-3]


    def get_LST(self, dt=None):
        dt = dt or datetime.datetime.utcnow()

        obslon = self.mysql.select_status(
            table = "observation", 
            where = {"NAME": "OBSLON"}
            )[0]["value"]

        ut1_utc = self.mysql.select_status(
            table = "observation", 
            where = {"NAME": "UT1-UTC"}
            )[0]["value"]

        t = astropy.time.Time(dt)

        try:
            t.delta_ut1_utc = float(ut1_utc)
            lst = t.sidereal_time("apparent", obslon)
            lst = lst.to_string(unit=astropy.units.hourangle, sep=":", pad=True, precision=3)

        except ValueError as e:
            self.logger.warn(e)
            lst = "##ERROR##"

        return lst


    def get_MJD(self, dt=None):
        dt = dt or datetime.datetime.utcnow()
        t = astropy.time.Time(dt)
        return t.mjd


    def get_CRVAL1(self):
        ra = self.mysql.select_status(table="observation", where={"NAME": "RA"})
        return astropy.coordinates.Angle("{} hours".format(ra[0]["value"])).deg


    def get_CRVAL2(self):
        dec = self.mysql.select_status(table="observation", where={"NAME": "DEC"})
        return astropy.coordinates.Angle("{} degrees".format(dec[0]["value"])).deg


    @property
    def _insrot(self):
        insrot = self.mysql.select_status(table="observation",
                                          where={"NAME": "INSROT"})
        return float(insrot[0]["value"]) * math.pi / 180


    @property
    def cdelt1(self):
        return float(self.mysql.select_status(where={"NAME": "CDELT1"})[0]["value"])


    @property
    def cdelt2(self):
        return float(self.mysql.select_status(where={"NAME": "CDELT2"})[0]["value"])


    def _get_swspa(self):
        swspa = float(self.mysql.select_status(table="observation", where={"NAME": "SWIMS_PA"})[0]["value"])
        return swspa * math.pi / 180
    def _get_CD_val(self, key):
        return float(self.mysql.select_status(where={"NAME": "CD{}".format(key)})[0]["value"])
    def _get_rotated_CD_matrix(self):
        pa = self._get_swspa()
        rot = np.array( ((np.cos(pa), np.sin(pa)), (-np.sin(pa), np.cos(pa))) )
        cd11 = self._get_CD_val("1_1")
        cd12 = self._get_CD_val("1_2")
        cd21 = self._get_CD_val("2_1")
        cd22 = self._get_CD_val("2_2")
        cd = np.array( ((cd11, cd12), (cd21, cd22)) )
        return np.dot(rot, cd)

    def get_CD1_1(self):
        return self._get_rotated_CD_matrix()[0][0]
    def get_CD1_2(self):
        return self._get_rotated_CD_matrix()[0][1]
    def get_CD2_1(self):
        return self._get_rotated_CD_matrix()[1][0]
    def get_CD2_2(self):
#        return self._get_CD_val("2_2")
        return self._get_rotated_CD_matrix()[1][1]


    def get_frameid(self, arm):
        arrays = config.get("det_{}".format(arm), "arrays")
        arrays = arrays.strip()

        if arrays == "":
            return ""

        arrays = arrays.split(",")

        for arr in arrays:
            if arr == "":
                continue
            res = self.mysql.select_status(table=arr, where={"NAME": "FRAMEID"})
            return res[0]["value"]

        return ""


    def get_frameid_blue(self):
        return self.get_frameid("b")


    def get_frameid_red(self):
        return self.get_frameid("r")


    def cast_values(self):
        hdr_out = []

        for line in self.data:
            
            key = line["header_keyword"]
            val = line["header_value"]
            typ = line["header_value_type"]
            fmt = line["header_value_format"]

            if key == "COMMENT":
                hdr_out.append(line)
                continue

            try:
                if typ == "str":
                    val = str(val)

                elif typ == "float":  # %f or %e
#                elif fmt.endswith("f"): # NG: not including %e.
#                    val = float(val)
                    val = FormattedFloat(val, fmt.upper())  # %xFx or %xEx.

                elif typ == "int":
                    val = int(float(val))

                elif typ == "bool":
                    if isinstance(val, bool):
                        val = val

                    elif isinstance(val, basestring):
                        if val.upper().startswith("T"):
                            val = True
                        else:
                            val = False

                    elif isinstance(val, (int, float)):
                        val = bool(val)

                    else:
                        _err = "$$${}: Invalid value for 'bool': {}".format(key, val)
                        self.det.logger.error(_err)
                        raise TypeError(_err)

                else:
                    _err = "$$${}: Unsupported Type: {}".format(key, typ)
                    self.det.logger.error(_err)
                    raise TypeError(_err)

            except:
                pass

            line["header_value"] = val

            hdr_out.append(line)

        return hdr_out


    def make_header(self, hdr_in=None):
        hdr_in = hdr_in or self.cast_values()

        hdr_out = astropy.io.fits.Header()

        for line in hdr_in:
            hdr_out[line["header_keyword"]] = (line["header_value"], line["header_comment"])

        return hdr_out

        
##########################################################################
def main():
    return


##########################################################################
if __name__ == "__main__":
    main()

    h = BasicHeaderHandler("det")
    h.logger.setLevel(20)
    h.daemon = True

    h.start()

    h.process_init()
    time.sleep(2)

    h.process_str_async()
    time.sleep(1)
    
    h.process_end()
#    h.process_end_async()
#    time.sleep(1)

#    print(h.data)

    import glob
    lst = glob.glob("/home/anir/share/yupa/Data/H2RG-196-ASIC-48/FSRamp/20190128012431/*fits")
    hdr_ide = astropy.io.fits.getheader(lst[0])

    h.process_IDE_Header(hdr_ide)

#    del a
#    a

    hdu = astropy.io.fits.PrimaryHDU()
    hdu.data = np.zeros((2048,2048))
    hdr_out = astropy.io.fits.Header()

    hdr_in = h.cast_values()
    for line in hdr_in:
        hdr_out[line["header_keyword"]] = (line["header_value"], line["header_comment"])

    hdr_out["NAXIS"] = (2, "Number of axes in frame")
    hdr_out["NAXIS1"] = (2048, "Number of axes in frame")
    hdr_out["NAXIS2"] = (2048, "Number of axes in frame")
#    print(hdr_out)
    hdu.header = hdr_out
#    hdu.header = h.make_header()
    hdu.writeto("a.fits")

#    for line in h.make_header():
#        print(line)
#        print(line["header_keyword"], "\t", line["header_value"], "\t", line["header_comment"])
#    print(vars(h))
#    err = h.que_err.get_nowait()
#    print(repr(err))
