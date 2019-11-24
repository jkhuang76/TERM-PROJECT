import threading
import random
import aubio
import copy
import time
from cmu_112_graphics import *
from Surface import Surface
from tkinter import *
import numpy as np


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
        self.defaultGap = 30
        self.scrollSpeed = 50 
        self.height = 500

    def collectBeats(self):
        self.music_source = aubio.source(self.fileName, self.samplingRate, self.hop_size)
        self.music_tempo = aubio.tempo("default", self.fft_size, self.hop_size, self.samplingRate)
        while True: 
            samples, read = self.music_source()
            is_beat = self.music_tempo(samples)
            if (is_beat):
                this_beat = int(self.total_frames - self.delay + is_beat[0] * self.hop_size)
                time = (this_beat/float(self.samplingRate)) 
                time = round(time,3)
                volume = aubio.level_lin(aubio.fvec(is_beat))
                #elapsedTime = endTime - startTime  #python processes thing too fast
                self.beats.append(time)
                self.volumes.append(volume)
            self.total_frames += read
            if (read < self.hop_size):
                break
        return self.beats, self.volumes

    def createPlatforms(self):
        beats, volumes = self.collectBeats()
        defaultY = 250
        groundHeight = 375
        for i in range(len(beats)):
            if (i == len(beats) - 1):
                beats[i] += beats[i-1] + 30
                self.platforms.append(Surface(beats[i], defaultY, 30, 10))
            elif (i == 0):
                beats[i] += 500 
                self.platforms.append(Surface(beats[i], defaultY, 30, 10))
            else: 
                platY = defaultY
                timeDif = beats[i+1] - beats[i]
                platSize = round(timeDif * self.scrollSpeed,2)
                beats[i] = round(beats[i-1] + platSize) + self.defaultGap*2
                if (volumes[i+1] > volumes[i]):
                    platY = self.platforms[i-1].y - 10
                elif(volumes[i+1] < volumes[i]):
                    platY = self.platforms[i-1].y + 10 
                if (platY >= groundHeight):
                    platY = self.platforms[i-1].y - 50 
                self.platforms.append(Surface(beats[i], platY, platSize, 10))

            # add descending and ascending platforms
    
    def getPlatforms(self):
        return self.platforms

class Goal(object):
    def __init__(self, x, y, r): 
        self.x = x 
        self.y = y 
        self.r = r

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




