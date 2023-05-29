"""
    Antenna Measurement system GUI control program
    Copyright (C) 2023

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

import os
import sys

from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6 import uic
import random

import blue

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

        self.dataConnector = None
        self.finishedConnector = None

        self.sweepTab = SweepTab(self)
        self.calibrationTab = CalibrationTab(self)
        self.singleTab = SingleTab(self)
        self.advancedTab = AdvancedTab(self)

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
        if status == 'connected':
            self.con_status.setText("AMS connected")
            self.status_widget.setStyleSheet(self.greenStyleSheet)
        elif status == 'attempting':
            self.con_status.setText("Attempting...")
            self.status_widget.setStyleSheet(self.amberStyleSheet)
        elif status == 'not_connected':
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


# from https://stackoverflow.com/questions/1432924/python-change-the-scripts-working-directory-to-the-scripts-own-directory
# this has to be there othwerise tab imports wont go to correct folders
os.chdir(sys.path[0])
random.seed()
app = QtWidgets.QApplication([])

window = MainWindow()
window.show()
app.exec()
