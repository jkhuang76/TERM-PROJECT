import threading
import random
import aubio
import copy
import time
from cmu_112_graphics import *
from Surface import Surface
from GameObject import GameObject
from tkinter import *
from PIL import Image
import numpy as np
from numpy import median, diff

# cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html

class Spike(GameObject):
    image = Image.open("spike.png")
    def __init__(self, x, y, image, size):
        super().__init__(x,y,size)
        self.image = Spike.image.resize(size)
startTime = time.time()
class BeatCollector(object):
    
    def __init__(self, fileName, samplingRate):
        self.fft_size = 1024
        self.hop_size = self.fft_size//2 
        self.fileName = fileName
        self.delay = 4. * self.hop_size
        self.samplingRate = samplingRate
        self.beats = []
        self.volumes = []
        self.total_frames = 0
        self.platforms  = []
        self.obstacles = []
        self.goal = None
        self.defaultGap = 30
        self.bpm = self.beats_to_bpm()
        self.scrollSpeed = int((self.bpm/60) *10)
        self.height = 500
        self.spikeImage = Image.open('spike.png')

    def collectBeats(self): # collectBeats basic idea from https://github.com/aubio/aubio/tree/master/python/demos, tempo demo
        self.music_source = aubio.source(self.fileName, self.samplingRate, self.hop_size)
        self.music_tempo = aubio.tempo("default", self.fft_size, self.hop_size, self.samplingRate)
        while True: 
            samples, read = self.music_source()
            is_beat = self.music_tempo(samples)
            if (is_beat):
                this_beat = int(self.total_frames - self.delay + is_beat[0] * self.hop_size)
                time = (this_beat/float(self.samplingRate)) 
                time = round(time,3)
                volume = aubio.db_spl(aubio.fvec(is_beat)) # added volume component, sound pressure level in db
                self.beats.append(time)
                self.volumes.append(volume)
            self.total_frames += read
            if (read < self.hop_size):
                break
        return self.beats, self.volumes

    def beats_to_bpm(self): # bpm extract modeled off https://github.com/aubio/aubio/tree/master/python/demos   # demo_bpm_extract.py
        b_source = aubio.source(self.fileName, self.samplingRate, self.hop_size) # different source for bpm analysis 
        spec_tempo = aubio.tempo("specdiff", self.fft_size, self.hop_size, self.samplingRate)
        beats = []
        while True: 
            samples, read = b_source()
            is_beat = spec_tempo(samples)
            if (is_beat):
                this_beat = spec_tempo.get_last_s()
                beats.append(this_beat)
            if (read < self.hop_size):
                break
        if (len(beats) > 4):
            bpms = 60./diff(beats)# convert beats into periods 
            return median(bpms)

    def createPlatforms(self):
        beats, volumes = self.collectBeats()
        defaultY = 300
        groundHeight = 375
        for i in range(len(beats)):
            if (i == len(beats) - 1):
                beats[i] += beats[i-1] + 30
                self.platforms.append(Surface(beats[i], defaultY, 30, 10))
                self.goal = Goal(beats[i], defaultY, 50)
            elif (i == 0):
                beats[i] += 500 
                self.platforms.append(Surface(beats[i], defaultY, 30, 10))
            else: 
                platY = defaultY
                timeDif = beats[i+1] - beats[i]
                platWidth = round(timeDif * self.scrollSpeed,2) # how wide the platform is based on how fast the scrolling is and time dif
                spikeSize = int(platWidth * 2)
                beats[i] = round(beats[i-1] + platWidth) + self.defaultGap*2
                # add descending and ascending platforms
                if (volumes[i+1] > volumes[i]):
                    platY = self.platforms[i-1].y - 10
                elif(volumes[i+1] < volumes[i]):
                    platY = self.platforms[i-1].y + 10 
                if (platY >= groundHeight):
                    platY = self.platforms[i-1].y - 50 
                    self.obstacles.append(Spike(beats[i], platY - 35, Spike.image, (spikeSize,spikeHeight)))
                if (i %10 == 0 ):
                    spikeHeight = int(abs(volumes[i])* 10)
                    if spikeHeight > 50:
                        spikeHeight = 30
                    self.obstacles.append(Spike(beats[i], platY - 35, Spike.image, (spikeSize,spikeHeight)))
                self.platforms.append(Surface(beats[i], platY, platWidth, 10))

    
    def getPlatforms(self):
        return self.platforms
    def getGoal(self):
        return self.goal

class Goal(object):
    def __init__(self, x, y, r): 
        self.x = x 
        self.y = y 
        self.r = r
    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.r - app.scrollX, self.y - self.r, 
                               self.x + self.r - app.scrollX, self.y + self.r)
        return (x0,y0,x1,y1)

class LevelApp(App):
    def appStarted(self):
        beatCollector1 = BeatCollector("Another One Bites The Dust.wav", 48000)
        beatsTime = beatCollector1.collectBeats()
        beatCollector1.createPlatforms()
        self.platforms = beatCollector1.getPlatforms()         
        self.scrollSpeed = 5
        self.scrollX = 0 
    def timerFired(self):
        if (len(self.platforms) > 0):
            self.scrollX += self.scrollSpeed
    
    def redrawAll(self,canvas):
        for platform in self.platforms: 
            canvas.create_rectangle(platform.x - platform.width - self.scrollX, platform.y - platform.height, 
                                    platform.x + platform.width - self.scrollX, platform.y + platform.height)
        canvas.create_rectangle(self.width//2 - 20, self.height//2 - 20, 
                            self.width//2 + 20, self.height//2 + 20, fill = "blue" )




        
    
#level = LevelApp(width = 500, height = 500)




