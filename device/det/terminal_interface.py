import subprocess
from taoics.tardys import config

class TerminalInterface:
    def __init__(self):
        pass

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
        #hidoukinisuru
        #fits header handlerwoyobu
        subprocess.run(self.make_cmd("sh", messiadir+"tardys_daq.sh", messia_addr, gesica_addr, clock_pattern, n_x, n_y, coding, n_sample, n_sur, exp_time_01, raw_data_dir, file_prefix), shell=True)

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



if __name__=="__main__":
    pass