import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)
        self.init_plot()
        x, y = load_data("data_0dB_priamo.txt")
        self.plot(x,y)
        x, y = load_data("data_50ohm.txt")
        self.plot(x,y)

    def plot(self, x, y):
        pen = pg.mkPen(color=(random.random()*255, random.random()*255, random.random()*255), width=3)
        self.graphwidget.plot(x, y, pen=pen)

    def init_plot(self):
        self.graphwidget.setBackground('w')
        self.graphwidget.setTitle("ADC = f(freq)")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphwidget.setLabel('left', 'ADC', **styles)
        self.graphwidget.setLabel('bottom', 'freq [MHz]', **styles)

# Load csv raw data reported by stm32
def load_data(filename):
    x_vals = []
    y_vals = []
    with open(filename, "r") as file:
        for line in file:
            x, y, voltage = line.split(",")
            try:
                x_vals.append(int(x))
                y_vals.append(int(y))
            except ValueError as e:
                print(e)
    return x_vals, y_vals

random.seed()
app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec()