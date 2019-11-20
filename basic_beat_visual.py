import time
import pyaudio
import aubio
import numpy as np
from cmu_112_graphics import *
from tkinter import * 

startTime = time.time()
class BeatCollector(object):
    
    def __init__(self, fileName, samplingRate):
        self.fft_size = 1024
        self.hop_size = self.fft_size//2 
        self.fileName = fileName
        self.delay = 4. * self.hop_size
        self.samplingRate = samplingRate
        self.beats = []
        self.total_frames = 0

    def collectBeats(self):
        self.music_source = aubio.source(self.fileName, self.samplingRate, self.hop_size)
        self.music_tempo = aubio.tempo("default", self.fft_size, self.hop_size, self.samplingRate)
        while True: 
            samples, read = self.music_source()
            is_beat = self.music_tempo(samples)
            if (is_beat):
                this_beat = int(self.total_frames - self.delay + is_beat[0] * self.hop_size)
                time = (this_beat/float(self.samplingRate)) *1000
                time = round(time,3)
                #elapsedTime = endTime - startTime  #python processes thing too fast
                self.beats.append(time)
            self.total_frames += read
            if (read < self.hop_size):
                break
        return self.beats 

beatCollector1 = BeatCollector("88.wav", 44100)
beatsTime = beatCollector1.collectBeats()
print((beatsTime))

def pyaudio_callback(_in_data, _frame_count, _time_info, _status):
    samples, read = beatCollector1.music_source
    is_beat = beatCollector1.music_tempo(samples)
    if is_beat:
        
        samples += click
        #print ('tick') # avoid print in audio callback
    audiobuf = samples.tobytes()
    if read < hop_s:
        return (audiobuf, pyaudio.paComplete)
    return (audiobuf, pyaudio.paContinue)

class Beat(object):
    def __init__(self,x,y,r):
        self.x = x 
        self.y = y 
        self.r = r 


class beatApp(App):
    def appStarted(self, beatsTime):
        self.beatsTime = beatsTime
        self.beats = beat 
        self.counter = 0 

     
    def timerFired(self):
        # go through beats and draw stuff 
        counter += self.timerDelay
    
        pass 

    def redrawAll(self):
        pass




        
