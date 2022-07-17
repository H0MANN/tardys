import subprocess
from turtle import mode
from taoics.tardys import config,config_mysql
from terminal_interface import TerminalInterface
import argparse


class MessiaClient:
    def __init__(self):
        self.interface = TerminalInterface()
        self.name = "det"
        self.messia = config.get("hostname", "messia")
        self.gesica = config.get("hostname", "gesica")
        self.messiadir = config.get(self.name, "messiadir")
        self.irca_id = config.get(self.name, "irca_id")
        self.mysql = config_mysql(self.name)

    ##############################################################
    ## irca
    ##############################################################

    def powerup_irca(self):
        """
        This method turn IRCA3 ON.
        """
        self.interface.pon(self.messiadir, self.messia, self.gesica, self.irca_id, 1)

    def powerdown_irca(self):
        """
        This method turn IRCA3 OFF.
        """
        self.interface.pon(self.messiadir, self.messia, self.gesica, self.irca_id, 0)

    def initialize_irca(self):
        self.interface.init_irca(self.messia, self.gesica, self.irca_id)

    ###############################################################
    ## det
    ###############################################################

    def coding_interpret(self, reset_sub, ref_sub):
        """
        Get the second from last character of the coding
        """
        if ref_sub:
            return 1
        else:
            if reset_sub:
                return 0
            else:
                return 2

    def setting_interpret(self, mode, n_ch, n_sample, n_sur, n_osample, n_reset, exp_time, reset_sub, ref_sub, complement):
        """
        This method converts the arguments the observer gives to the arguments Messia system actually use.
        """
        n_y = 1296
        complements = {"STRAIGHT":0, "INVERT":1, "SECONDARY":2}

        if mode.upper()=="FOWLER":
            clock_pattern = "hpk2015_red"
            n_sur = 1
        elif mode.upper()=="SUR":
            clock_pattern = "hpk2015_red_sur"
        else:
            raise ValueError("INVARID SAMPLING MODE")

        n_x = int(n_y/n_ch)

        coding = '{}00{}{}'.format(hex(n_osample-1), self.coding_interpret(reset_sub, ref_sub), complements[complement.upper()])

        return (clock_pattern, n_x, n_y, n_ch, coding, n_sample, n_sur, n_osample, n_reset, exp_time, mode.upper(), reset_sub, ref_sub)

    def set_det(self, mode, n_ch, n_sample, n_sur, n_osample, n_reset, exp_time , reset_sub, ref_sub, complement):
        """
        This method update the detector setting.
        """
        vals = self.setting_interpret(mode, n_ch, n_sample, n_sur, n_osample, n_reset, exp_time, reset_sub, ref_sub, complement)

        keys=["SPV", "N_X", "N_Y", "N_OUT","CODING", "NSAMPLE", "NSURAMP", "NOSAMPLE", "NRESET", "EXP_TIME", "SMPLMODE", "RST_SUB", "REF_SUB"]

        self.mysql.update_status_values(dict(zip(keys, vals)))

#ここになくてもいいかも
class DS9:
    def __init__(self):
        self.interface = TerminalInterface()
    def start_ds9(self):
        self.interface.start_process("ds9")

    #def show_frames(self, frame_name):
    #    self.interface()


if __name__ == "__main__":
    messia_client = MessiaClient()

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", help="FOWLER or SUR(Sample Up the Ramp)")
    parser.add_argument("--n_ch", type = int, default='8', help="ONLY 8 IS VALID")
    parser.add_argument("--n_sample", type = int, default="1")
    parser.add_argument("--n_sur", type = int, default="1")
    parser.add_argument("--n_osample", type= int, default=1)
    parser.add_argument("--n_reset", type = int, default = 1, help="number of reset")
    parser.add_argument("exp_time", help='raw data directory')
    parser.add_argument("--reset_sub", type = str , default="False")
    parser.add_argument("--ref_sub", type = str, default="False")
    parser.add_argument("--complement_mode", default = "SECONDARY", help="LINEAR or INVERT or SECONDARY")


    args = parser.parse_args()

    #print(args.reset_sub)
    messia_client.set_det(args.mode,args.n_ch, args.n_sample, args.n_sur, args.n_osample, args.n_reset, args.exp_time, args.reset_sub, args.ref_sub, args.complement_mode)




