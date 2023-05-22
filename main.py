from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random
import os
import sys
from data_processing import load_data_csv, save_data_csv
import blue
import threading


from tabs import SweepTab, CalibrationTab



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("mainwindow.ui", self)
        self.setWindowIcon(QtGui.QIcon('vut_logo.png'))

        self.threadpool = QThreadPool()
        self.init_stylesheets()
        self.blue = blue.Blue(self)
        self.blue.signals.statusChanged.connect(self.setConnectionStatus)
        self.blue.signals.dataUpdated.connect(self.dataFromBluetoothArrived)
        self.blue.signals.dataStreamFinished.connect(self.dataStreamFinished)

        self.dataConnector  = None
        self.finishedConnector = None

        self.sweepTab = SweepTab(self)
        self.calibrationTab = CalibrationTab(self)        
        self.singleFreq = SingleFreqHandler(self)

        #self.plot_all_files()
        
        #self.i=0
        #self.plot_0_and_1()
        #self.plot_calibrate()
        #for i in range(25,2400, 100):
        #    self.plot_atenuator(i)

    # defines where to send data from bluetooth
    # dataConnector is a function
    def setDataConnector(self, dataConnector):
        self.dataConnector = dataConnector

    def dataFromBluetoothArrived(self, data):
        if (self.dataConnector is not None):
            self.dataConnector(data)

    # defines what to do after datastream is finished
    def setFinishedConnector(self, finishedConnector):
        self.finishedConnector = finishedConnector

    def dataStreamFinished(self, msg):
        if (self.finishedConnector is not None):
            self.finishedConnector(msg)

    def setConnectionStatus(self, status):
        if status=='connected':
            self.con_status.setText("AMS connected")
            self.status_widget.setStyleSheet(self.greenStyleSheet)
        elif status=='attempting':
            self.con_status.setText("Attempting...")
            self.status_widget.setStyleSheet(self.amberStyleSheet)
        elif status=='not_connected':
            self.con_status.setText("Not connected")
            self.status_widget.setStyleSheet(self.redStyleSheet)

    def init_stylesheets(self):
         # stylesheets
        self.amberStyleSheet = '''QWidget#status_widget{
                background-color: rgb(255, 160, 50);
                border-radius: 5px; 
                border: 1px solid white;
                border-color: rgb(0, 0, 0);
                }
        '''
        self.redStyleSheet = '''QWidget#status_widget{
                background-color: rgb(255, 104, 101);
                border-radius: 5px; 
                border: 1px solid white;
                border-color: rgb(0, 0, 0);
                }
        '''
        self.greenStyleSheet = '''QWidget#status_widget{
                background-color: rgb(104, 255, 101);
                border-radius: 5px; 
                border: 1px solid white;
                border-color: rgb(0, 0, 0);
                }
        '''

class SingleFreqHandler():
    

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.g = mainwindow.singleFreqGraph
        self.g.setBackground('w')
        self.blue = mainwindow.blue

        self.x, self.y, self.i = [], [], 0

        self.mainwindow.startButton.clicked.connect(self.startButtonClicked)
        self.mainwindow.stopButton.clicked.connect(self.stopButtonClicked)
        self.blue.signals.singleDataUpdated.connect(self.update)
        pen = pg.mkPen(color=(random.random()*255, random.random()*255, random.random()*255), width=3)
        self.plotLine = self.g.plot([], [], pen=pen, name="Continuous Sweep")
        shortpen = pg.mkPen(color=(0,0,255)
        , width=3)
        #self.g.plot(cal_short[0], cal_short[1], pen=shortpen, name="Short")
        matchpen = pg.mkPen(color=(255,0,0), width=3)
        #self.g.plot(cal_match[0], cal_match[1], pen=matchpen, name="Match")

    def start_data_reception(self):
        self.index = 0
        self.x, self.y = [],[]
        self.i = None
        self.plotLine.clear()
        self.raw_buffer = ""
        self.buff_index = 0
        bt_thread = threading.Thread(target=self.blue.data_reception_cycle2, args=(self.blue.signals.singleDataUpdated,), daemon=True)
        bt_thread.start()

    def startButtonClicked(self):
        f = int(self.mainwindow.singlefreqEdit.text())
        step = int(self.mainwindow.singleStepEdit.text())
        command = "AMS_SINGLE(" + str(f) + ", " + str(step) + ")"
        if (self.blue.isConnected()):
            self.blue.send_message(command)
            self.start_data_reception()
        else:
            self.msgLabel.setText("Not connected to AMS ")
    
    def stopButtonClicked(self):
        command = "AMS_STOP()"
        if (self.blue.isConnected()):
            self.blue.send_message(command)
        else:
            self.msgLabel.setText("Not connected to AMS ")

    def update(self, data):
        print(self.x, self.y)
        fx,fy = self.split_raw_data(data)
        for index in range(len(fx)):
            x = fx[index]
            y = fy[index]
            if (self.i is None):
                self.x.append(x)
                self.y.append(y)
                self.i=0
            else:
                last_x = self.x[self.i]
                if x<last_x:
                    self.i = 0
                else:
                    self.i+=1
                if (self.i < len(self.x)):
                    self.x[self.i] = x
                    self.y[self.i] = y
                else:
                    self.x.append(x)
                    self.y.append(y)
        self.plotLine.setData(self.x, self.y)


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
        print("returning:", found_datapoints_x, found_datapoints_y)
        return found_datapoints_x, found_datapoints_y

# from https://stackoverflow.com/questions/1432924/python-change-the-scripts-working-directory-to-the-scripts-own-directory
os.chdir(sys.path[0])

random.seed()
app = QtWidgets.QApplication([])

#load_data_global()
#calibrate_linear()
#print(cal_values)
window = MainWindow()
window.show()

app.exec()