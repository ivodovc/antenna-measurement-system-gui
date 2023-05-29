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

from PyQt6 import QtWidgets
from PyQt6.QtCore import *
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
    def __init__(self, mainwindow, graphwidget):
        self.mainwindow = mainwindow
        self.graphwidget = graphwidget
        self.init_plot()
        self.graphwidgetgeometry = self.graphwidget.frameGeometry()
        self.reference_lines = {}
        self.plotLines = []
        self.data_x, self.data_y = [],[]
        self.clear()

    def plot(self, x, y, name):
        if "csv" in name:
            plot_color=(random.random()*255, random.random()*255, random.random()*255)
            w = 2
        else:
            plot_color=(random.random()*255, random.random()*255, random.random()*255)
            w = 3
        pen = pg.mkPen(color=plot_color, width=w)
        plotLine = self.graphwidget.plot(x, y, pen=pen, name=name)
        self.plotLines.append(plotLine)

    def clear(self):
        self.graphwidget.clear()
        self.plotLines = []
        self.draw_reference_lines()
        #self.infinite_line = self.graphwidget.infiniteLine(750)

    def draw_reference_lines(self):
        for line in self.reference_lines:
            data = self.reference_lines[line]
            self.plot(data[0], data[1], line)

    def init_plot(self):
        self.graphwidget.setBackground('w')
        self.graphwidget.setTitle("ADC = f(freq)")
        styles = {'color':'r', 'font-size':'20px'}
        self.graphwidget.setLabel('left', 'ADC', **styles)
        self.graphwidget.setLabel('bottom', 'freq [MHz]', **styles)
        self.graphwidget.addLegend()
        self.graphwidget.invertY(True)

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
        self.data_x += fx
        self.data_y += fy
        self.plotLines[-1].setData(self.data_x, self.data_y)

    def prepareForContTracing(self):
        self.index = 0
        self.x, self.y = [],[]
        self.i = None
        self.raw_buffer = ""
        self.buff_index = 0
        self.continuous_points = self.graphwidget.plot([0], [0], pen=None, symbol='o', symbolSize=5, symbolBrush=('r'))

    def newDataArrivedCont(self, data):
        fx,fy = self.split_raw_data(data)
        if len(fx)>0:
            self.continuous_points.setData([fx[-1]], [fy[-1]])
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
                #x_int, y_int = int(x), int(y)
                x_int, y_int = float(x), float(y)
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

        self.mw.intStepRadioButton.toggled.connect(self.step_radio_button_changed)
        self.mw.singleRadioButton.toggled.connect(self.sweep_radio_button_changed)

        self.mw.comboBox.currentTextChanged.connect(self.combotextChanged)
        self.update_ref_data()
        self.step_radio_button_changed()

    def clearGraphClicked(self):
        self.graph.clear()

    def measButtonClicked(self):
        if (self.mw.singleRadioButton.isChecked()):
            self.startNormalSweep()
        elif (self.mw.contRadioButton.isChecked()):
            self.startContSweep()
        
    def startContSweep(self):
        # get params
        parsed_args = self.getSweepInputs()
        if parsed_args is not None:
            from_int, to_int, step_int, pwr_int = parsed_args
        else:
            #bad parsing
            return
        self.graph.graphwidget.setXRange(from_int, to_int)
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
        self.graph.graphwidget.setXRange(from_int, to_int)
        if (self.mw.intStepRadioButton.isChecked()):
            command = "AMS_SWEEP(" + str(from_int) + ", " + str(to_int) + ", " + str(step_int) + "," + str(pwr_int) + ")"
        elif (self.mw.miniStepRadioButton.isChecked()):
            command = "AMS_SWEEP_NDIV(" + str(from_int) + ", " + str(to_int) + ", " + str(1) + "," + str(pwr_int) + "," + str(int(1/step_int)) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.blue.send_message(command)
            self.start_data_reception()
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")

    def newWindowButtonClicked(self):
        self.graph.openInNewWindow()

    def get_correct_step(self):
        if (self.mw.intStepRadioButton.isChecked()):
            step_int = int(self.mw.stepEdit.text())
            if (step_int<1):
                return None
            else:
                return step_int
        elif (self.mw.miniStepRadioButton.isChecked()):
            step_text = self.mw.step_comboBox.currentText().split()[0]
            step_unit = self.mw.step_comboBox.currentText().split()[1]
            step_float = float(step_text)
            if step_unit == "MHz":
                return step_float
            elif step_unit == "kHz":
                return step_float/1000
            return None

    def getSweepInputs(self):
        from_text = self.mw.fromEdit.text()
        to_text = self.mw.toEdit.text()
        pwr_int = int(self.mw.comboBox.currentText()[0]) # first character is power level

        from_int, to_int, step_num = 0,0,0
        # check if params are digits
        try:
            from_int = int(from_text)
            to_int = int(to_text)
            step_num = self.get_correct_step()
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
        if (step_num >= to_int-from_int):
            self.mw.msgLabel.setText("Step is too big")
            return
        #if (step_num < 1):
            #self.mw.msgLabel.setText("Step is too small")
            #return
        return from_int, to_int, step_num, pwr_int

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

    def combotextChanged(self):
        self.update_ref_data()

    def update_ref_data(self):
        pwr_str = self.mw.comboBox.currentText()[0]
        ref = get_all_references_for_pwr(pwr_str)
        self.graph.reference_lines = ref
        self.graph.clear()

    def step_radio_button_changed(self):
        if (self.mw.intStepRadioButton.isChecked()):
            self.mw.label_4.setEnabled(True)
            self.mw.stepEdit.setEnabled(True)
            self.mw.step_comboBox.setEnabled(False)
            self.mw.label_27.setEnabled(False)
        elif (self.mw.miniStepRadioButton.isChecked()):
            self.mw.singleRadioButton.setChecked(True)
            self.mw.step_comboBox.setEnabled(True)
            self.mw.label_27.setEnabled(True)
            self.mw.label_4.setEnabled(False)
            self.mw.stepEdit.setEnabled(False)

    def sweep_radio_button_changed(self):
        if (self.mw.contRadioButton.isChecked()):
            self.mw.intStepRadioButton.setChecked(True)

class CalibrationTab:
    
    def __init__(self, mainwindow):
        self.mw = mainwindow
        self.blue = mainwindow.blue

        self.graph = GraphHandler(self.mw, self.mw.calibrateGraphWidget)
        
        self.mw.calibrateEditButton.clicked.connect(self.calibrate_edit_button)
        self.mw.comboBox_3.currentTextChanged.connect(self.combotextChanged)

        self.update_cal_data()
        # self.mw.clearButton.clicked.connect(self.clearGraphClicked)

        # self.blue.signals.dataUpdated.connect(self.graph.updateData)

    def calibrate_edit_button(self):
        # from and to frequency
        ref_name = self.mw.refnameEdit.text()
        ref_name = check_filename_available(ref_name, self.mw.comboBox_3.currentText()[0])
        self.mw.refnameEdit.setText(ref_name)
        from_text = self.mw.calibFromEdit.text()
        to_text = self.mw.calibToEdit.text()
        step_text = self.mw.calibStepEdit.text()
        from_f = int(from_text)
        to_f = int(to_text)
        step_f = int(step_text)
        pwr_int = int(self.mw.comboBox_3.currentText()[0])
        command = "AMS_SWEEP(" + str(from_f) + ", " + str(to_f) + ", " + str(step_f) + "," + str(pwr_int) + ")"
        # self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.mw.setFinishedConnector(self.calibration_finished)
            self.cal_next_name = ref_name
            self.cal_next_pwr = str(pwr_int)
            self.graph.clear()
            self.blue.send_message(command)
            self.start_data_reception(ref_name + "_" + str(pwr_int))
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
        save_reference(self.cal_next_name, self.cal_next_pwr, cal_data)
        # to prevent unvanted overwrites set empty function
        self.mw.setFinishedConnector(lambda: None)

    def combotextChanged(self):
        self.update_cal_data()

    def update_cal_data(self):
        pwr_str = self.mw.comboBox_3.currentText()[0]
        ref = get_all_references_for_pwr(pwr_str)
        self.graph.reference_lines = ref
        self.graph.clear()


class SingleTab:

    def __init__(self, mainwindow):
        self.mw = mainwindow
        self.blue = mainwindow.blue

        self.mw.singleStartButton.clicked.connect(self.start_single)
        self.mw.singleStopButton.clicked.connect(self.mw.sendStop)

    def start_single(self):
        # from and to frequency
        f = int(self.mw.singleFreqEdit.text())
        if f < 25 or f > 6000:
            # invalid freq
            return
        pwr_int = int(self.mw.singleComboBox.currentText()[0])
        command = "AMS_SINGLE(" + str(f) + ", " + str(pwr_int) + ")"
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.blue.send_message(command)
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")


class AdvancedTab:

    def __init__(self, mainwindow):
        self.mw = mainwindow
        self.blue = mainwindow.blue

        self.mw.sendRegistersButton.clicked.connect(self.send_regs)
        self.mw.stopRegistersButton.clicked.connect(self.mw.sendStop)

    def send_regs(self):
        # from and to frequency
        reg0_text = self.mw.reg0Edit.text()
        reg1_text = self.mw.reg1Edit.text()
        reg2_text = self.mw.reg2Edit.text()
        reg3_text = self.mw.reg3Edit.text()
        reg4_text = self.mw.reg4Edit.text()
        reg5_text = self.mw.reg5Edit.text()
        try:
            reg0_int = int(reg0_text, 16)
            reg1_int = int(reg1_text, 16)
            reg2_int = int(reg2_text, 16)
            reg3_int = int(reg3_text, 16)
            reg4_int = int(reg4_text, 16)
            reg5_int = int(reg5_text, 16)
        except Exception as e:
            print("Error when parsing register values", e)
            return
        command = "AMS_REGISTER(" + reg0_text + ", " + reg1_text + ", " + reg2_text + ", " + reg3_text + ", " + reg4_text + ", " + reg5_text + ")"
        if len(command) > 100:
            print("Command too long when sending registers")
            return
        self.mw.msgLabel.setText("Command '" + command + "' sent.")
        if (self.blue.isConnected()):
            self.blue.send_message(command)
        else:
            self.mw.msgLabel.setText("Not connected to AMS ")
