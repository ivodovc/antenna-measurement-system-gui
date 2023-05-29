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

import socket
from bluetooth import *
from PyQt6.QtCore import *
import threading


class CustomSignals(QObject):
    statusChanged = pyqtSignal(str)
    dataUpdated = pyqtSignal(str)
    singleDataUpdated = pyqtSignal(str)
    dataStreamFinished = pyqtSignal(str)


class Blue:

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.device_combo = self.mainwindow.devices_comboBox
        self.mainwindow.refreshButton.clicked.connect(self.list_devices)
        self.mainwindow.disconnectButton.clicked.connect(self.disconnect)
        self.mainwindow.connectButton.clicked.connect(self.connectButtonAction)
        self.mainwindow.amsversionButton.clicked.connect(self.amsversion)
        self.mainwindow.lowPowerButton.clicked.connect(self.setLowPower)
        self.mainwindow.wakeUpButton.clicked.connect(self.wakeUp)

        self.mainwindow.defaultDeviceRadioButton.toggled.connect(self.radiobuttonschanged)
        self.connected = False
        self.signals = CustomSignals()

    def connectButtonAction(self):
        self.x = threading.Thread(target=self.connect, args=(), daemon=True)
        self.x.start()

    def connect(self):
        # Server Address is set
        if (self.mainwindow.defaultDeviceRadioButton.isChecked()):
            HC06_address = '98:D3:31:90:53:B3'
        elif (self.mainwindow.customDeviceRadioButton.isChecked()):
            addr = self.mainwindow.customAddressEdit.text()
            HC06_address = addr
            print(HC06_address)
        port = 1  # HC06 setting
        self.s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        # self.mainwindow.status_widget.setStyleSheet(self.amberStyleSheet)
        self.signals.statusChanged.emit("attempting")
        try:
            self.s.connect((HC06_address, port))
        except Exception as e:
            print("Bluetooth Connection to HC06 failed", e)
            self.setConnected(False)
            return
        print("Connection established")
        self.setConnected(True)
        self.s.setblocking(1)
        # 1000ms timeout
        self.s.settimeout(1)

    def send_message(self, message):
        if (self.isConnected()):
            self.s.send(bytes(message, 'UTF-8'))
        else:
            return 0

    def flush_buffer(self):
        if (self.isConnected()):
            self.s.setblocking(0)
            try:
                while 1:
                    msg = self.s.recv(1024).decode('utf-8')
            except Exception as e:
                self.s.setblocking(1)
                return
        else:
            return 0

    # receives message till termination syombl;
    def receive_message(self):
        received_msg = ""
        if (self.isConnected()):
            while 1:
                msg = self.s.recv(1024).decode('utf-8')
                received_msg += msg
                if ';' in msg:
                    print("Succseful")
                    return received_msg
                if (len(msg) == 0):
                    return received_msg
        else:
            return 0

    # Starts receving data and sending it to function f
    # cycle in loop until timeout or ]
    # run in other thread
    def data_reception_cycle(self):
        self.flush_buffer()
        self.s.setblocking(1)
        self.s.settimeout(1)
        try:
            while 1:
                data = self.s.recv(1024).decode('utf-8')
                self.signals.dataUpdated.emit(data)
                if ';' in data:
                    self.signals.dataStreamFinished.emit("success")
                    return
                if (len(data) == 0):
                    return
        except Exception as e:
            print(e)
            return

    # Starts receving data and sending it to function f
    # cycle in loop until timeout or ]
    # run in other thread
    # signal to emit
    def data_reception_cycle2(self, signal):
        self.flush_buffer()
        self.s.setblocking(1)
        self.s.settimeout(1)
        try:
            while 1:
                data = self.s.recv(1024).decode('utf-8')
                if ';' in data:
                    return
                signal.emit(data)
                if (len(data) == 0):
                    return
        except Exception as e:
            print(e)
            return

    def disconnect(self):
        if hasattr(self, 's'):
            self.s.close()
        self.setConnected(False)

    def list_devices(self):
        nearby_devices = discover_devices(lookup_names=True)
        for addr, name in nearby_devices:
            self.device_combo.addItem(name + "(" + addr + ")")

    def setConnected(self, b):
        if b:
            self.connected = True
            self.signals.statusChanged.emit("connected")

        else:
            self.connected = False
            self.signals.statusChanged.emit("not_connected")

    def isConnected(self):
        return self.connected

    def amsversion(self):
        self.send_message("AMS_VERSION()")
        try:
            self.flush_buffer()
            response = self.receive_message()
            to_display = response.split("AMS_MSG(")[1].split(");")[0]
            self.mainwindow.amsversionText.setText(to_display)
        except Exception as e:
            self.mainwindow.amsversionText.setText("Error:", e)
            print(e)

    def amshowareyou(self):
        self.send_message("AMS_HOWAREYOU()")
        try:
            self.flush_buffer()
            response = self.receive_message()
            to_display = response.split("AMS_MSG(")[1].split(");")[0]
            self.mainwindow.amsversionText.setText(to_display)
        except Exception as e:
            self.mainwindow.amsversionText.setText("Error: ", e)
            print(e)

    def setLowPower(self):
        self.send_message("AMS_LOWPOWER()")
        try:
            self.flush_buffer()
            response = self.receive_message()
            to_display = response.split("AMS_MSG(")[1].split(");")[0]
            self.mainwindow.powerText.setText(to_display)
        except Exception as e:
            self.mainwindow.powerText.setText("Error: ", e)
            print(e)

    def wakeUp(self):
        self.send_message("AMS_WAKEUP()")
        try:
            self.flush_buffer()
            response = self.receive_message()
            to_display = response.split("AMS_MSG(")[1].split(");")[0]
            self.mainwindow.powerText.setText(to_display)
        except Exception as e:
            self.mainwindow.powerText.setText("Error: ", e)
            print(e)

    def radiobuttonschanged(self):
        if (self.mainwindow.defaultDeviceRadioButton.isChecked()):
            self.mainwindow.connection_widget.setEnabled(False)
        elif (self.mainwindow.customDeviceRadioButton.isChecked()):
            self.mainwindow.connection_widget.setEnabled(True)