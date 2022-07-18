import subprocess
from taoics.tardys import config
import logging
import threading
import queue
import time
import subprocess
from fits_header_handler import BasicHeaderHandler

class TerminalInterface:
    def __init__(self):
        self.h = BasicHeaderHandler("det")

    ##########################################################
    ## command makeing related
    ##########################################################
    def quote(self, string):
        return "'"+str(string)+"'"

    def backquote(self, string):
        return "`"+str(string)+"`"

    def pipe(self, *args):
        return " | ".join(map(str, args))

    def doublepipe(self, *args):
        return " || ".join(map(str, args))

    def make_cmd(self, *args):
        return " ".join(map(str, args))

    #########################################################
    ## general
    #########################################################
    def mkdir(self, dir):
        subprocess.run(self.make_cmd("mkdir -p", dir), shell=True)


    ##########################################################
    ## process related
    ##########################################################

    def is_exist(self, process):
        ret = subprocess.run(self.pipe("ps aux", self.make_cmd("grep", process), "grep -v grep", "grep -v python", "wc -l"), shell=True, check = True, encoding="utf-8", stdout= subprocess.PIPE)
        #ret = subprocess.run("ps aux | grep " + process + " | grep -v grep | grep -v python | wc -l", shell=True, check=True, encoding="utf-8", stdout = subprocess.PIPE)
        return ret

    def kill_process(self, process): 
        # This may needs to be fixed.
        subprocess.run(self.make_cmd("kill -9", + self.backquote(self.make_cmd("pgrep -f", process)))) # pgrep : find process ID

    def start_process(self, process):
        subprocess.run(self.doublepipe(self.pipe("ps -ef", "grep ds9" ,"grep -v grep"), process))

    #########################################################
    ## ds9 related
    #########################################################

    #def show_frames(self, frame_name):
    #    subprocess.run(self.make_cmd("xpaset -p ds9 file", ))

    ##########################################################
    ## messia6 related
    ##########################################################

    #----------------------------------------------------------
    #  shellscript related
    #----------------------------------------------------------

    def init_irca(self, server, gesica_addr, irca_id):
        subprocess.run(self.make_cmd("sh init_irca3.sh" ,server, gesica_addr, irca_id), shell=True)

    def tardys_daq(self, messia_addr, gesica_addr, messiadir, clock_pattern, n_x, n_y, coding, n_sample, n_sur, exp_time_01, raw_data_dir, file_prefix):
        #この時点では何もしない
        h.daemon=True
        h.start()

        #timingがINITの項目についてテーブルが変更
        h.process_init()

        h.process_str_async()

        p = subprocess.Popen(self.make_cmd("sh", messiadir+"tardys_daq.sh", messia_addr, gesica_addr, clock_pattern, n_x, n_y, coding, n_sample, n_sur, exp_time_01, raw_data_dir, file_prefix), shell=True)

        while p.poll() is None:
            time.sleep(1)
            logging.info("子プロセス実行中")

        h.process_mid_async()

        h.process_end()

    #----------------------------------------------------------
    #  ~/messia6/local/m related
    #----------------------------------------------------------

    def mf2_com(self, messiadir , server, gesica_addr, irca_id, cmd): #''をいれる
        """
        Args:
            messiadir(str) : directory messia softwares
            server(str) : messia host computer ip address
            gesica_addr(str) : gesica ip address
            irca_id(str) : irca id
            cmd(str) : cmd 
        
        Returns:

        """
        return self.make_cmd(messiadir+"m", server, self.quote(self.make_cmd("mf2_com", gesica_addr, irca_id, cmd)))
        #return " ".join([messiadir+"m" ,server, self.quatation(" ".join(["mf2_com", gesica_addr, irca_id, cmd]))])

    def pon(self, messiadir, server, gesica_addr, irca_id, on_off):
        #subprocess.run(self.mf2_com(messiadir, server, gesica_addr, irca_id, " ".join(["pon", str(on_off)])), shell = True)
        subprocess.run(self.mf2_com(messiadir, server, gesica_addr, irca_id, self.make_cmd("pon", on_off)), shell=True)

class Threading(threading.Thread):
    def __init__(self):
        super().__init__()

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s: %(message)s')
                
        self.evt_interrupt = threading.Event()
        self.evt_init = threading.Event()
        self.evt_str = threading.Event()
        self.evt_mid = threading.Event()
        self.evt_end = threading.Event()

        self._done = {"INIT": False, "STR": False, "MID": False, "END": False}
        self._evt = {"INIT": self.evt_init,
                     "STR": self.evt_str,
                     "MID": self.evt_mid,
                     "END": self.evt_end}

        self.timings = ("INIT", "STR", "MID", "END")

        self._stop_loop  = False

    def run(self):
        while 1:
            #print(self._evt["INIT"].is_set())
            if not self._done["INIT"] and self._evt["INIT"].is_set():
                logging.info("INIT is set")
                self.process_init()
            if not self._done["STR"] and self._evt["STR"].is_set():
                logging.info("STR is set")
                self.process_str()
            if not self._done["MID"] and self._evt["MID"].is_set():
                logging.info("MID is set")
                self.process_mid()
            if not self._done["END"] and self._evt["END"].is_set():
                logging.info("END is set")
                self.process_end()
                break

        return

    def process_init(self):
        self._update_table("INIT")
        return
        
    def process_init_async(self):
        self.evt_init.set()
        return

    def process_str(self):
        #self.evt_str.wait(5)
        self._update_table("STR")
        return

    def process_str_async(self):
        self.evt_str.set()
        return

    def process_mid(self):
        self.evt_mid.wait(1)
        self._update_table("MID")
        return

    def process_mid_async(self):
        self.evt_mid.set()
        return
        
    def process_end(self):
        self.evt_mid.wait(1)
        self._update_table("END")
        return

    def process_end_async(self):
        self.evt_end.set()
        return

    def _update_table(self, timing):
        if self._done[timing]:
            return

        logging.info("Updating '{}'.".format(timing.upper()))

        self._done[timing] = True

        #各処理にかかる時間を仮定
        if timing=="STR":
            time.sleep(10)
        else:
            time.sleep(1)

        logging.info("Updated '{}'.".format(timing.upper()))

        return

    def tardys_daq(self):
        logging.info("Data acquisition in progress")
        p = subprocess.Popen("sleep 5", shell=True)
        return p

    def main(self):
        #この時点では何もしない
        self.daemon=True
        self.start()

        #timingがINITの項目についてテーブルが変更
        self.process_init()
        #self._done["INIT"]がTrueになる

        #self.evt_strをsetすることで、if not self._done["STR"] and self._evt["STR"].is_set()の文が実行される
        self.process_str_async()
        #self._done["STR"]がTrueになる

        time.sleep(1)

        self.process_mid_async()

        time.sleep(1)

        self.process_end()


if __name__=="__main__":
    h = Threading()

    #この時点では何もしない
    h.daemon=True
    h.start()

    #timingがINITの項目についてテーブルが変更
    h.process_init()

    h.process_str_async()

    p = h.tardys_daq()

    while p.poll() is None:
        time.sleep(1)
        logging.info("子プロセス実行中")

    h.process_mid_async()

    h.process_end()