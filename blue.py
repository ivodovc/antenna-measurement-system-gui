import socket
import time
from bluetooth import *
from PyQt6 import QtGui
from PyQt6.QtCore import *
import threading

class CustomSignals(QObject):
    statusChanged = pyqtSignal(str)
    dataUpdated = pyqtSignal(str)
    singleDataUpdated = pyqtSignal(str)

class Blue:

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.device_combo = self.mainwindow.devices_comboBox
        self.mainwindow.refreshButton.clicked.connect(self.list_devices)
        self.mainwindow.disconnectButton.clicked.connect(self.disconnect)
        self.mainwindow.connectButton.clicked.connect(self.connectButtonAction)
        self.mainwindow.amsversionButton.clicked.connect(self.amsversion)
        self.mainwindow.amshowareyouButton.clicked.connect(self.amshowareyou)
        self.connected = False
        self.signals = CustomSignals()
        #print(self.amberStyleSheet)

    def connectButtonAction(self):
        self.x = threading.Thread(target=self.connect, args=(), daemon=True)
        self.x.start()

    def connect(self):
        HC06_address = '98:D3:31:90:53:B3' # Server Address
        port = 1  # HC06 setting
        self.s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        #self.mainwindow.status_widget.setStyleSheet(self.amberStyleSheet)
        self.signals.statusChanged.emit("attempting")
        try:
            self.s.connect((HC06_address,port))
        except Exception as e:
            print("Bluetooth Connection to HC06 failed", e)
            self.setConnected(False)
            return
        print("Connection established")
        self.setConnected(True)
        self.s.setblocking(1)
        self.s.settimeout(1) # 100ms timeout

    def send_message(self, message):
        if (self.isConnected()):
            self.s.send(bytes(message, 'UTF-8'))
        else:
            return 0

    # Starts receving data and sending it to function f
    # cycle in loop until timeout or ]
    # run in other thread
    def data_reception_cycle(self):
        try:
            while 1:
                data = self.s.recv(1024).decode('utf-8')
                self.signals.dataUpdated.emit(data)
                if ';' in data:
                    print("Succseful")
                    return
                if (len(data)==0):
                    return
        except Exception as e:
            print(e)
            return

    # Starts receving data and sending it to function f
    # cycle in loop until timeout or ]
    # run in other thread
    # signal to emit
    def data_reception_cycle2(self, signal):
        try:
            while 1:
                data = self.s.recv(1024).decode('utf-8')
                if ';' in data:
                    print("Succseful")
                    return
                signal.emit(data)
                if (len(data)==0):
                    return
        except Exception as e:
            print(e)
            return

    def disconnect(self):
        if hasattr(self, 's'):
            self.s.close()
        self.setConnected(False)

    def list_devices(self):
        nearby_devices = discover_devices(lookup_names = True)
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
        time.sleep(0.1)
        try:
            response = self.s.recv(1024).decode('utf-8')
            self.mainwindow.amsversionText.setText(response)
        except Exception as e:
            self.mainwindow.amsversionText.setText("Not responed")

    def amshowareyou(self):
        self.send_message("AMS_HOWAREYOU()")
        time.sleep(0.5)
        try:
            response = self.s.recv(1024).decode('utf-8')
            self.mainwindow.amsversionText.setText(response)
        except Exception as e:
            self.mainwindow.amsversionText.setText("Not responed")
