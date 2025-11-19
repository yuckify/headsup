import math
from datetime import datetime
import re

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog, QMenu
from PySide6.QtCore import QTimer, Qt, Signal, QSettings, QPoint
from PySide6.QtGui import QAction, QFont, QPainter, QPen, QFontMetrics

class h_bar_meter(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.min = 0
        self.max = 100
        self.value = 30

    def set_values(self, params):
        self.label.setFont(self.font())
        self.fm = QFontMetrics(self.font())
        self.keys = re.findall("\$\(([a-zA-Z0-9_]+)\)", self.property("format"))
        self.value = float(params[self.keys[0]])
        self.title.setText(self.property("title"))
        self.title.setFont(self.font())
        self.min = float(self.property("min"))
        self.max = float(self.property("max"))

        display = self.property("format")
        for k in self.keys:
            fmt = f"$({k})"
            display = display.replace(fmt, f"{int(params[k])}")
        self.label.setText(display)
        self.update()


    def paintEvent(self, event):
        pass

