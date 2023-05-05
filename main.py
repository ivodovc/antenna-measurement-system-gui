from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random
import os
from data_processing import load_data, calibrate, calibrate_linear, load_data_global, values, cal_values
import blue
import threading

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
        #self.plot_all_files()
        self.graphwidgetgeometry = self.graphwidget.frameGeometry()
        self.data_x, self.data_y = [],[]
        self.plot([], [], "first")
        #self.i=0
        #self.plot_0_and_1()
        #self.plot_calibrate()
        #for i in range(25,2400, 100):
        #    self.plot_atenuator(i)

    def saveButtonClicked(self):
        self.plotLine.setData([2,3], [4,5])
        print("Save Clicked")

    def start_data_reception(self):
        self.index = 0
        self.raw_buffer = ""
        self.buff_index = 0
        bt_thread = threading.Thread(target=blue.data_reception_cycle, args=(self.updateData, ), daemon=True)
        bt_thread.start()

    
    def updateData(self, data):
        fx, fy = self.split_raw_data(data)
        self.data_x += fx
        self.data_y += fy
        self.plotLine.setData(self.data_x, self.data_y)
        #self.plot(self.data_x, self.data_y, "test")


    def split_raw_data(self, data):
        self.raw_buffer += data
        found_datapoints_x = []
        found_datapoints_y = []
        while self.buff_index < len(self.raw_buffer):
            c = self.raw_buffer[self.buff_index]
            if (c=="}"):
                opening = self.raw_buffer.rfind("{", 0, self.buff_index)
                x,y = self.raw_buffer[opening+1: self.buff_index].split(",")
                x_int, y_int = int(x), int(y)
                found_datapoints_x.append(x_int)
                found_datapoints_y.append(y_int)
                self.raw_buffer = self.raw_buffer[self.buff_index+1:]
                self.buff_index=0
            else:
                self.buff_index+=1
        return found_datapoints_x, found_datapoints_y

    def measButtonClicked(self):
        self.graphwidget.clear()
        self.plotLine.clear()
        self.plot([],[],"first")
        self.data_x = []
        self.data_y = []
        self.start_data_reception()
        # get params
        from_text = self.fromEdit.text()
        to_text = self.toEdit.text()
        step_text = self.stepEdit.text()
        from_int, to_int, step_int = 0,0,0
        # check if params are digits
        try:
            from_int = int(from_text)
            to_int = int(to_text)
            step_int = int(step_text)
        except Exception as e:
            print(e)
            self.msgLabel.setText("Input freq Error")
            return
        # check if numbers are valid
        if (from_int >= to_int):
            self.msgLabel.setText("From frequency should be smaller than To frequency")
            return
        if (from_int > 2700 or from_int < 27):
            self.msgLabel.setText("From out of range")
            return
        if (to_int > 2700 or to_int < 27):
            self.msgLabel.setText("To out of range")
            return
        if (step_int >= to_int-from_int):
            self.msgLabel.setText("Step is too big")
            return
        if (step_int < 1):
            self.msgLabel.setText("Step is too small")
            return
        command = "AMS_SWEEP(" + str(from_int) + ", " + str(to_int) + ", " + str(step_int) + ")"
        self.msgLabel.setText("Command '" + command + "' sent.")
        if (blue.isConnected()):
            blue.send_message(command)
        else:
            self.msgLabel.setText("Not connected to AMS ")

    def newWindowButtonClicked(self):
        self.graphwindow = GraphWindow(self.graphwidget)
        self.graphwidget.setParent(self.graphwindow)
        self.graphwidget.show()
        self.graphwindow.show()

    def graphWindowClosed(self):
        self.graphwidget.setParent(self.Tab1)
        self.graphwidget.show()
        self.graphwidget.setGeometry(self.graphwidgetgeometry)

    def plot(self, x, y, name):
        pen = pg.mkPen(color=(random.random()*255, random.random()*255, random.random()*255), width=3)
        self.plotLine = self.graphwidget.plot(x, y, pen=pen, name=name)



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
        #print(freq)
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







random.seed()
app = QtWidgets.QApplication([])

#load_data_global()
#calibrate_linear()
#print(cal_values)
window = MainWindow()
window.show()
blue = blue.Blue(window)

bg1 = pg.BarGraphItem(x=0.5, height=0.5, width=0.2, brush='r')
w = window.barGraph
w.setBackground('w')
w.setXRange(0,1)
w.setYRange(0,1)
w.addItem(bg1)
w.getPlotItem().hideAxis("bottom")

x = threading.Thread(target=blue.connect, args=(), daemon=True)
x.start()
app.exec()