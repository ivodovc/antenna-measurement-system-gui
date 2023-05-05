import socket
import time
from bluetooth import *
from PyQt6 import QtGui

class Blue:

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.device_combo = self.mainwindow.devices_comboBox
        self.mainwindow.refreshButton.clicked.connect(self.list_devices)
        self.mainwindow.disconnectButton.clicked.connect(self.disconnect)
        self.mainwindow.connectButton.clicked.connect(self.connect)
        self.mainwindow.amsversionButton.clicked.connect(self.amsversion)
        self.mainwindow.amshowareyouButton.clicked.connect(self.amshowareyou)
        self.connected = False

    def connect(self):
        HC06_address = '98:D3:31:90:53:B3' # Server Address
        port = 1  # HC06 setting
        self.s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.mainwindow.con_status.setText("Attempting...")
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
        pass

    def send_message(self, message):
        if (self.isConnected()):
            self.s.send(bytes(message, 'UTF-8'))
        else:
            return 0

    # Starts receving data and sending it to function f
    # cycle in loop until timeout or ]
    # run in other thread
    def data_reception_cycle(self, f):
        try:
            while 1:
                data = self.s.recv(1024).decode('utf-8')
                if "]" in data:
                    print("Succseful")
                    return
                f(data)
                if (len(data)==0):
                    return
        except Exception as e:
            print(e)
            return

    def disconnect(self):
        self.s.close()
        self.setConnected(False)

    def list_devices(self):
        nearby_devices = discover_devices(lookup_names = True)
        for addr, name in nearby_devices:
            self.device_combo.addItem(name + "(" + addr + ")") 

    def setConnected(self, b):
        if b:
            self.connected = True
            self.mainwindow.con_status.setText("AMS connected")
            self.mainwindow.status_wrap.setStyleSheet('background-color: rgb(104, 255, 101);')
            
        else:
            self.connected = False
            self.mainwindow.con_status.setText("Not connected")
            self.mainwindow.status_wrap.setStyleSheet('background-color: rgb(255, 104, 101);')

    def isConnected(self):
        return self.connected

    def amsversion(self):
        self.send_message("AMS_VERSION()")
        try:
            response = self.s.recv(1024).decode('utf-8')
            self.mainwindow.amsversionText.setText(response)
        except Exception as e:
            self.mainwindow.amsversionText.setText("Not responed")

    def amshowareyou(self):
        self.send_message("AMS_HOWAREYOU()")
        try:
            response = self.s.recv(1024).decode('utf-8')
            self.mainwindow.amsversionText.setText(response)
        except Exception as e:
            self.mainwindow.amsversionText.setText("Not responed")
