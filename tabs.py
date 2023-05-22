from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random
import threading

from data_processing import load_data_csv, calibrate, calibrate_linear, load_data_global, values, cal_values

# Extra separate window for graph
class GraphWindow(QtWidgets.QMainWindow):
    def __init__(self, graphhandler):
        super().__init__()
        self.setWindowTitle("Graph Window")
        self.setCentralWidget(graphhandler.graphwidget)
        self.gh = graphhandler

    def closeEvent(self, event):
        self.gh.graphWindowClosed()

# Class to handle graphing data and graphing actions
class GraphHandler:
    
    def __init__(self, mainwindow, graphwidget):
        self.mainwindow = mainwindow
        self.graphwidget = graphwidget
        self.init_plot()
        self.graphwidgetgeometry = self.graphwidget.frameGeometry()
        self.plotLines = []
        self.data_x, self.data_y = [],[]
        self.clear()

    def plot(self, x, y, name):
        pen = pg.mkPen(color=(random.random()*255, random.random()*255, random.random()*255), width=3)
        plotLine = self.graphwidget.plot(x, y, pen=pen, name=name)
        self.plotLines.append(plotLine)

    def clear(self):
        self.graphwidget.clear()
        self.plotLines = []
        self.plot(cal_short[0], cal_short[1], "short")
        self.plot(cal_match[0], cal_match[1], "match")

    def init_plot(self):
        self.graphwidget.setBackground('w')
        self.graphwidget.setTitle("ADC = f(freq)")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphwidget.setLabel('left', 'ADC', **styles)
        self.graphwidget.setLabel('bottom', 'freq [MHz]', **styles)
        self.graphwidget.addLegend()

    def createNewPlotLine(self):
        self.plot([],[], str(len(self.plotLines)))
        self.raw_buffer = ""
        self.buff_index = 0
        self.data_x = []
        self.data_y = []

    def graphWindowClosed(self):
        print("Closed")
        self.graphwidget.setParent(self.mainwindow.Tab1)
        self.graphwidget.show()
        self.graphwidget.setGeometry(self.graphwidgetgeometry)

    def openInNewWindow(self):
        self.graphwindow = GraphWindow(self)
        self.graphwidget.setParent(self.graphwindow)
        self.graphwidget.show()
        self.graphwindow.show()

    def newDataArrived(self, data):
        fx, fy = self.split_raw_data(data)
        self.data_x += fx
        self.data_y += fy
        self.plotLines[-1].setData(self.data_x, self.data_y)

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

    def updateLastPlotLineWithNewData(self, data):
        self.data_x += data[0]
        self.data_y += data[1]
        self.plotLines[-1].setData(self.data_x, self.data_y)

class SweepTab:

    def __init__(self, mainwindow):
        self.mw = mainwindow
        self.blue = mainwindow.blue

        self.graph = GraphHandler(self.mw, self.mw.sweepGraphWidget)
        
        self.mw.saveButton.clicked.connect(self.saveButtonClicked)
        self.mw.measButton.clicked.connect(self.measButtonClicked)
        self.mw.newWindowButton.clicked.connect(self.newWindowButtonClicked)
        self.mw.clearButton.clicked.connect(self.clearGraphClicked)

    def saveButtonClicked(self):
        print("Save Clicked")

    def clearGraphClicked(self):
        self.graph.clear()

    def measButtonClicked(self):
        # get params
        parsed_args = self.getSweepInputs()
        if parsed_args is not None:
            from_int, to_int, step_int, pwr_int = parsed_args
        else:
            #bad parsing
            return
        command = "AMS_SWEEP(" + str(from_int) + ", " + str(to_int) + ", " + str(step_int) + "," + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.blue.send_message(command)
            self.start_data_reception()
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

    def newWindowButtonClicked(self):
        self.graph.openInNewWindow()

    def getSweepInputs(self):
        from_text = self.mw.fromEdit.text()
        to_text = self.mw.toEdit.text()
        step_text = self.mw.stepEdit.text()
        pwr_int = int(self.mw.comboBox.currentText()[0]) # first character is power level

        from_int, to_int, step_int = 0,0,0
        # check if params are digits
        try:
            from_int = int(from_text)
            to_int = int(to_text)
            step_int = int(step_text)
        except Exception as e:
            print(e)
            self.mw.msgLabel.setText("Input freq Error")
            return
        # check if numbers are valid
        if (from_int >= to_int):
            self.mw.msgLabel.setText("From frequency should be smaller than To frequency")
            return
        if (from_int > 6000 or from_int < 25):
            self.mw.msgLabel.setText("From out of range")
            return
        if (to_int > 6000 or to_int < 25):
            self.mw.msgLabel.setText("To out of range")
            return
        if (step_int >= to_int-from_int):
            self.mw.msgLabel.setText("Step is too big")
            return
        if (step_int < 1):
            self.mw.msgLabel.setText("Step is too small")
            return
        return from_int, to_int, step_int, pwr_int

    def start_data_reception(self):
        #self.index = 0
        self.mw.setDataConnector(self.graph.newDataArrived)
        self.graph.createNewPlotLine()
        bt_thread = threading.Thread(target=self.blue.data_reception_cycle, args=(), daemon=True)
        bt_thread.start()

class CalibrationTab:
    
    def __init__(self, mainwindow):
        self.mw = mainwindow
        self.blue = mainwindow.blue

        self.graph = GraphHandler(self.mw, self.mw.calibrateGraphWidget)
        
        self.mw.calibrateShortButton.clicked.connect(self.calibrate_short_button)
        self.mw.calibrateMatchButton.clicked.connect(self.calibrate_match_button)
        self.mw.testMeasureButton.clicked.connect(self.test_measure_button)
        #self.mw.clearButton.clicked.connect(self.clearGraphClicked)

        #self.blue.signals.dataUpdated.connect(self.graph.updateData)

    def calibrate_short_button(self):
        print("calibrateshort")

    def calibrate_match_button(self):
        print("calibratmatch")

    def test_measure_button(self):
        print("test_measure")
    

cal_short = load_data_csv("calibration_short.csv")
cal_match = load_data_csv("calibration_match.csv")