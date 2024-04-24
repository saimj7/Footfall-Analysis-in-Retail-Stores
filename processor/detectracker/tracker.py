from __future__ import division, print_function, absolute_import

import os
from timeit import time
import warnings
import sys
import numpy as np
from PIL import Image
from processor.detectracker.yolo import YOLO

from processor.detectracker.deep_sort import preprocessing
from processor.detectracker.deep_sort import nn_matching
from processor.detectracker.deep_sort.detection import Detection
from processor.detectracker.deep_sort.tracker import Tracker
from processor.detectracker.tools import generate_detections as gdet
from processor.detectracker.deep_sort.detection import Detection as ddet
warnings.filterwarnings('ignore')

class Detectracker:

    def __init__(self):

        # Definition of the parameters
        self.max_cosine_distance = 0.3
        #self.max_cosine_distance = 30
        self.nn_budget = None
        self.nms_max_overlap = 1.0

        # deep_sort
        self.model_filename = 'processor/detectracker/model_data/mars-small128.pb'
        self.encoder = gdet.create_box_encoder(self.model_filename,batch_size=1)

        self.metric = nn_matching.NearestNeighborDistanceMetric("cosine", self.max_cosine_distance, self.nn_budget)
        self.tracker = Tracker(self.metric)
        self.yolo = YOLO()

    # Return processed tracks and detections
    def getTrackDetections(self, frame):
        # image = Image.fromarray(frame)
        image = Image.fromarray(frame[...,::-1]) #bgr to rgb
        boxs = self.yolo.detect_image(image)
        # print("box_num",len(boxs))
        features = self.encoder(frame,boxs)

        # score to 1.0 here).
        detections = [Detection(bbox, 1.0, feature) for bbox, feature in zip(boxs, features)]

        # Run non-maxima suppression.
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        indices = preprocessing.non_max_suppression(boxes, self.nms_max_overlap, scores)
        detections = [detections[i] for i in indices]

        # Call the tracker
        self.tracker.predict()
        self.tracker.update(detections)

        return self.tracker, detections
