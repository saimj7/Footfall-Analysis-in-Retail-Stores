import numpy as np

class Dwell:

    # Initialize heatmap
    def __init__(self, fps):
        
        # FPS
        self.fps = fps
        
        # ID list
        self.id_list = []
        
        # Start time list
        self.start_list = []
        
        # Start end list
        self.end_list = []
        
        # User face list
        self.face_list = []
        
        # User face position list
        self.face_pos_list = []
        
        # Dwell time list
        self.dwell_list = []
        
        # Position list
        self.pos_list = []
        
        # Age list
        self.age_list = []
        
        # Gender list
        self.gender_list = []
        
        # Time list
        self.time_list = []
        
    # Update Dwell
    def update_dwell(self, frame, track_list, agender, frameNo):
        if len(self.id_list) == 0:
            for i in range(len(track_list)):
                self.id_list.append(track_list[i][0])
                self.start_list.append(0)
                self.end_list.append(-1)
                face = frame[track_list[i][1][1] : track_list[i][1][3], track_list[i][1][0] : track_list[i][1][2], :]
                self.face_pos_list.append(track_list[i][1])
                self.face_list.append(face)
                self.dwell_list.append(-1)
                self.pos_list.append([track_list[i][2]])
                self.time_list.append([frameNo / self.fps])
                self.age_list.append("")
                self.gender_list.append("")
        else:
            track_id_list = []
            for i in range(len(track_list)):
                track_id_list.append(track_list[i][0])
            for i in range(len(self.id_list)):
                ind = self.id_list[i]
                if ind in track_id_list:
                    self.end_list[i] = -1
                    if track_list[track_id_list.index(ind)][2] != self.pos_list[i][-1]:
                        self.pos_list[i].append(track_list[track_id_list.index(ind)][2])
                        self.time_list[i].append(frameNo / self.fps)
                        self.face_pos_list[i] = track_list[track_id_list.index(ind)][1]
                else:
                    if self.end_list[i] == -1:
                        self.end_list[i] = 1.0 / self.fps * frameNo
                        self.dwell_list[i] = self.end_list[i] - self.start_list[i]
            for i in range(len(track_list)):
                mem = track_list[i]
                if mem[0] in self.id_list:
                    self.end_list[self.id_list.index(mem[0])] = -1
                    self.face_pos_list[self.id_list.index(mem[0])] = mem[1]
                    continue
                else:
                    self.id_list.append(mem[0])
                    self.start_list.append(1.0 / self.fps * frameNo)
                    self.end_list.append(-1)
                    face = frame[mem[1][1] : mem[1][3], mem[1][0] : mem[1][2], :]
                    self.face_list.append(face)
                    self.face_pos_list.append(mem[1])
                    self.dwell_list.append(-1)                     
                    self.pos_list.append([track_list[i][2]])
                    self.time_list.append([frameNo / self.fps])
                    self.age_list.append("")
                    self.gender_list.append("")
                    
        for data in agender:
            for i in range(len(self.id_list)):
                if self.age_list[i] != "":
                    continue
                if self.intersect_area(data[2], self.face_pos_list[i]) > 0.8 * np.abs(data[2][2] - data[2][0]) * np.abs(data[2][3] - data[2][1]):
                    self.age_list[i] = data[0]
                    self.gender_list[i] = data[1]
                    self.face_list[i] = frame[data[2][1] : data[2][3], data[2][0] : data[2][2], :]
                    continue
            
    # Get all data
    def get_data(self):
        data_list = []
        for i in range(len(self.id_list)):
            if self.end_list[i] == -1:
                pos = self.pos_list[i]
            else:
                pos = []
            data = [self.id_list[i], self.start_list[i], self.end_list[i], self.dwell_list[i], self.face_list[i], pos, self.age_list[i], self.gender_list[i]]
            data_list.append(data)
        return data_list
    
    # Get all data
    def get_log_data(self):
        data_list = []
        for i in range(len(self.id_list)):
            data = [self.id_list[i], self.start_list[i], self.end_list[i], self.dwell_list[i], self.face_list[i], self.pos_list[i], self.age_list[i], self.gender_list[i], self.time_list[i]]
            data_list.append(data)
        return data_list
    
    # Calculate intersect area
    def intersect_area(self, a, b):
        y = max(a[1], b[1])
        w = a[2] - a[0]
        
        if a[0] < b[0] or a[2] > b[2] or a[2] < b[0]:
            w = -1
        
        h = min(a[3], b[3]) - y
        if a[3] <= b[1]:
            h = -1
        if w <= 0 or h <= 0: return 0 # or (0,0,0,0) ?
        return w * h
