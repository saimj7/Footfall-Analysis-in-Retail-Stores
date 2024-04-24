import cv2
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QDialog, QListWidget, QAction, qApp, QDesktopWidget, QFileDialog, QMessageBox, QWidget, QTableWidget,QTableWidgetItem,QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5.uic import loadUi, loadUiType
from tqdm import tqdm
from processor.detectracker.tracker import Detectracker
from processor.agender.gender import Agender
from analyser.heatmap import Heatmap
from analyser.dwell import Dwell
from windows.customer import CustomerItem


class DeviceWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super(DeviceWindow, self).__init__(*args, **kwargs)

        loadUi("./UI/DeviceWindow.ui", self)

        # Connection for file open button
        self.btnOpen.clicked.connect(self.getFilePath)

        # Connection for web cam selection
        self.cbCam.currentIndexChanged.connect(self.selectCam)

        # Connection for file ok button
        self.btnOk.clicked.connect(self.clickOk)

        # Connection for file cancel button
        self.btnCancel.clicked.connect(self.clickCancel)

        # Get ip camera url
        self.ip_url = ""

        # Mode
        self.mode = 0

        # Get list all webcams and add them in combobox
        self.device_list = self.getCamArr()
        self.cbCam.clear()
        for item in self.device_list:
            self.cbCam.addItem(item)
        self.camNum = 0

    # Connection for file ok button
    @QtCore.pyqtSlot()
    def clickOk(self):
        if self.boolFile.isChecked():
            self.cap = cv2.VideoCapture(str(self.fileName))
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
            self.mode = 1
        elif self.boolWebCam.isChecked():
            self.camNum = self.cbCam.currentIndex()
            #self.cap = cv2.VideoCapture(str(self.camNum)) # FIXME
            self.cap = cv2.VideoCapture(0) # Using the default webcam (0) for now
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
            self.mode = 2
        else:
            self.ip_url = self.editURL.text()
            self.cap = cv2.VideoCapture(self.ip_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
            self.mode = 3
        self.close()

    # Connection for file cancel button
    @QtCore.pyqtSlot()
    def clickCancel(self):
        self.mode = 0
        self.close()

    # Connection for file open button
    @QtCore.pyqtSlot()
    def getFilePath(self):
        fileName = QFileDialog.getOpenFileName(self, 'Open File', 'Dataset\\',"Video files (*.mp4 *.avi)")
        self.fileName = fileName[0]
        self.editPath.setText(fileName[0])
        self.setShelve = False

    # Select camera
    @QtCore.pyqtSlot()
    def selectCam(self):
        return self.cbCam.currentIndex()

    # Get the number of cameras
    def getCamArr(self):
        index = 0
        arr = []
        while True:
            cap = cv2.VideoCapture(index)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
            if not cap.read()[0]:
                break
            else:
                arr.append("Cam : " + str(index))
            cap.release()
            index += 1
        return arr
