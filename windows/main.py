import cv2
import random as rng
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QStatusBar, QListWidget, QAction, qApp, QDesktopWidget, QFileDialog, QMessageBox, QWidget, QTableWidget,QTableWidgetItem,QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5.uic import loadUi
from tqdm import tqdm
from processor.detectracker.tracker import Detectracker
from processor.agender.gender import Agender
from analyser.heatmap import Heatmap
from analyser.dwell import Dwell
from windows.customer import CustomerItem
from windows.device import DeviceWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("./UI/MainWindow.ui", self)

        self.live_preview.setScaledContents(True)
        from PyQt5.QtWidgets import QSizePolicy
        self.live_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.cam_clear_gaurd = False

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Welcome!")

        # Connection for file open button
        self.btnAddInsideSrc.clicked.connect(self.addInsideSrc)

        # Connection for file open button
        self.btnAddOutsideSrc.clicked.connect(self.addOutsideSrc)

        # Connection for start of processing
        self.btnStart.clicked.connect(self.startProcess)

        # Connection for pause of processing
        self.btnPause.clicked.connect(self.pauseProcess)

        # Connection for pause of processing
        self.btnStop.clicked.connect(self.stopProcess)

        # Connection for add shelve button
        self.btnAddShelve.clicked.connect(self.addShelve)

        # Connection for reset shelve
        self.btnResetShelve.clicked.connect(self.resetShelve)

        # Clear video sources list
        self.listInsideSrc.clear()
        self.inCap = []

        self.backFrame = []
        self.width = []
        self.height = []

        # Heatmap
        self.heatmap = []

        # Dwell time
        self.inDwell = []
        self.outDwell = []

        # Clear video sources list
        self.listOutsideSrc.clear()
        self.outCap = []

        # Detect and tracker
        self.inDetectors = []
        self.outDetectors = []

        # Age and gender predictor
        self.gender = Agender()

        # Video file name to be processsed
        self.fileName = ""

        # Frame rate
        self.fps = 0

        # Frame number
        self.frameNo = 0

        # Set running status
        self.running = False

        # Set shelve status
        self.setShelve = False

        # Set shelve list
        self.shelve_list_list = []

        # Set customer list
        self.log_tabwidget.clear()
        self.customer_list = QListWidget(self)
        self.recommend_list = QListWidget(self)
        self.log_tabwidget.addTab(self.customer_list, "Monitoring")
        self.log_tabwidget.addTab(self.recommend_list, "Analysis")

        # Tab control
        self.log_tabwidget.blockSignals(True) #just for not showing the initial message
        self.log_tabwidget.currentChanged.connect(self.onTabChange) #changed!
        self.log_tabwidget.blockSignals(False)
        self.log_tabwidget.setTabEnabled(1, False);

        # Set timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)

        # Set colors
        self.color = []
        self.color.append((255, 0, 0))
        self.color.append((0, 255, 0))
        self.color.append((0, 0, 255))
        self.color.append((0, 0, 0))
        self.color.append((255, 255, 255))
        self.color.append((17, 15, 100))
        self.color.append((50, 56, 200))
        self.color.append((86, 31, 4))
        self.color.append((220, 88, 50))
        self.color.append((25, 146, 190))
        self.color.append((62, 174, 250))
        self.color.append((103, 86, 65))
        self.color.append((145, 133, 128))

    # Closing window event
    def closeEvent(self, event):
        close = QMessageBox()
        close.setText("Do you want to quit?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            if self.running:
                self.timer.stop()
                for cap in self.inCap:
                    cap.release()
                for cap in self.outCap:
                    cap.release()
                self.statusBar.showMessage("Stopping...")

            event.accept()
        else:
            event.ignore()

    #@QtCore.pyqtSlot()
    def onTabChange(self, i):
        if i == 1:
            for ii in range(len(self.shelve_list_list)):
                shelve_list = self.shelve_list_list[ii]
                if len(shelve_list) > 0:
                    data = self.inDwell[ii].get_log_data()
                    #data = self.dwell.get_log_data()
                    num_user = len(data)
                    num_shelve = len(shelve_list)
                    id_list = []
                    age_list = []
                    gender_list = []

                    for j in range(len(data)):
                        id_list.append(data[j][0])
                        age_list.append(data[j][6])
                        gender_list.append(data[j][7])
                    status_table = np.zeros((num_user, num_shelve))
                    for j in range(len(data)):
                        temp = []
                        for k in range(len(data)):
                            temp.append([])
                        for k in range(len(data[j][5])):
                            shelve = self.find_shelve(shelve_list, data[j][5][k])
                            temp[shelve].append(round(data[j][8][k], 2))
                        for k in range(len(shelve_list)):
                            if len(temp[k]) > 0:
                                status_table[j][k] = max(temp[k]) - min(temp[k])

                    # Write result
                    import csv
                    gender_list = [x.lower() for x in gender_list]
                    with open("data/logs/status_table_" + str(ii) + ".csv", "w", newline = '') as csv_file:
                        writer = csv.writer(csv_file, delimiter = ',')
                        header = ["ID", "Age", "Gender"]
                        for iii in range(len(shelve_list)):
                            header.append(str(iii))
                        writer.writerow(header)
                        for iii in range(len(id_list)):
                            line = [str(id_list[iii]), str(age_list[iii]), str(gender_list[iii])]
                            for j in range(len(shelve_list)):
                                line.append(status_table[iii][j])
                            writer.writerow(line)

                    # Add recommend
                    aver_wait_time = np.average(status_table, axis = 0)
                    total_aver_wait_time = np.mean(status_table)
                    sort_wait_time_index = np.argsort(aver_wait_time)
                    frequency = np.sum(status_table > 0, axis = 0)
                    sort_frequency_index = np.argsort(frequency)

                    male_ind = np.where(np.array(gender_list) == 'male')[0]
                    female_ind = np.where(np.array(gender_list) == 'female')[0]

                    if len(male_ind > 0):
                        male_table = status_table[male_ind, :]
                        male_frequency = np.sum(male_table > 0, axis = 0)
                        sort_male_frequency_index = np.argsort(male_frequency)
                    if len(female_ind > 0):
                        female_table = status_table[female_ind, :]
                        female_frequency = np.sum(female_table > 0, axis = 0)
                        sort_female_frequency_index = np.argsort(female_frequency)

                    print_num = int(len(shelve_list) * 1)
                    if print_num < 1:
                        print_num = 1
                    rec_total_wait_time = "The average wait time at the shelves is " + str(round(total_aver_wait_time, 2))
                    rec_wait_time_shelve = "The most waited shelves are: "
                    rec_freq_shelve = "The most popular shelves are: "
                    rec_free_shelve = "The most free shelves are: "
                    rec_male_freq_shelve = "The most popular shelves among males are: "
                    rec_female_freq_shelve = "The most popular shelves among females are: "

                    for iii in range(print_num):
                        rec_wait_time_shelve = rec_wait_time_shelve + str(sort_wait_time_index[-1 - iii]) + " "
                        rec_freq_shelve = rec_freq_shelve + str(sort_frequency_index[-1 - iii]) + " "
                        rec_free_shelve = rec_free_shelve + str(sort_frequency_index[iii]) + " "
                        if len(male_ind) > 0:
                            rec_male_freq_shelve = rec_male_freq_shelve + str(sort_male_frequency_index[-1 - iii]) + " "
                        if len(female_ind) > 0:
                            rec_female_freq_shelve = rec_female_freq_shelve + str(sort_female_frequency_index[-1 - iii]) + " "

                    item0 = QtWidgets.QListWidgetItem()
                    widget0 = QtWidgets.QWidget()
                    widgetText0 =  QtWidgets.QLabel("Region: " + str(ii))
                    widgetLayout0 = QtWidgets.QVBoxLayout()
                    widgetLayout0.addWidget(widgetText0)
                    widgetLayout0.addStretch()
                    widgetLayout0.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                    widget0.setLayout(widgetLayout0)
                    item0.setSizeHint(widget0.sizeHint())
                    self.recommend_list.addItem(item0)
                    self.recommend_list.setItemWidget(item0, widget0)

                    item1 = QtWidgets.QListWidgetItem()
                    widget1 = QtWidgets.QWidget()
                    widgetText1 =  QtWidgets.QLabel(rec_total_wait_time)
                    widgetLayout1 = QtWidgets.QVBoxLayout()
                    widgetLayout1.addWidget(widgetText1)
                    widgetLayout1.addStretch()
                    widgetLayout1.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                    widget1.setLayout(widgetLayout1)
                    item1.setSizeHint(widget1.sizeHint())
                    self.recommend_list.addItem(item1)
                    self.recommend_list.setItemWidget(item1, widget1)

                    item2 = QtWidgets.QListWidgetItem()
                    widget2 = QtWidgets.QWidget()
                    widgetText2 =  QtWidgets.QLabel(rec_wait_time_shelve)
                    widgetLayout2 = QtWidgets.QVBoxLayout()
                    widgetLayout2.addWidget(widgetText2)
                    widgetLayout2.addStretch()
                    widgetLayout2.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                    widget2.setLayout(widgetLayout2)
                    item2.setSizeHint(widget2.sizeHint())
                    self.recommend_list.addItem(item2)
                    self.recommend_list.setItemWidget(item2, widget2)

                    item3 = QtWidgets.QListWidgetItem()
                    widget3 = QtWidgets.QWidget()
                    widgetText3 =  QtWidgets.QLabel(rec_freq_shelve)
                    widgetLayout3 = QtWidgets.QVBoxLayout()
                    widgetLayout3.addWidget(widgetText3)
                    widgetLayout3.addStretch()
                    widgetLayout3.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                    widget3.setLayout(widgetLayout3)
                    item3.setSizeHint(widget3.sizeHint())
                    self.recommend_list.addItem(item3)
                    self.recommend_list.setItemWidget(item3, widget3)

                    item33 = QtWidgets.QListWidgetItem()
                    widget33 = QtWidgets.QWidget()
                    widgetText33 =  QtWidgets.QLabel(rec_free_shelve)
                    widgetLayout33 = QtWidgets.QVBoxLayout()
                    widgetLayout33.addWidget(widgetText33)
                    widgetLayout33.addStretch()
                    widgetLayout33.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                    widget33.setLayout(widgetLayout33)
                    item33.setSizeHint(widget33.sizeHint())
                    self.recommend_list.addItem(item33)
                    self.recommend_list.setItemWidget(item33, widget33)

                    if len(male_ind) > 0:
                        item4 = QtWidgets.QListWidgetItem()
                        widget4 = QtWidgets.QWidget()
                        widgetText4 =  QtWidgets.QLabel(rec_male_freq_shelve)
                        widgetLayout4 = QtWidgets.QVBoxLayout()
                        widgetLayout4.addWidget(widgetText4)
                        widgetLayout4.addStretch()
                        widgetLayout4.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                        widget4.setLayout(widgetLayout4)
                        item4.setSizeHint(widget4.sizeHint())
                        self.recommend_list.addItem(item4)
                        self.recommend_list.setItemWidget(item4, widget4)

                    if len(female_ind) > 0:
                        item5 = QtWidgets.QListWidgetItem()
                        widget5 = QtWidgets.QWidget()
                        widgetText5 =  QtWidgets.QLabel(rec_female_freq_shelve)
                        widgetLayout5 = QtWidgets.QVBoxLayout()
                        widgetLayout5.addWidget(widgetText5)
                        widgetLayout5.addStretch()
                        widgetLayout5.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                        widget5.setLayout(widgetLayout5)
                        item5.setSizeHint(widget5.sizeHint())
                        self.recommend_list.addItem(item5)
                        self.recommend_list.setItemWidget(item5, widget5)

                    self.tableWidget = QtWidgets.QTableWidget()
                    self.tableWidget.setRowCount(len(id_list) + 1)
                    self.tableWidget.setColumnCount(len(shelve_list) + 4)
                    self.tableWidget.setItem(0,0, QTableWidgetItem("No"))
                    self.tableWidget.setItem(0,1, QTableWidgetItem("User ID"))
                    self.tableWidget.setItem(0,2, QTableWidgetItem("Age"))
                    self.tableWidget.setItem(0,3, QTableWidgetItem("Gender"))
                    for iii in range(len(shelve_list)):
                        self.tableWidget.setItem(0, 4 + iii, QTableWidgetItem("Shelf" + str(iii)))
                    for iii in range(len(id_list)):
                        self.tableWidget.setItem(iii + 1, 0, QTableWidgetItem(str(iii + 1)))
                        self.tableWidget.setItem(iii + 1, 1, QTableWidgetItem(str(id_list[iii])))
                        if age_list[iii] != []:
                            self.tableWidget.setItem(iii + 1, 2, QTableWidgetItem(str(age_list[iii])))
                        if gender_list[iii] != []:
                            self.tableWidget.setItem(iii + 1, 3, QTableWidgetItem(str(gender_list[iii])))
                        for jj in range(len(shelve_list)):
                            self.tableWidget.setItem(iii + 1, 4 + jj, QTableWidgetItem(str(round(status_table[iii][jj], 2))))

                    item6 = QtWidgets.QListWidgetItem()
                    widget6 = QtWidgets.QWidget()
                    widgetLayout6 = QtWidgets.QVBoxLayout()
                    widgetLayout6.addWidget(self.tableWidget)
                    widgetLayout6.addStretch()
                    #widgetLayout6.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
                    widget6.setLayout(widgetLayout6)
                    item6.setSizeHint(widget6.sizeHint())
                    self.recommend_list.addItem(item6)
                    self.recommend_list.setItemWidget(item6, widget6)

    # Connection for adding devices button
    @QtCore.pyqtSlot()
    def addInsideSrc(self):
        device_window = DeviceWindow(self)
        device_window.exec_()

        if device_window.mode != 0:
            if device_window.mode == 1:
                self.listInsideSrc.addItem(device_window.fileName)
            elif device_window.mode == 2:
                self.listInsideSrc.addItem("Webcam: " + str(device_window.camNum))
            else:
                self.listInsideSrc.addItem(device_window.ip_url)
            self.inCap.append(device_window.cap)
            self.shelve_list_list.append([])

    # Connection for adding devices button
    @QtCore.pyqtSlot()
    def addOutsideSrc(self):
        device_window = DeviceWindow(self)
        device_window.exec_()

        if device_window.mode != 0:
            if device_window.mode == 1:
                self.listOutsideSrc.addItem(device_window.fileName)
            elif device_window.mode == 2:
                self.listOutsideSrc.addItem("Webcam: " + str(device_window.camNum))
            else:
                self.listOutsideSrc.addItem(device_window.ip_url)
            self.outCap.append(device_window.cap)

    def toQImage(self, raw_img):
        from numpy import copy
        img = copy(raw_img)
        qformat = QImage.Format_Indexed8
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        outImg = QImage(img.tobytes(), img.shape[1], img.shape[0], img.strides[0], qformat)
        outImg = outImg.rgbSwapped()
        return outImg

    def center_window(self):
       qtRectangle = self.frameGeometry()
       centerPoint = QDesktopWidget().availableGeometry().center()
       qtRectangle.moveCenter(centerPoint)
       self.move(qtRectangle.topLeft())

    # Select camera
    @QtCore.pyqtSlot()
    def select_camera(self, last_index):
        number = 0
        hint = "Select a camera (0 to " + str(last_index) + "): "
        try:
            number = int(input(hint))
        except Exception:
            print("It's not a number!")
            return self.select_camera(last_index)

        if number > last_index:
            print("Invalid number! Retry!")
            return self.select_camera(last_index)
        return number

    # Start processing
    @QtCore.pyqtSlot()
    def startProcess(self):
        if self.running == True:
            self.timer.stop()
            for cap in self.inCap:
                cap.release()
            for cap in self.outCap:
                cap.release()
            self.running = False
        if self.running == False:
            self.fps = self.inCap[0].get(cv2.CAP_PROP_FPS)
            #self.fps = 1
            self.frameNo = 0

        if not self.inCap[0].read()[0]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('Please add a proper video source!')
            msg.setWindowTitle("Error")
            msg.exec_()
        else:
            self.running = True
            self.log_tabwidget.setTabEnabled(1, False);
            self.timer.start(1000.0 / self.fps)

            # Clear all variables and tabs
            self.backFrame = []
            self.width = []
            self.height = []

            # Heatmap
            self.heatmap = []

            # Dwell time
            self.inDwell = []
            self.outDwell = []

            self.customer_list.clear()
            self.recommend_list.clear()

            self.inDetectors = []
            for cap in self.inCap:
                self.inDetectors.append(Detectracker())
                ret, backFrame = cap.read()
                self.backFrame.append(cv2.cvtColor(backFrame, cv2.COLOR_RGB2BGR))
                height, width, depth = backFrame.shape

                self.width.append(width)
                self.height.append(height)
                self.heatmap.append(Heatmap(width, height))
                self.inDwell.append(Dwell(self.fps))

            self.outDetectors = []
            for cap in self.outCap:
                self.outDetectors.append(Detectracker())
                self.outDwell.append(Dwell(self.fps))

            self.statusBar.showMessage("Running...")

    # Process frame
    def nextFrameSlot(self):
        inFrame = []
        outFrame = []

        for cap in self.inCap:
            ret, frame = cap.read()
            inFrame.append(frame)

        for cap in self.outCap:
            ret, frame = cap.read()
            outFrame.append(frame)

        if any(x is None for x in inFrame) or any(x is None for x in outFrame):
            self.timer.stop()
            for cap in self.inCap:
                cap.release()
            for cap in self.outCap:
                cap.release()
            self.statusBar.showMessage("Video ended...")
            self.running = False
            self.frameNo = 0

            customer_data = []
            for i in range(len(self.inCap)):
                customer_data.append(self.inDwell[i].get_log_data())
            self.writeLog(customer_data, 1)

            customer_data = []
            for i in range(len(self.outCap)):
                customer_data.append(self.outDwell[i].get_log_data())
            self.writeLog(customer_data, 2)
            self.log_tabwidget.setTabEnabled(1, True)
        else:
            self.frameNo += 1
            inImg = []
            for i in range(len(inFrame)):
                # Set maximum of width and height
                wmax = self.heatmap[i].width
                hmax = self.heatmap[i].height

                frame = inFrame[i]
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                #frame = cv2.resize(frame, (self.width, self.height))
                temp_frame = frame.copy()

                tracker, detections = self.inDetectors[i].getTrackDetections(frame)
                agender = self.gender.getAgeGenderFace(frame)

                # Update heatmap
                #if (self.frameNo % int(self.fps) == 0 or self.frameNo == 1):
                track_list = []
                track_dwell_list = []
                for ii in range(len(tracker.tracks)):
                    track = tracker.tracks[ii]
                    bbox = track.to_tlbr()
                    x, y = int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2)
                    if x >= wmax:
                        x = wmax - 1
                    if x < 0:
                        x = 0
                    if y >= hmax:
                        y = hmax - 1
                    if y < 0:
                        y = 0

                    ind = track.track_id
                    track_list.append([ind, x, y])

                    a, b, c, d = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                    if a >= wmax:
                        a = wmax - 1
                    if a < 0:
                        a = 0
                    if c >= wmax:
                        c = wmax - 1
                    if c < 0:
                        c = 0
                    if b >= hmax:
                        b = hmax - 1
                    if b < 0:
                        b = 0
                    if d >= hmax:
                        d = hmax - 1
                    if d < 0:
                        d = 0
                    track_dwell_list.append([ind, [a, b, c, d], [x, y]])

                self.inDwell[i].update_dwell(temp_frame, track_dwell_list, agender, self.frameNo)
                self.heatmap[i].update_heatmap(track_list)

                # Get heatmap
                heatmap = self.heatmap[i].get_curHeatmap()

                # Draw heatmap
                heatmapshow = None
                heatmapshow = cv2.normalize(heatmap, heatmapshow, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                heatmapshow = cv2.applyColorMap(heatmapshow, cv2.COLORMAP_JET)
                heatmapshow = cv2.cvtColor(heatmapshow, cv2.COLOR_RGB2BGR)

                # Draw rectangles and texts
                for track in tracker.tracks:
                    if not track.is_confirmed() or track.time_since_update > 1:
                    #if not track.is_confirmed():
                    #if track.time_since_update > 1:
                        continue
                    bbox = track.to_tlbr()
                    cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 255, 255), 2)
                    #cv2.putText(frame, str(track.track_id), (int(bbox[0]), int(bbox[1])), 0, 2, (0, 255, 0), 4)

                for det in detections:
                    bbox = det.to_tlbr()
                    #cv2.rectangle(frame,(int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 0, 0), 2)

                # Draw age and gender
                if len(agender) > 0:
                    for res in agender:
                        label = "{},{}".format(res[1], res[0])
                        cv2.rectangle(frame, (res[2][0], res[2][1]), (res[2][2], res[2][3]), (0, 255, 0), 2)
                        cv2.putText(frame, label, (res[2][0], res[2][1]-10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4, cv2.LINE_AA)

                for ii in range(len(self.shelve_list_list[i])):
                    shelve_list = self.shelve_list_list[i]
                    rect = shelve_list[ii]
                    cv2.rectangle(frame, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])), (0, 255, 0), 2)
                    cv2.putText(frame, "Shelf" + str(ii), (int(rect[0]), int(rect[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Report monitor result
                customer_data = self.inDwell[i].get_data()

                if i == 0:
                    self.updateCustomerList(customer_data, 1)
                else:
                    self.updateCustomerList(customer_data, 2)

                # Draw tracks
                for mmm in range(len(customer_data)):
                #for data in customer_data:
                    data = customer_data[mmm]
                    ind = data[0]
                    pos = data[5]
                    if len(pos) > 1:
                        cv2.polylines(frame, [np.int32(pos)], False, self.color[mmm % 13], 2)

                result_overlay = cv2.addWeighted(frame, 0.7, heatmapshow, 0.7, 0)
                inImg.append(result_overlay)

            outImg = []
            for i in range(len(outFrame)):
                frame = outFrame[i]
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                #frame = cv2.resize(frame, (self.width, self.height))
                temp_frame = frame.copy()

                tracker, detections = self.outDetectors[i].getTrackDetections(frame)
                agender = self.gender.getAgeGenderFace(frame)

                # Update heatmap
                #if (self.frameNo % int(self.fps) == 0 or self.frameNo == 1):
                track_list = []
                track_dwell_list = []
                for ii in range(len(tracker.tracks)):
                    track = tracker.tracks[ii]
                    bbox = track.to_tlbr()
                    x = int((bbox[0] + bbox[2]) / 2)
                    y = int((bbox[1] + bbox[3]) / 2)
                    ind = track.track_id
                    track_list.append([ind, x, y])

                    #face = temp_frame[int(bbox[1]) : int(bbox[3]), int(bbox[0]) : int(bbox[2]), :]
                    #track_dwell_list.append([ind, face, [x, y]])
                    track_dwell_list.append([ind, [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])], [x, y]])

                self.outDwell[i].update_dwell(temp_frame, track_dwell_list, agender, self.frameNo)

                # Draw rectangles and texts
                for track in tracker.tracks:
                    if not track.is_confirmed() or track.time_since_update > 1:
                        continue
                    bbox = track.to_tlbr()
                    cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 255, 255), 2)
                    cv2.putText(frame, str(track.track_id), (int(bbox[0]), int(bbox[1])), 0, 2, (0, 255, 0), 2)

                for det in detections:
                    bbox = det.to_tlbr()
                    cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 0, 0), 2)

                # Draw age and gender
                if len(agender) > 0:
                    for res in agender:
                        label = "{},{}".format(res[1], res[0])
                        cv2.rectangle(frame, (res[2][0], res[2][1]), (res[2][2], res[2][3]), (0, 255, 0), 2)
                        cv2.putText(frame, label, (res[2][0], res[2][1]-10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 2, cv2.LINE_AA)

                # Report monitor result
                customer_data = self.outDwell[i].get_data()
                self.updateCustomerList(customer_data, 2)

                for mmm in range(len(customer_data)):
                #for data in customer_data:
                    data = customer_data[mmm]
                    ind = data[0]
                    pos = data[5]
                    if len(pos) > 1:
                        cv2.polylines(frame, [np.int32(pos)], False, self.color[mmm % 13], 2)

                outImg.append(frame)

            if len(inImg) < 6:
                for i in range(6 - len(inImg)):
                    #inImg.append(inImg[0])
                    inImg.append(np.zeros((self.height[0], self.width[0], 3), np.uint8))
            if len(outImg) < 3:
                for i in range(3 - len(outImg)):
                    #outImg.append(outImg[0])
                    outImg.append(np.zeros((self.height[0], self.width[0], 3), np.uint8))

            w = int(self.live_preview.frameGeometry().width() / 3.0)
            h = int(self.live_preview.frameGeometry().height() / 3.0)

            for i in range(len(inImg)):
                inImg[i] = cv2.resize(inImg[i], (w, h))
            for i in range(len(outImg)):
                outImg[i] = cv2.resize(outImg[i], (w, h))

            vis1 = np.concatenate((np.concatenate((inImg[0], inImg[1]), axis = 1), inImg[2]), axis = 1)
            vis2 = np.concatenate((np.concatenate((inImg[3], inImg[4]), axis = 1), inImg[5]), axis = 1)
            vis3 = np.concatenate((np.concatenate((outImg[0], outImg[1]), axis = 1), outImg[2]), axis = 1)
            vis = np.concatenate((np.concatenate((vis1, vis2), axis = 0), vis3), axis = 0)

            vis = cv2.resize(vis, (int(vis.shape[1] / 4) * 4, int(vis.shape[0] / 4) * 4))

            # Draw grids
            cv2.line(vis, (0, h), (3 * w, h), (0, 0, 0), 3)
            cv2.line(vis, (0, 2 * h), (3 * w, 2 * h), (0, 0, 0), 3)
            cv2.line(vis, (w, 0), (w, 3 * h), (0, 0, 0), 3)
            cv2.line(vis, (2 * w, 0), (2 * w, 3 * h), (0, 0, 0), 3)

            #img = QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
            img = QImage(vis, vis.shape[1], vis.shape[0], QtGui.QImage.Format_RGB888)
            pix = QPixmap.fromImage(img)
            self.live_preview.setPixmap(pix)

    # Pause process
    @QtCore.pyqtSlot()
    def pauseProcess(self):
        if self.running == True:
            if self.btnPause.text() == "Pause":
                self.timer.stop()
                self.btnPause.setText("Resume")

                customer_data = []
                for i in range(len(self.inCap)):
                    customer_data.append(self.inDwell[i].get_log_data())
                self.writeLog(customer_data, 1)

                customer_data = []
                for i in range(len(self.outCap)):
                    customer_data.append(self.outDwell[i].get_log_data())
                self.writeLog(customer_data, 2)

                self.log_tabwidget.setTabEnabled(1, True);
                self.statusBar.showMessage("Paused...")
            else:
                self.btnPause.setText("Pause")
                self.log_tabwidget.setTabEnabled(1, False);
                self.timer.start()
                self.statusBar.showMessage("Running...")

    # Stop process
    @QtCore.pyqtSlot()
    def stopProcess(self):
        if self.running == True:
            self.timer.stop()

            for cap in self.inCap:
                cap.release()
            for cap in self.outCap:
                cap.release()

            self.statusBar.showMessage("Stopped...")
            self.running = False
            self.frameNo = 0

            # Clear video sources list
            self.listInsideSrc.clear()
            self.inCap = []

            # Clear video sources list
            self.listOutsideSrc.clear()
            self.outCap = []

            customer_data = []
            for i in range(len(self.inCap)):
                customer_data.append(self.inDwell[i].get_log_data())
            self.writeLog(customer_data, 1)

            customer_data = []
            for i in range(len(self.outCap)):
                customer_data.append(self.outDwell[i].get_log_data())
            self.writeLog(customer_data, 2)

            self.log_tabwidget.setTabEnabled(1, True);

    # Update custom list widget
    def updateCustomerList(self, customer_data, mode):
        if mode == 1:
            self.customer_list.clear()
        for data in customer_data:
            listWidget = CustomerItem()
            listWidget.setData(data)
            listWidgetItem = QtWidgets.QListWidgetItem(self.customer_list)
            listWidgetItem.setSizeHint(listWidget.sizeHint())
            self.customer_list.addItem(listWidgetItem)
            self.customer_list.setItemWidget(listWidgetItem, listWidget)

    # Write log file
    def writeLog(self, data_list_list, mode):
        # data = [self.id_list[i], self.start_list[i], self.end_list[i], self.dwell_list[i], self.face_list[i], pos, self.age_list[i], self.gender_list[i], self.time_list[i]]
        import csv
        if mode == 2:
            for i in range(len(data_list_list)):
                data_list = data_list_list[i]
                with open("data/logs/log_pos_outside_" + str(i) + ".csv", "w", newline = '') as csv_file:
                    writer = csv.writer(csv_file, delimiter = ',')
                    header = ["No", "ID", "Age", "Gender", "Start Time", "End Time", "Dwell Time", "Time", "Position"]
                    writer.writerow(header)
                    no = 1
                    for data in data_list:
                        for ii in range(len(data[5])):
                            if ii == 0:
                                line = [str(no), str(data[0]), data[6], data[7], \
                                        str(round(data[1], 2)), str(round(data[2], 2)), str(round(data[3], 2)), str(round(data[8][ii], 2)), str(data[5][ii][0]) + ":" + str(data[5][ii][1])]
                            else:
                                line = [" ", " ", " ", " ", \
                                        " ", " ", " ", str(round(data[8][ii], 2)), str(data[5][ii][0]) + ":" + str(data[5][ii][1])]
                            writer.writerow(line)
                        no += 1
        else:
            for i in range(len(data_list_list)):
                data_list = data_list_list[i]
                with open("data/logs/log_pos_inside_" + str(i) + ".csv", "w", newline = '') as csv_file:
                    writer = csv.writer(csv_file, delimiter = ',')
                    header = ["No", "ID", "Age", "Gender", "Start Time", "End Time", "Dwell Time", "Time", "Position"]
                    writer.writerow(header)
                    no = 1
                    for data in data_list:
                        for ii in range(len(data[5])):
                            if ii == 0:
                                line = [str(no), str(data[0]), data[6], data[7], \
                                        str(round(data[1], 2)), str(round(data[2], 2)), str(round(data[3], 2)), str(round(data[8][ii], 2)), str(data[5][ii][0]) + ":" + str(data[5][ii][1])]
                            else:
                                line = [" ", " ", " ", " ", \
                                        " ", " ", " ", str(round(data[8][ii], 2)), str(data[5][ii][0]) + ":" + str(data[5][ii][1])]
                            writer.writerow(line)
                        no += 1

                if len(self.shelve_list_list[i]) > 0:
                    with open("data/logs/log_shelve_inside_" + str(i) + ".csv", "w", newline = '') as csv_file:
                        writer = csv.writer(csv_file, delimiter = ',')
                        header = ["No", "ID", "Age", "Gender", "Start Time", "End Time", "Dwell Time", "Time", "Shelf"]
                        writer.writerow(header)
                        no = 1
                        for data in data_list:
                            for ii in range(len(data[5])):
                                shelve = self.find_shelve(self.shelve_list_list[i], data[5][ii])
                                if ii == 0:
                                    line = [str(no), str(data[0]), data[6], data[7], \
                                            str(round(data[1], 2)), str(round(data[2], 2)), str(round(data[3], 2)), str(round(data[8][ii], 2)), str(shelve)]
                                else:
                                    line = [" ", " ", " ", " ", \
                                            " ", " ", " ", str(round(data[8][ii], 2)), str(shelve)]
                                writer.writerow(line)
                            no += 1

    # Find nearest shelf
    def find_shelve(self, sh_list, pos):
        dist_list = []
        for i in range(len(sh_list)):
            x = (sh_list[i][0] + sh_list[i][2]) / 2
            y = (sh_list[i][1] + sh_list[i][3]) / 2
            dist_list.append((x - pos[0]) ** 2 + (y - pos[1]) ** 2)
        return dist_list.index(min(dist_list))

    # Add shelf
    @QtCore.pyqtSlot()
    def addShelve(self):
        self.setShelve = True
        self.timer.stop()
        self.statusBar.showMessage("Paused...")
        self.btnPause.setText("Resume")

        ind = self.listInsideSrc.currentRow()
        if ind == -1:
            ind = 0
        img = QImage(self.backFrame[ind], self.backFrame[ind].shape[1], self.backFrame[ind].shape[0], QtGui.QImage.Format_RGB888)
        shelve_list = self.shelve_list_list[ind]
        for i in range(len(shelve_list)):
            rect = shelve_list[i]
            cv2.rectangle(self.backFrame[ind], (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])), (0, 255, 0), 2)
            cv2.putText(self.backFrame[ind], "Shelf" + str(i), (int(rect[0]), int(rect[1])), 0, 5e-3 * 100, (0, 255, 0), 2)
        pix = QPixmap.fromImage(img)
        self.live_preview.setPixmap(pix)

    # Reset shelf
    @QtCore.pyqtSlot()
    def resetShelve(self):
        self.timer.stop()
        self.shelve_list_list = []
        for i in range(len(self.inCap)):
            self.shelve_list_list.append([])
        self.timer.start()

    def mousePressEvent(self, QMouseEvent):
        if self.setShelve == True:
            self.shelve1st = QMouseEvent.pos()

    def mouseReleaseEvent(self, QMouseEvent):
        if self.setShelve == True:
            #cursor = QtGui.QCursor()
            #print(cursor.pos())

            # Check the shelve position
            self.shelve2nd = QMouseEvent.pos()
            pos1 = self.shelve1st
            pos2 = self.shelve2nd
            pos3 = self.live_preview.geometry()

            if pos1.x() < pos3.x() or pos1.y() < pos3.y() or pos2.x() > pos3.x() + pos3.width() or pos2.y() > pos3.y() + pos3.height():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText('Failed to set a reasonable position of the shelf!')
                msg.setWindowTitle("Error")
                msg.exec_()
                return

            ind = self.listInsideSrc.currentRow()
            if ind == -1:
                ind = 0

            # Get position in image
            x1 = int(float(pos1.x() - pos3.x()) / float(pos3.width()) * self.width[ind])
            y1 = int(float(pos1.y() - pos3.y()) / float(pos3.height()) * self.height[ind])
            x2 = int(float(pos2.x() - pos3.x()) / float(pos3.width()) * self.width[ind])
            y2 = int(float(pos2.y() - pos3.y()) / float(pos3.height()) * self.height[ind])

            tempFrame = self.backFrame[ind].copy()
            img = QImage(tempFrame, self.backFrame[ind].shape[1], self.backFrame[ind].shape[0], QtGui.QImage.Format_RGB888)
            shelve_list = self.shelve_list_list[ind]
            for i in range(len(shelve_list)):
                rect = shelve_list[i]
                cv2.rectangle(tempFrame, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])), (0, 255, 0), 2)
                cv2.putText(tempFrame, "Shelf" + str(i), (int(rect[0]), int(rect[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.rectangle(tempFrame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            pix = QPixmap.fromImage(img)
            self.live_preview.setPixmap(pix)

            addS = QMessageBox()
            addS.setText("Do you want to add the shelf here?")
            addS.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            addS = addS.exec()

            if addS == QMessageBox.Yes:
                self.shelve_list_list[ind].append([x1, y1, x2, y2])
                self.setShelve = False
                self.timer.start()
                self.statusBar.showMessage("Running...")
                self.btnPause.setText("Pause")
            else:
                tempFrame1 = self.backFrame[ind].copy()
                img = QImage(tempFrame1, self.backFrame[ind].shape[1], self.backFrame[ind].shape[0], QtGui.QImage.Format_RGB888)
                shelve_list = self.shelve_list_list[ind]
                for i in range(len(shelve_list)):
                    rect = shelve_list[i]
                    cv2.rectangle(tempFrame1, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])), (0, 255, 0), 2)
                    cv2.putText(tempFrame1, "Shelf" + str(i), (int(rect[0]), int(rect[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                pix = QPixmap.fromImage(img)
                self.live_preview.setPixmap(pix)
                return
