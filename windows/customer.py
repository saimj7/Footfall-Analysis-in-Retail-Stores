import numpy as np
from time import localtime, asctime
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from PyQt5 import QtGui
from PyQt5.QtGui import QImage, QPixmap


# Custom class to show customer information
class CustomerItem (QtWidgets.QListWidget):
    def __init__ (self, parent = None):
        super(CustomerItem, self).__init__(parent)
        loadUi("./UI/CustomerItem.ui", self)

    # Set data
    def setData(self, data):
        self.setID(data[0])
        self.setStartTime(data[1])        
        self.setEndTime(data[2])
        self.setDwellTime(data[3])
        self.setCustomerImage(data[4])
        self.setAge(data[6])
        self.setGender(data[7])

    # Set age
    def setAge(self, age):
        self.lblAge.setText(age)

    # Set gender
    def setGender(self, gender):
        self.lblGender.setText(gender)

    # Set ID
    def setID(self, id):
        self.lblID.setText(str(id))

    # Set start time
    def setStartTime(self, time):
        self.lblStart.setText(str(np.round(time, 2)))

    # Set end time
    def setEndTime(self, time):
        self.lblEnd.setText(str(np.round(time, 2)))

    # Set dwell time
    def setDwellTime(self, time):
        self.lblDwell.setText(str(np.round(time, 2)))

    # Set image
    def setCustomerImage(self, frame):
        frame = frame.copy()
        #img = QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        img = QImage(frame.tobytes(), frame.shape[1], frame.shape[0], frame.strides[0], QtGui.QImage.Format_RGB888)
        #img = img.rgbSwapped()
        pix = QPixmap.fromImage(img)
        self.faceImage.setPixmap(pix)
        self.faceImage.show()
