from sysinfobase import *


from dmidecode import DMIDecode
import psutil


class SysInfo(SysInfoBase):
    def __init__(self):
        super().__init__()
    
    
    def cpu_temp(self):
            temp = psutil.sensors_temperatures()
            dmi = DMIDecode()
            cpu_temp = temp["k10temp"][0]
            
            return cpu_temp.current


    def is_startup(self):
        return False
    
    
    def set_startup(self, value):
        pass

    
    def game_fps(self):
        return 0
    
    
    def game_name(self):
        return ""


