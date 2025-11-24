from datetime import datetime
import psutil
import os, signal
import pyautogui
import subprocess

import pyRTSS


class SysInfo:
    def __init__(self):
        self.rtss = pyRTSS.RTSS()
        self.ts = datetime.now()
        self.game = None

        # minimize the console window
        w = pyautogui.getActiveWindow()
        w.minimize()


    def update(self):
        if (datetime.now() - self.ts).total_seconds() < 1:
            return
        
        self.snap = self.rtss.snapshot()
        self.ts = datetime.now()
        
        self.update_game()


    def update_game(self):
        if self.snap.dwLastForegroundAppProcessID == 0:
            self.game = None
            return
        if not psutil.pid_exists(self.snap.dwLastForegroundAppProcessID):
            self.game = None
            return

        self.game = self.snap.arrApp[self.snap.dwLastForegroundApp]


    def cpu_temp(self):
        return 0


    def game_fps(self):
        self.update()
        if self.game is None:
            return 0
        denom = self.game.dwTime1 - self.game.dwTime0
        if denom == 0:
            return 0
        fps = 1000.0 * self.game.dwFrames / denom
        return fps
    

    def game_name(self):
        self.update()
        if self.game is None:
            return ""
        return os.path.splitext(os.path.basename(self.game.szName))[0]
    

    def set_startup(self, start):
        script_path = os.path.dirname(os.path.abspath(__file__))
        os.system(f"py -3.12 {script_path}/windows_startup_installer.py {1 if start else 0}")


    def is_startup(self):
        user = os.environ.get("USERNAME")
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        start_path = f"C:/Users/{user}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/headsup.bat"
        run_cmd = f"py -3.12 {script_dir}/main.py"

        if not os.path.exists(start_path):
            print("is_startup(): path does not exist")
            return False

        file_cmd = None
        with open(start_path, "r") as f:
            file_cmd = f.read()
        if file_cmd == run_cmd:
            return True
        else:
            print("is_startup(): bad startup command")
            return False

