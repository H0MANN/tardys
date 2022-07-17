import subprocess
from taoics.tardys import config
from terminal_interface import TerminalInterface

#it has similar role as idclient.py in swims

class MessiaServer:
    def __init__(self):
        self.interface = TerminalInterface()
        self.name = "messia"
        self.messiadir = config.get("det", "messiadir")
        self.messia_server = config.get("hostname", "server")

    #def is_exist(self, process):
    #    ret = subprocess.run("ps aux | grep " + process + " | grep -v grep | grep -v python | wc -l", shell=True, check=True, encoding="utf-8", stdout = subprocess.PIPE)
    #    return ret

    def is_connected(self):
        return bool(int(self.interface.is_exist(self.name).stdout))

    def connect(self):
        if self.is_connected():
            self.logger.debug("Already connected.")
            return

        try:
            subprocess.run(self.messiadir+self.name + " " + self.messia_server, shell=True)
        except Exception as err:
            raise err

    def kill_messia(self):
        self.interface.kill_process(self.name)
        #subprocess.run("kill -9 `pgrep -f " + self.name+ "`", shell=True) #pgrep : find process ID
        
if __name__ == '__main__':
    server = MessiaServer()

    print(server.is_connected())
    server.kill_messia()
