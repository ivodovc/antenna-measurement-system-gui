import os
import sys
# from https://stackoverflow.com/questions/1432924/python-change-the-scripts-working-directory-to-the-scripts-own-directory
os.chdir(sys.path[0])

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random


from data_processing import load_data_csv, save_data_csv
import blue
import threading


from tabs import SweepTab, CalibrationTab, SingleTab, AdvancedTab



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
        self.singleTab = SingleTab(self)
        self.advancedTab= AdvancedTab(self)

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

    # defines where to send data from bluetooth
    # dataConnector is a function
    def setContDataConnector(self, contDataConnector):
        self.setContDataConnector = contDataConnector

    def contDataFromBluetoothArrived(self, data):
        if (self.setContDataConnector is not None):
            self.contDataConnector(data)


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

    def sendStop(self):
        command = "AMS_STOP()"
        if (self.blue.isConnected()):
            self.blue.send_message(command)
        else:
            self.msgLabel.setText("Not connected to AMS ")



random.seed()
app = QtWidgets.QApplication([])

window = MainWindow()
window.show()
app.exec()