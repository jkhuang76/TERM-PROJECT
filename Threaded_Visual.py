import threading
import pyaudio 
import aubio
import random
import copy
import time
from cmu_112_graphics import *
from tkinter import *
import numpy as np

win_s = 1024                # fft size
hop_s = win_s // 2    


filename = "Another One Bites The Dust.wav"

samplerate = 48000

a_source = aubio.source(filename, samplerate, hop_s)
samplerate = a_source.samplerate

# create aubio tempo detection
a_tempo = aubio.tempo("default", win_s, hop_s, samplerate)

beats = [] # global variable, better way to share information between the two threads? 
def pyaudio_callback(_in_data, _frame_count, _time_info, _status):
    samples, read = a_source()
    is_beat = a_tempo(samples)
    if is_beat:
        beats.append((Beat(500, 200, 10))) # hard coded based on current canvas
    audiobuf = samples.tobytes()
    if read < hop_s:
        return (audiobuf, pyaudio.paComplete)
    return (audiobuf, pyaudio.paContinue)


def pyaudio_stream_thread(name):
    p = pyaudio.PyAudio()
    pyaudio_format = pyaudio.paFloat32
    frames_per_buffer = hop_s
    n_channels = 1
    stream = p.open(format=pyaudio_format, channels=n_channels, rate=samplerate,
            output=True, frames_per_buffer=frames_per_buffer,
            stream_callback=pyaudio_callback)

    stream.start_stream()

    while stream.is_active():
        time.sleep(0.1)
    stream.stop_stream()
    stream.close()
    p.terminate()

class Beat(object):
    #basic beat represented by a dot
    #should add more information regarding to volume, type of note
    def __init__(self,x,y,r):
        self.x = x 
        self.y = y 
        self.r = r 
    def move(self):
        self.x -= 10
    def __repr__(self):
        return f"Beat at {self.x}, {self.y} with radius {self.r}"

class Player(object): # basic player class represented by square
    def __init__(self, x, y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.vy = 0  #test of gravity
    def movePlayer(self,dx,dy):
        self.x += dx 
        self.y += dy

class beatApp(App):
    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
    def appStarted(self):
        self.beats = beats
        self.counter = 0 
        self.timerDelay = 100
        self.score = 0
        self.player = Player(50, self.height//2, 20)

     
    def timerFired(self):
        # go through beats and move them to the left
        self.counter += self.timerDelay
        for beat in self.beats: 
            beat.move()
        self.clearScreen()
        self.player.y += self.player.vy * self.counter # test of gravity

    def keyPressed(self,event):
        if (event.key == "Right"):
            self.player.movePlayer(+5,0)
        elif (event.key == "Left"):
            self.player.movePlayer(-5,0)
        elif (event.key == "Up"):
            self.player.movePlayer(0, +5)
            self.player.vy = 9.81/1000 # "gravity", have to create floor and collisions to stop momentum

    def clearScreen(self): # gets rid of beats that are off the screen
        tempBeats = copy.copy(beats) # creates lots of lists, how to do this more efficiently?
        newBeats = set()
        for beat in tempBeats: 
            if (beat.x > 0):
                newBeats.add(beat)
        self.beats = newBeats

    def mousePressed(self, event): # click to remove beat and tap along to the beat
        newBeats = set()
        for beat in self.beats: 
            if (event.x in range(80,120) and beatApp.distance(beat.x, beat.y, event.x, event.y) <= beat.r):
                beats.remove(beat)
                self.score += 5

        

    def redrawAll(self,canvas): # draw player nad beats
        canvas.create_line(100, 0, 100, self.height) #baseline
        for beat in self.beats: 
            
            canvas.create_oval(beat.x - beat.r, beat.y - beat.r, 
                                beat.x + beat.r, beat.y + beat.r)
        canvas.create_text(self.width//2, 30, text = f"Score: {self.score}", 
        font = "Solomon 16")
        canvas.create_rectangle(self.player.x - self.player.size, self.player.y - self.player.size, 
                            self.player.x + self.player.size, self.player.y + self.player.size)

        


def drawing_thread(name):
    myApp = beatApp(width = 500, height = 500)


if __name__ == "__main__":
    

    threads = list()
    streamThread = threading.Thread(target=pyaudio_stream_thread, args=(0,))
    threads.append(streamThread)
    streamThread.start()
    appThread = threading.Thread(target = drawing_thread, daemon = True, args=(1,))
    threads.append(appThread)
    appThread.start()
    streamThread.join()
    appThread.join()
    # how to synchronize threads? 
    
    