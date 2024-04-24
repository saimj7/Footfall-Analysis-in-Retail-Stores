import numpy as np

class Heatmap:

    # Initialize heatmap
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cur_heatmap = np.zeros((self.height, self.width))
        self.cur_usermap = np.zeros((self.height, self.width))
        self.hist_heatmap = []
        self.hist_usermap = []
        self.hist_track = []
        
        self.dot_size = [int(self.width / 40), int(self.height / 40)]
        
    # Update heatmap using frame
    def update_heatmap(self, track):
        self.hist_track.append(track)
        for i in range(len(track)):
            self.cur_usermap = np.zeros((self.height, self.width))
            self.cur_usermap[track[i][2], track[i][1]] = track[i][0]
            self.hist_usermap.append(self.cur_usermap)
        
        if len(self.hist_heatmap) == 0:
            self.cur_heatmap = np.zeros((self.height, self.width))
            self.cur_heatmap[0][0] = 900
            for i in range(len(track)):
                x0 = track[i][1]
                y0 = track[i][2]
                for x in range(x0 - self.dot_size[0], x0 + self.dot_size[0]):
                    for y in range(y0 - self.dot_size[1], y0 + self.dot_size[1]):
                        if x >= 0 and x < self.width and y > 0 and y < self.height:
                            self.cur_heatmap[y, x] = 1
            # self.cur_heatmap = (self.cur_usermap > 0).astype(np.int)
            self.hist_heatmap.append(self.cur_heatmap)
        else:
            self.cur_heatmap = self.hist_heatmap[-1]
            # self.temp = (self.cur_usermap > 0).astype(np.int)
            self.temp = np.zeros((self.height, self.width))
            for i in range(len(track)):
                x0 = track[i][1]
                y0 = track[i][2]
                for x in range(x0 - self.dot_size[0], x0 + self.dot_size[0]):
                    for y in range(y0 - self.dot_size[1], y0 + self.dot_size[1]):
                        if x >= 0 and x < self.width and y > 0 and y < self.height:
                            self.temp[y, x] = 1
            prev_track = self.hist_track[-2]
            for i in range(len(track)):
                if self.cur_heatmap[track[i][2], track[i][1]] > 0:
                    x0 = track[i][1]
                    y0 = track[i][2]
                    for x in range(x0 - self.dot_size[0], x0 + self.dot_size[0]):
                        for y in range(y0 - self.dot_size[1], y0 + self.dot_size[1]):
                            if x >= 0 and x < self.width and y > 0 and y < self.height:
                                self.cur_heatmap[y, x] += 3
                            
                    #self.cur_heatmap[track[i][2], track[i][1]] += 3
                else:
                    x0 = track[i][1]
                    y0 = track[i][2]
                    for x in range(x0 - self.dot_size[0], x0 + self.dot_size[0]):
                        for y in range(y0 - self.dot_size[1], y0 + self.dot_size[1]):
                            if x >= 0 and x < self.width and y > 0 and y < self.height:
                                self.cur_heatmap[y, x] += 1
                                
                   #self.cur_heatmap[track[i][2], track[i][1]] += 1
            for i in range(len(prev_track)):
                if self.temp[prev_track[i][2], prev_track[i][1]] == 0 and \
                    self.cur_heatmap[prev_track[i][2], prev_track[i][1]] > 0:
                    x0 = prev_track[i][1]
                    y0 = prev_track[i][2]
                    for x in range(x0 - self.dot_size[0], x0 + self.dot_size[0]):
                        for y in range(y0 - self.dot_size[1], y0 + self.dot_size[1]):
                            if x >= 0 and x < self.width and y > 0 and y < self.height:
                                self.cur_heatmap[y, x] -= 2
                                if self.cur_heatmap[y, x] < 0:
                                    self.cur_heatmap[y, x]= 0
                                
                   #self.cur_heatmap[prev_track[i][2], prev_track[i][1]] -= 1
            self.hist_heatmap.append(self.cur_heatmap)
            
    def get_curHeatmap(self):
        return self.cur_heatmap       
    
    def get_histUsermap(self):
        return self.hist_usermap
