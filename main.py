import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random
import os

class GraphWindow(QtWidgets.QMainWindow):
    def __init__(self, graph):
        super().__init__()
        self.setWindowTitle("Graph Window")
        self.setCentralWidget(graph)

    def closeEvent(self, event):
        window.graphWindowClosed()

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)
        self.init_plot()
        self.setWindowIcon(QtGui.QIcon('vut_logo.png'))
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.measButton.clicked.connect(self.measButtonClicked)
        self.newWindowButton.clicked.connect(self.newWindowButtonClicked)
        self.plot_all_files()
        self.graphwidgetgeometry = self.graphwidget.frameGeometry()
        #self.plot_0_and_1()
        #self.plot_calibrate()
        #for i in range(25,2400, 5):
            #self.plot_atenuator(i)

    def saveButtonClicked(self):
        print("Save Clicked")

    def measButtonClicked(self):
        self.graphwidget.clear()
        self.plot_all_files()

    def newWindowButtonClicked(self):
        self.graphwindow = GraphWindow(self.graphwidget)
        self.graphwidget.setParent(self.graphwindow  )
        self.graphwidget.show()
        self.graphwindow.show()

    def graphWindowClosed(self):
        self.graphwidget.setParent(self.centralwidget)
        self.graphwidget.show()
        self.graphwidget.setGeometry(self.graphwidgetgeometry)

    def plot(self, x, y, name):
        pen = pg.mkPen(color=(random.random()*255, random.random()*255, random.random()*255), width=3)
        self.graphwidget.plot(x, y, pen=pen, name=name)

    def plot_0_and_1(self):
        x, y = load_data("vsetko/" + "data_0dB_priamo.txt")
        self.plot(x,y, "data_0dB_priamo.txt")
        x, y = load_data("vsetko/" + "data_50ohm.txt")
        self.plot(x,y, "data_50ohm.txt")

    def plot_atenuator(self, freq):
        db = []
        y = []
        for key in values:
            if "atenuator" not in key:
                continue
            db_val = -int(key[5])
            if "12" in key:
                db_val = -12
            if "10" in key:
                db_val = -10
            ADC_val_index = values[key][0].index(freq)
            ADC_val = values[key][1][ADC_val_index]
            db.append(db_val)
            y.append(ADC_val)
        zipped = sorted(zip(db, y), reverse=True)
        lists = [list(t) for t in zip(*zipped)]
        #print(lists[0])
        print(freq)
        self.plot(lists[1], lists[0], str(freq)+"MHz")

    def plot_all_files(self):
        for file in os.listdir("vsetko"):
             if file.endswith(".txt"):
                x, y = load_data("vsetko/" + str(file))
                self.plot(x,y, file)

    def plot_calibrate(self):
        for key in cal_values:
            x = cal_values[key][0]
            y = cal_values[key][1]
            self.plot(x, y, key)

    def init_plot(self):
        self.graphwidget.setBackground('w')
        self.graphwidget.setTitle("ADC = f(freq)")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphwidget.setLabel('left', 'ADC', **styles)
        self.graphwidget.setLabel('bottom', 'freq [MHz]', **styles)
        self.graphwidget.addLegend()

# Load csv raw data reported by stm32
def load_data(filename):
    x_vals = []
    y_vals = []
    with open(filename, "r") as file:
        for line in file:
            graph_points = line.rstrip().split(";")
            for point in graph_points:
                if (len(point)<1):
                    continue
                x, y, voltage = point.split(",")
                try:
                    x_vals.append(int(x))
                    y_vals.append(int(y))
                except ValueError as e:
                    #print("error:", e)
                    pass
    return x_vals, y_vals

# find index of requested frequency and return y value for that frequency
def get_value_at_freq(filename, freq):
    all_values = values[filename]
    index = all_values[0].index(freq)
    return  all_values[1][index]

def calibrate():
    #25 az 2400 MHz
    for freq in range(25,2400):
        priamo_0db = get_value_at_freq("data_0dB_priamo.txt", freq)
        priamo_50Ohm = get_value_at_freq("data_50ohm.txt", freq)

        at_db = [0,2,4,6]
        at_filenames = ["data_" + str(db) + "dB_atenuator.txt" for db in at_db]
        at_hodnoty = [get_value_at_freq(filename, freq) for filename in at_filenames]
        cal_hodnoty = [None] * len(at_hodnoty)
        # rozdiel 0db priamo a 0db at
        rozdiel = at_hodnoty[0] - priamo_0db
        for i in range(len(at_db)):
            db = at_db[i]
            hodnota = at_hodnoty[i]
            cal_hodnota = hodnota-rozdiel
            cal_hodnoty[i] = cal_hodnota
            cal_values[str(db) + "dB_cal"][0].append(freq)
            cal_values[str(db) + "dB_cal"][1].append(cal_hodnota)

def calibrate_linear():
    #25 az 2400 MHz
    for freq in range(25,2000):
        priamo_0db = get_value_at_freq("data_0dB_priamo.txt", freq)
        priamo_50Ohm = get_value_at_freq("data_50ohm.txt", freq)
        at_12_db = get_value_at_freq("data_12dB_atenuator.txt", freq)
        at_0_db = get_value_at_freq("data_0dB_atenuator.txt", freq)

        at_db = [0,2,4,6,8,10,12]
        at_filenames = ["data_" + str(db) + "dB_atenuator.txt" for db in at_db]
        at_hodnoty = [get_value_at_freq(filename, freq) for filename in at_filenames]
        cal_hodnoty = [None] * len(at_hodnoty)
        # rozdiel 0db priamo a 0db at
        rozdiel = at_hodnoty[0] - priamo_0db
        for i in range(len(at_db)):
            db = at_db[i]
            hodnota = at_hodnoty[i]
            #print(freq)
            #print(at_12_db, at_0_db, hodnota)
            if (at_12_db - at_0_db)>0:
                norm_at = (hodnota - at_0_db) / (at_12_db - at_0_db)
            else:
                 norm_at = (hodnota - at_0_db) / 1
            cal_hodnota = priamo_0db + ((priamo_50Ohm - priamo_0db) * norm_at)
            cal_hodnoty[i] = cal_hodnota
            cal_values[str(db) + "dB_cal"][0].append(freq)
            cal_values[str(db) + "dB_cal"][1].append(cal_hodnota)

cal_values = {}
cal_values["0dB_cal"] = [list(), list()]
cal_values["2dB_cal"] = [list(), list()]
cal_values["4dB_cal"] = [list(), list()]
cal_values["6dB_cal"] = [list(), list()]
cal_values["8dB_cal"] = [list(), list()]
cal_values["10dB_cal"] = [list(), list()]
cal_values["12dB_cal"] = [list(), list()]
values = {}
def load_data_global():
    for file in os.listdir("vsetko"):
             if file.endswith(".txt"):
                x, y = load_data("vsetko/" + str(file))
                name = str(file)
                values[str(file)] = [x,y]


random.seed()
app = QtWidgets.QApplication([])
load_data_global()
calibrate_linear()
#print(cal_values)
window = MainWindow()
window.show()
app.exec()