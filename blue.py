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
        self.s.settimeout(0.1) # 100ms timeout
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
        i = 0
        while 1:
            s = "{"+ str(i) + ", "
            s2 =  str(i**2) + "};"
            if (i%2==0):
                f(s)
            else:
                f(s2)
            i+=1
            if i>100:
                break
            """try:
                data = self.s.recv(1024)
            except Exception as e:
                print(e)
                break
            f(data)
            if "]" in data:
                break"""

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

def ref():
    HC06_address = '98:D3:31:90:53:B3' # Server Address
    port = 1  # HC06 setting
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.connect((HC06_address,port))
    s.setblocking(1)
    s.settimeout(0.1)
    buffer = ""
    print("Connected. Type something...")
    while 1:
        try:
            data = s.recv(1024)
            buffer += data.decode('utf-8')
            if "\n" in buffer:
                print(buffer)
                buffer = ""
        except Exception as e:
            #print(e)
            pass

    while 1:
        text = input()
        if text == "quit":
            break
        s.send(bytes(text, 'UTF-8'))
        data = s.recv(1024)
        print(data)
    s.close()