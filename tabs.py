from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6 import uic
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import random
import threading

from data_processing import *

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
    
    # display mode could be "default", "refcoef" or "SWR"
    def __init__(self, mainwindow, graphwidget, display_mode="default"):
        self.mainwindow = mainwindow
        self.graphwidget = graphwidget
        self.set_new_display_mode("default", 4)
        self.init_plot()
        self.graphwidgetgeometry = self.graphwidget.frameGeometry()
        self.plotLines = []
        self.data_x, self.data_y = [],[]
        self.clear()

    def set_new_display_mode(self, display_mode, pwr_level):
        allowed = ["default", "refcoef", "SWR"]
        self.pwr_level = pwr_level
        if (display_mode in allowed):
            self.display_mode = display_mode
            if (self.display_mode=="refcoef"):
                self.y_fun = get_RC
            elif (self.display_mode=="SWR"):
                self.y_fun = get_SWR
            else:
                # return plain simple ADC reading
                self.y_fun = lambda freq, ADC, pwr_level: ADC
        else:
            self.display_mode = "default"

    def plot(self, x, y, name):
        if name=="short_ref" or name=="match_ref":
            plot_color = (0,0,0)
        else:
            plot_color=(random.random()*255, random.random()*255, random.random()*255)
        pen = pg.mkPen(color=plot_color, width=3)
        plotLine = self.graphwidget.plot(x, y, pen=pen, name=name)
        self.plotLines.append(plotLine)

    def clear(self):
        self.graphwidget.clear()
        self.plotLines = []
        self.draw_reference_lines()

    def draw_reference_lines(self):
        cal_short_y_values = []
        cal_match_y_values = []
        for i in range(len(cal_short[0])):
            freq = cal_short[0][i]
            adc = cal_short[1][i]
            y = self.y_fun(freq, adc, self.pwr_level)
            cal_short_y_values.append(y)
        for i in range(len(cal_match[0])):
            freq = cal_match[0][i]
            adc = cal_match[1][i]
            y = self.y_fun(freq, adc, self.pwr_level)
            cal_match_y_values.append(y)
        self.plot(cal_short[0], cal_short_y_values, "short_ref")
        self.plot(cal_match[0], cal_match_y_values, "match_ref")
        #self.plot(cal_short[0], cal_short[1], "short_ref")
        #self.plot(cal_match[0], cal_match[1], "match_ref")

    def init_plot(self):
        self.graphwidget.setBackground('w')
        self.graphwidget.setTitle("ADC = f(freq)")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphwidget.setLabel('left', 'ADC', **styles)
        self.graphwidget.setLabel('bottom', 'freq [MHz]', **styles)
        self.graphwidget.addLegend()

    def createNewPlotLine(self, name=None):
        if name is None:
            name = str(len(self.plotLines))
        self.plot([],[], name)
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
        fy_disp = []
        for i in range(len(fx)):
            freq = fx[i]
            adc_y = fy[i]
            y_display = self.y_fun(freq, adc_y, self.pwr_level)
            fy_disp.append(y_display)
        self.data_x += fx
        self.data_y += fy_disp
        self.plotLines[-1].setData(self.data_x, self.data_y)

    def prepareForContTracing(self):
        self.index = 0
        self.x, self.y = [],[]
        self.i = None
        self.raw_buffer = ""
        self.buff_index = 0

    def newDataArrivedCont(self, data):
        fx,fy = self.split_raw_data(data)
        for index in range(len(fx)):
            x = fx[index] #frequency
            adc_y = fy[index]
            y = self.y_fun(x, adc_y, self.pwr_level)
            #y = fy[index]
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
        self.plotLines[-1].setData(self.x, self.y)

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

        self.mw.measButton.clicked.connect(self.measButtonClicked)
        self.mw.newWindowButton.clicked.connect(self.newWindowButtonClicked)
        self.mw.clearButton.clicked.connect(self.clearGraphClicked)
        self.mw.sweepStopButton.clicked.connect(self.mw.sendStop)

    def clearGraphClicked(self):
        self.graph.clear()

    def measButtonClicked(self):
        if (self.mw.singleRadioButton.isChecked()):
            self.startNormalSweep()
        elif (self.mw.contRadioButton.isChecked()):
            print("Continuous")
            self.startContSweep()
        
    def startContSweep(self):
        # get params
        parsed_args = self.getSweepInputs()
        if parsed_args is not None:
            from_int, to_int, step_int, pwr_int = parsed_args
        else:
            #bad parsing
            return
        self.graph.pwr_level = pwr_int
        command = "AMS_SWEEP_CONT(" + str(from_int) + ", " + str(to_int) + ", " + str(step_int) + "," + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.blue.send_message(command)
            self.start_cont_data_reception()
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

    def startNormalSweep(self):
        # get params
        parsed_args = self.getSweepInputs()
        if parsed_args is not None:
            from_int, to_int, step_int, pwr_int = parsed_args
        else:
            #bad parsing
            return
        self.graph.pwr_level = pwr_int
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

    def start_cont_data_reception(self):
        self.graph.prepareForContTracing()
        self.mw.setDataConnector(self.graph.newDataArrivedCont)
        self.graph.createNewPlotLine()
        bt_thread = threading.Thread(target=self.blue.data_reception_cycle, args=(), daemon=True)
        bt_thread.start()

    def start_data_reception(self):
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
        self.mw.comboBox_3.currentTextChanged.connect(self.combotextChanged)

        self.update_cal_data()
        #self.mw.clearButton.clicked.connect(self.clearGraphClicked)

        #self.blue.signals.dataUpdated.connect(self.graph.updateData)

    def calibrate_short_button(self):
        # from and to frequency
        cal_type = "short"
        from_f = 25
        to_f = 2700
        step_f = 1
        pwr_int = int(self.mw.comboBox_3.currentText()[0])
        command = "AMS_SWEEP(" + str(from_f) + ", " + str(to_f) + ", " + str(step_f) + "," + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.mw.setFinishedConnector(self.calibration_finished)
            self.cal_next_type = cal_type
            self.cal_next_pwr = str(pwr_int)
            delete_cal_data(cal_type, str(pwr_int))
            self.graph.clear()
            self.blue.send_message(command)
            self.start_data_reception(cal_type + "_" +str(pwr_int))
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

    def calibrate_match_button(self):
        # from and to frequency
        cal_type = "match"
        from_f = 25
        to_f = 2700
        step_f = 1
        pwr_int = int(self.mw.comboBox_3.currentText()[0])
        command = "AMS_SWEEP(" + str(from_f) + ", " + str(to_f) + ", " + str(step_f) + "," + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.mw.setFinishedConnector(self.calibration_finished)
            self.cal_next_type = cal_type
            self.cal_next_pwr = str(pwr_int)
            delete_cal_data(cal_type, str(pwr_int))
            self.graph.clear()
            self.blue.send_message(command)
            self.start_data_reception(cal_type + "_" +str(pwr_int))
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

    def test_measure_button(self):
        # from and to frequency
        print("CALLING")
        cal_type = "none"
        from_f = 25
        to_f = 2700
        step_f = 1
        pwr_int = int(self.mw.comboBox_3.currentText()[0])
        command = "AMS_SWEEP(" + str(from_f) + ", " + str(to_f) + ", " + str(step_f) + "," + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.cal_next_type = cal_type
            self.cal_next_pwr = str(pwr_int)
            self.blue.send_message(command)
            self.graph.clear()
            self.start_data_reception("testline")
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

    def start_data_reception(self, name=None):
        self.mw.setDataConnector(self.graph.newDataArrived)
        self.graph.createNewPlotLine(name)
        bt_thread = threading.Thread(target=self.blue.data_reception_cycle, args=(), daemon=True)
        bt_thread.start()

    def calibration_finished(self, msg):
        # when calibration is finished save all data to file
        cal_data = self.graph.plotLines[-1].getData()
        print(self.graph.plotLines[-1].getData())
        save_cal_data(self.cal_next_type, self.cal_next_pwr, cal_data)
        # to prevent unvanted overwrites
        self.mw.setFinishedConnector(function())

    def combotextChanged(self):
        self.update_cal_data()

    def update_cal_data(self):
        pwr_str = self.mw.comboBox_3.currentText()[0]
        short_cal_data = get_cal_data("short", pwr_str)
        match_cal_data = get_cal_data("match", pwr_str)
        self.graph.clear()
        if (short_cal_data):
            self.graph.plot(short_cal_data[0], short_cal_data[1], "short_" + get_pwrtext(pwr_str))
        if (match_cal_data):
            self.graph.plot(match_cal_data[0], match_cal_data[1], "match_" + get_pwrtext(pwr_str))

class SingleTab:

    def __init__(self, mainwindow):
        self.mw = mainwindow
        self.blue = mainwindow.blue
        
        self.mw.singleStartButton.clicked.connect(self.start_single)
        self.mw.singleStopButton.clicked.connect(self.mw.sendStop)

    def start_single(self):
        # from and to frequency
        f = int(self.mw.singleFreqEdit.text())
        if f<25 or f>6000:
            # invalid freq
            return
        pwr_int = int(self.mw.comboBox_3.currentText()[0])
        command = "AMS_SINGLE(" + str(f) + ", " + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.blue.send_message(command)
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

cal_short = load_data_manual_csv("calibration_short.csv")
cal_match = load_data_manual_csv("calibration_match.csv")