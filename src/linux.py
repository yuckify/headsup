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


