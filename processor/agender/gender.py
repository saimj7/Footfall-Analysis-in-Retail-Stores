# Import required modules
import cv2 as cv
import math
import time
import argparse

class Agender:
    
    # Initialization
    def __init__(self):
        # Set model paths
        self.faceProto = "processor/agender/opencv_face_detector.pbtxt"
        self.faceModel = "processor/agender/opencv_face_detector_uint8.pb"
        
        self.ageProto = "processor/agender/model/deploy_age2.prototxt"
        self.ageModel = "processor/agender/model/age_net.caffemodel"
        
        self.genderProto = "processor/agender/model/deploy_gender2.prototxt"
        self.genderModel = "processor/agender/model/gender_net.caffemodel"
        
        self.MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
        self.ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        self.genderList = ['Male', 'Female']

        # Load network
        self.ageNet = cv.dnn.readNet(self.ageModel, self.ageProto)
        self.genderNet = cv.dnn.readNet(self.genderModel, self.genderProto)
        self.faceNet = cv.dnn.readNet(self.faceModel, self.faceProto)

    # Get face boxes
    def getFaceBox(self, net, frame, conf_threshold=0.7):
        frameOpencvDnn = frame.copy()
        frameHeight = frameOpencvDnn.shape[0]
        frameWidth = frameOpencvDnn.shape[1]
        blob = cv.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)
    
        net.setInput(blob)
        detections = net.forward()
        bboxes = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > conf_threshold:
                x1 = int(detections[0, 0, i, 3] * frameWidth)
                y1 = int(detections[0, 0, i, 4] * frameHeight)
                x2 = int(detections[0, 0, i, 5] * frameWidth)
                y2 = int(detections[0, 0, i, 6] * frameHeight)
                bboxes.append([x1, y1, x2, y2])
                cv.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight/150)), 8)
        return frameOpencvDnn, bboxes
    
    # Get age, gender and face region
    def getAgeGenderFace(self, frame):
        frameFace, bboxes = self.getFaceBox(self.faceNet, frame)
        padding = 20
        
        if not bboxes:
            return []

        result = []
        for bbox in bboxes:
            face = frame[max(0,bbox[1]-padding):min(bbox[3]+padding,frame.shape[0]-1),max(0,bbox[0]-padding):min(bbox[2]+padding, frame.shape[1]-1)]

            # Predict gender and confidence level    
            blob = cv.dnn.blobFromImage(face, 1.0, (227, 227), self.MODEL_MEAN_VALUES, swapRB=False)
            self.genderNet.setInput(blob)
            genderPreds = self.genderNet.forward()
            gender = self.genderList[genderPreds[0].argmax()]
    
            # Get age and confidence
            self.ageNet.setInput(blob)
            agePreds = self.ageNet.forward()
            age = self.ageList[agePreds[0].argmax()]
    
            result.append([age, gender, bbox])
        return result
