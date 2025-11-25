import GPUtil
import psutil
import sys, os
from datetime import datetime
import re
import signal
import subprocess
import platform
import copy
import argparse
from tabulate import tabulate
import cpuinfo

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog, QMenu
from PySide6.QtCore import QTimer, Qt, Signal, QSettings
from PySide6.QtGui import QAction, QFont

from dial_meter import dial_meter
from sysinfo import *


def py_uic(name):
    src_dir = os.path.dirname(os.path.realpath(__file__))
    ui_file = f"{src_dir}/{name}.ui"
    py_file = f"{src_dir}/{name}.py"

    compile = False

    if not os.path.exists(py_file):
        compile = True

    if os.path.exists(py_file):
        ui_time = datetime.fromtimestamp(os.path.getmtime(ui_file))
        py_time = datetime.fromtimestamp(os.path.getmtime(py_file))
        if ui_time > py_time:
            compile = True
    
    if compile:
        # os.system(f"pyside6-uic {ui_file} -o {py_file}")
        result = subprocess.run(["pyside6-uic", f"{ui_file}", "-o", f"{py_file}"],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            print(f"ERROR:\n{result.stderr}")


py_uic("statsgui")
py_uic("settings")


import statsgui
import settings


def strtobool(s):
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    
    if s.lower() == "true":
        return True
    else:
        return False


class Option:
    def __init__(self, name, default):
        self.name = name
        self.value = default
        self.data = None
        self.changed = False


class Settings(QDialog):

    updated = Signal()

    def __init__(self):
        super().__init__()
        self.ui = settings.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.button_cancel.clicked.connect(self.button_cancel)
        self.ui.button_save.clicked.connect(self.button_save)

        self.options = {
            "display": Option("display", None),
            "fullscreen": Option("fullscreen", True),
            "scaling": Option("scaling", 100),
            "startup": Option("startup", False)
        }
        self.config = QSettings("yuckify", "pystats")

        self.display = None
        self.ui.display_list.activated.connect(self.opt_display)
        self.ui.fullscreen.stateChanged.connect(self.opt_fullscreen)
        self.ui.settings_select.itemClicked.connect(self.select_page)
        # self.ui.scaling.textChanged.connect(self.opt_scaling)
        self.ui.scaling.editingFinished.connect(self.opt_scaling)
        self.ui.startup.stateChanged.connect(self.opt_startup)


    def init(self, changed = False):
        # display list
        self.ui.display_list.clear()
        screens = QApplication.screens()
        i = 0
        config_display = self.config.value("display")
        for s in screens:
            key = f"{s.manufacturer()} {s.model()} {s.serialNumber()}"
            name = f"{s.manufacturer()} {s.model()}"
            self.ui.display_list.addItem(name, s)
            if key == config_display:
                self.ui.display_list.setCurrentIndex(i)
                self.options["display"].data = s
                self.options["display"].changed = changed
                self.options["display"].value = f"{s.manufacturer()} {s.model()} {s.serialNumber()}"
                self.options["display"].name = f"{s.manufacturer()} {s.model()}"
            i += 1

        # fullscreen
        self.options["fullscreen"].changed = changed
        self.options["fullscreen"].value = strtobool(self.config.value("fullscreen"))
        self.ui.fullscreen.setChecked(self.options["fullscreen"].value)

        # scaling
        self.options["scaling"].changed = changed
        try:
            self.options["scaling"].value = float(self.config.value("scaling"))
        except:
            self.options["scaling"].value = 100
        self.ui.scaling.setText(str(self.options["scaling"].value))

        # startup
        self.options["startup"].changed = changed
        self.options["startup"].value = strtobool(self.config.value("startup"))
        self.ui.startup.setChecked(self.options["startup"].value)


    def select_page(self, column):
        page = column.text(0)
        widget = getattr(self.ui, page)
        self.ui.settings_pages.setCurrentWidget(widget)


    def showEvent(self, event):
        self.init(False)
        super(QDialog, self).showEvent(event)

    
    def button_cancel(self):
        self.hide()

    
    def button_save(self):
        self.updated.emit()
        for k in self.options:
            self.config.setValue(k, self.options[k].value)
        self.hide()


    def opt_display(self, obj):
        s = self.ui.display_list.currentData()
        self.options["display"].data = s
        self.options["display"].changed = True
        self.options["display"].value = f"{s.manufacturer()} {s.model()} {s.serialNumber()}"
        self.options["display"].name = f"{s.manufacturer()} {s.model()}"


    def opt_fullscreen(self):
        opt = self.options["fullscreen"]
        opt.changed = True
        opt.value = self.ui.fullscreen.isChecked()
        opt.name = "fullscreen"


    def opt_scaling(self):
        opt = self.options["scaling"]
        opt.changed = True
        try:
            opt.value = float(self.ui.scaling.text())
        except:
            opt.value = 100
        opt.name = "scaling"
    

    def opt_startup(self):
        opt = self.options["startup"]
        opt.changed = True
        opt.value = self.ui.startup.isChecked()
        opt.name = "fullscreen"


class GuiObject:
    def __init__(self, ui):
        self.ui = ui
        self.keys = []
        if self.is_label():
            self.format = ui.text()
            self.keys = re.findall("\$\(([a-zA-Z0-9_]+)\)", self.format)
        if self.is_formatted():
            ui.setText("")
        self.font = ui.font()

    
    def update(self, params, settings):
        if self.is_formatted():
            display = self.format
            for k in self.keys:
                fmt = f"$({k})"
                display = display.replace(fmt, str(params[k]))
            self.ui.setText(display)
        if hasattr(self.ui, "set_values"):
            self.ui.set_values(params)

        f = QFont(self.font)
        f.setPointSize(f.pointSize()*(settings.options["scaling"].value/100.0))
        self.ui.setFont(f)


    def is_formatted(self):
        return len(self.keys)
    

    def is_label(self):
        return isinstance(self.ui, QLabel)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = statsgui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.sysinfo = SysInfo()

        # 
        self.label_objs = []

        # init the objects list
        for obj_name in dir(self.ui):
            obj = getattr(self.ui, obj_name)
            if not isinstance(obj, QLabel) and not isinstance(obj, dial_meter):
                continue
            
            gui_obj = GuiObject(obj)
            self.label_objs.append(gui_obj)
        
        self.settings = Settings()
        self.settings.updated.connect(self.settings_updated)
        self.settings.init(True)
        self.settings_updated()
        self.cpu_info = cpuinfo.get_cpu_info()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_timeout)
        self.update_timer.start(500)


    def set_fullscreen(self, fs):
        if fs:
            self.showFullScreen()
        else:
            self.showNormal()


    def set_startup(self, s):
        if s == self.sysinfo.is_startup():
            return
        
        self.sysinfo.set_startup(s)


    def settings_updated(self):
        for k in self.settings.options:
            opt = self.settings.options[k]
            if not opt.changed:
                continue
                
            if k == "display":
                self.set_display(opt.data)
            elif k == "fullscreen":
                self.set_fullscreen(opt.value)
            elif k == "startup":
                self.set_startup(opt.value)

            opt.changed = False


    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.show_conext_menu(event.globalPosition().toPoint())

        return super().mousePressEvent(event)


    def show_conext_menu(self, pos):
        menu = QMenu(self)

        # setup the right-click context
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.action_settings)
        menu.addAction(settings_action)

        menu.exec(pos)


    def action_settings(self):
        self.settings.show()


    def set_display(self, disp):
        screen_geo = disp.geometry()
        x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
        y = screen_geo.y() + (screen_geo.height() - self.height()) // 2
        self.move(x, y)
        self.setGeometry(screen_geo)
        fs = self.settings.options["fullscreen"]
        if fs.value:
            self.set_fullscreen(fs.value)
            fs.changed = False


    def update_timeout(self):
        self.get_params()
        self.update_gui()


    def update_gui(self):
        for obj in self.label_objs:
            obj.update(self.params, self.settings)


    def get_params(self):
        # ram
        ram_total = round(psutil.virtual_memory().total/1e9, 1)
        ram_used = round(psutil.virtual_memory().used/1e9, 1)

        # disk
        disk_total = round(psutil.disk_usage("/").total/1e9, 1)
        disk_used = round(psutil.disk_usage("/").used/1e9, 1)

        # gpus
        gpus = GPUtil.getGPUs()
        gpu = gpus[0]

        cpu_name = self.cpu_info["brand_raw"]
        cpu_name = cpu_name.replace(" Processor", "")
        match = re.findall(" ([0-9]+)-Core", cpu_name)
        if match:
            cpu_name = cpu_name.replace(f" {match[0]}-Core", "")


        self.params = {
            # random stats
            "time": datetime.now().strftime("%I:%M:%S %p"),
            "date": datetime.now().strftime("%m/%d/%Y"),

            # ram stats
            "ram_frequency": 0,
            "ram_total": ram_total,
            "ram_used": ram_used,
            "ram_used_percent": round(100*ram_used/ram_total, 1),

            # cpu stats
            "cpu_name": cpu_name,
            "cpu_temperature": round(self.sysinfo.cpu_temp(), 1),
            "cpu_used_percent": round(psutil.cpu_percent(), 1),
            "cpu_frequency": int(psutil.cpu_freq().current),
            "cpu_frequency_max": int(psutil.cpu_freq().max),

            # disk
            "disk_total": disk_total,
            "disk_used": disk_used,
            "disk_used_percent": round(100*disk_used/disk_total, 1),

            # gpu
            "gpu_name": gpu.name,
            "gpu_used": round(gpu.load*100.0, 1),
            "gpu_driver": gpu.driver,
            "gpu_mem_total": round(gpu.memoryTotal/1e3, 1),
            "gpu_mem_used": round(gpu.memoryUsed/1e3, 1),
            "gpu_mem_used_percent": round(100*gpu.memoryUsed/gpu.memoryTotal, 1),
            "gpu_temperature": gpu.temperature,

            # game
            "game_fps": int(self.sysinfo.game_fps()),
            "game_name": self.sysinfo.game_name(),
        }

        return self.params


def sig_handler(signum, frame):
    print("Ctrl-c exit")
    exit(0)


def main():
    parser = argparse.ArgumentParser(description="gui to display system stats")
    parser.add_argument("-l", "--list", default=False, action="store_true", help="print all available statistics")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, sig_handler)

    app = QApplication(sys.argv)
    window = MainWindow()

    if args.list:
        params = window.get_params()
        data = []
        for n in params:
            data.append([n, params[n]])
        print(tabulate(data, headers=["Variable", "Value"]))

        window.sysinfo.set_startup(True)

        return 0

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

