from concurrent.futures import process
from taoics.tardys import config,config_mysql
from terminal_interface import TerminalInterface
from messia_client import MessiaClient
from detlib import Detlib
from common import Common
from decimal import Decimal
import logging, subprocess, argparse
import datetime
import threading.Thread


class DetError(Exception):
    pass

class Det:
    def __init__(self, logger=None):
        self.interface = TerminalInterface()
        self.client = MessiaClient()
        self.detlib = Detlib()
        self.common = Common()
        self.name = "det"
        self.logger = logger or logging.getLogger(__name__)
        self.inscode = config.get(self.name, "inscode")
        self.inscode_eng = config.get(self.name, "inscode_eng")
        self.rawdir = config.get(self.name, "rawdir")
        self.rsltdir = config.get(self.name, "rsltdir")
        self.messiadir = config.get(self.name, "messiadir")
        self.messia = config.get("hostname", "messia")
        self.gesica = config.get("hostname", "gesica")
        self.mysql = config_mysql(self.name) #detのインスタンス

    ###############################################################
    ## general
    ###############################################################

    def get_utc_str(self):
        return f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%d%H%M%S}"

    ###############################################################
    ## SQL general (commonにいれたいけど。。。)
    ###############################################################
    """
    def _select_status_values(self, keys):
        vals = [self.mysql.select_status(where={"NAME": key}) for key in keys] 
        return vals

    def select_status_values(self, keys):
        #Args:
        #    keys(list) : list of parameters you want
        #Returns:
        #    vals(list) : list of parameter value
        

        vals = [self.mysql.select_status(where={"NAME": key}) for key in keys]     
        vals = [val[0]["value"] for val in vals]
        return vals

    def select_status_dict(self, keys):
    #    Args:
    #        keys(list) : list of parameters you want
    #    Returns:
    #        vals(dict) : {param1 : param_value1, param2 : param_value2, ... }
    

        vals = [self.mysql.select_status(where={"NAME": key}) for key in keys]   
        print(vals)  
        dic = {val[0]["name"]:val[0]["value"] for val in vals}
        return dic
    """
    ###############################################################
    ## frame_id_related
    ###############################################################

    def get_current_frame_id(self):
        val = self.mysql.select_status(where={"NAME": "FRAMEID_ENG"})

        if len(val) == 0:
            _err = "No 'FRAMEID_ENG' found in the status table '{}'.".format(self.mysql.table_status)
            self.logger.error(_err)
            raise DetError(_err)

        return val[0]["value"]


    def get_next_frame_id(self):
        ## Get Frame-id from db (for testing).

        inscode = self.inscode_eng

        current_id = self.get_current_frame_id()

        new_id =int( current_id.replace(inscode, "")) + 1
       
        frame_id = "{}{:08d}".format(inscode, new_id)

        self.mysql.update_status_values({"FRAMEID_ENG": frame_id})

        return frame_id

    ###############################################################
    ## data acquisition related
    ###############################################################
    
    def show_setting(self):
        keys = ["SMPLMODE", "N_OUT", "NSAMPLE", "NSURAMP", "NOSAMPLE", "NRESET", "EXP_TIME", "RST_SUB", "REF_SUB"]

        dic = self.common.select_status_dict(keys)
        #print(dic)
        
        for item, key in dic.items():
            print("{} : {}".format(item, key))
        

    def load_setting(self):
        """
        Returns:
            vals(list):[clock_pattern, n_x, n_y, coding, n_sample, n_sur, exp_time_01]
        """
        keys = ["SPV", "N_X", "N_Y", "CODING", "NSAMPLE", "NSURAMP", "EXP_TIME", "NRESET"]
        vals = self.common.select_status_values(keys)
        vals, n_reset = vals[:-1], vals[-1]
        #print(vals)
        vals[-1] = int(Decimal(vals[-1])*10) # change exposure time in second to in 0.1 second
        return vals, n_reset

    """acq_frameはリセット回数が１回のみ
    def reset_frame(self, setting):
        setting[-1] = "hpk2015_rst"
        self.interface.tardys_daq(self.messiadir, *setting, frame_id, self.rawdir)
    """

    def acq_frame(self, frame_id = None):
        #print(self.mysql.select_status(where={"NAME": "EXP_TIME"}))
        exp_time = float(self.mysql.select_status(where={"NAME": "EXP_TIME"})[0]["value"])
        sample_mode = self.mysql.select_status(where={"NAME": "SMPLMODE"})[0]["value"]

        setting, n_reset = self.load_setting() #n_resetはリセット回数を指定できるようになってからどうするか決める。リセットフレームは最後の一回以外捨てていいなららくだけど。

        if frame_id is None:
            frame_id = self.get_next_frame_id()

        rawdir = f'{self.rawdir}{sample_mode}/{self.get_utc_str()}/'

        self.show_setting()
        self.interface.tardys_daq(self.messia, self.gesica, self.messiadir, *setting, rawdir, frame_id)

        #rawdir, self.rsltdir, frame_id ,exp_time, sample_mode wo watasu

        return rawdir, frame_id

        #thread = threading.Tread(target=self.detlib.create_fits, args = [rawdir, self.rsltdir, frame_id ,exp_time, sample_mode] )
        #thread.daemon=True
        #thread.start()

        
if __name__ == "__main__":
    det = Det()

    #keys = ["SAMPLING_MODE", "N_CH", "N_SAMPLE", "N_SUR", "N_OSAMPLE", "N_RESET", "EXP_TIME", "REF_SUB"]

    #print(det._select_status_values(keys))
    det.show_setting()
    det.load_setting()
    det.acq_frame()






