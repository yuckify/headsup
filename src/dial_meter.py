import math
from datetime import datetime
import re

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog, QMenu
from PySide6.QtCore import QTimer, Qt, Signal, QSettings, QPoint
from PySide6.QtGui import QAction, QFont, QPainter, QPen, QFontMetrics

class dial_meter(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.min = 0
        self.max = 100
        self.value = 30
        self.pad = 5
        self.label = QLabel(self)
        self.label.setFont(self.font())
        self.fm = QFontMetrics(self.font())
        self.keys = []
        self.title = QLabel(self)
        self.title.setFont(self.font())


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
        p = QPainter(self)

        # the rect
        r = self.rect()
        p.eraseRect(r)

        # make sure this is a circle and not an oval, width == height
        r.setWidth(min(r.width(), r.height()))
        r.setHeight(min(r.width(), r.height()))
        
        # add some padding
        r.setWidth(r.width() - self.pad*2)
        r.setHeight(r.height() - self.pad*2)
        r.setX(r.x() + self.pad)
        r.setY(r.y() + self.pad)

        # title parameters
        title_rect = self.fm.boundingRect(self.title.text())
        title_rect.adjust(-2, -2, 2, 2)
        r.setY(title_rect.bottom() + self.pad)

        # make sure this is a circle and not an oval, width == height
        r.setWidth(min(r.width(), r.height()))
        r.setHeight(min(r.width(), r.height()))
        
        # circle parameters
        c_r = r.width()/2
        c_x = r.x() + c_r
        c_y = r.y() + c_r

        # parameters for the start line, cos/sin are clockwise
        start_angle = 90+45
        s_len = 20
        s_angle = start_angle/180*3.14159
        s_point_a = QPoint(c_x + (c_r - s_len/2)*math.cos(s_angle), c_y + (c_r - s_len/2)*math.sin(s_angle))
        s_point_b = QPoint(c_x + (c_r + s_len/2)*math.cos(s_angle), c_y + (c_r + s_len/2)*math.sin(s_angle))

        # parameters for the gauge line
        gauge_angle = (self.value - self.min)/(self.max - self.min)*360
        gauge_angle = max(min(gauge_angle, 360), 0)

        p.drawArc(r, 0, 360*16)
        p.drawLine(s_point_a, s_point_b)
        
        meter_pen = QPen()
        meter_pen.setWidth(10)
        p.setPen(meter_pen)
        p.drawArc(r, (360 - start_angle)*16, -gauge_angle*16)

        # draw the value label
        label_rect = self.fm.boundingRect(self.label.text())
        label_rect.adjust(-2, -2, 2, 2)
        self.label.setGeometry(c_x - label_rect.width()/2, c_y, label_rect.width(), label_rect.height())

        # draw the title
        self.title.setGeometry(c_x - title_rect.width()/2, c_y - title_rect.height(), title_rect.width(), title_rect.height())

        p.end()





