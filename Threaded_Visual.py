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


def pyaudio_stream_thread(flagList):
    while(flagList[0]):
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
    def move(self,dx,dy):
        self.x += dx
        self.y += dy
    def __repr__(self):
        return f"Beat at {self.x}, {self.y} with radius {self.r}"

class Surface(object): #surfaces - "ground", platforms, rectangles
    def __init__(self, x, y, size, isRectangle):
        self.x = x 
        self.y = y 
        self.size = size 
        self.isRectangle = isRectangle
    def getBounds(self):
        if (self.isRectangle):
            (x0,y0,x1,y1) = (self.x - self.size, self.y - self.size//2, 
                               self.x + self.size, self.y + self.size//2)
        else: 
            (x0,y0,x1,y1) = (self.x - self.size, self.y - self.size, 
                            self.x + self.size, self.y + self.size)
        return (x0,y0,x1,y1)
    

class Player(object): # basic player class represented by square
    def __init__(self, x, y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.vx = 0
        self.vy = 5  #test of gravity
        self.isJumping = False
        self.accY = 8
    
    def changeVelocity(self, vx, vy): 
        self.vx = vx 
        self.vy = vy
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.size, self.y - self.size, 
                            self.x + self.size, self.y + self.size)
        return (x0,y0,x1,y1)

    def collidesWith(self,other,app):
        playerBounds = self.getBounds()
        otherBounds = other.getBounds()
        if (app.boundsIntersect(playerBounds, otherBounds)): 
            return True
        return False
    
            



class beatApp(App):
    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
    def __init__(self, width, height):
        super().__init__(width = width, height = height)
        self.pyaudioFlag = [False]
    def appStarted(self):
        self.pyaudioFlag = [True]
        self.beats = beats
        self.counter = 0 
        self.timerDelay = 100
        self.score = 0
        self.player = Player(50, self.height//2 -20, 20)
        self.ground = Surface(self.width//2, self.height*0.8, self.width//2, True)
    

     
    def timerFired(self):
        # go through beats and move them to the left
        self.counter += self.timerDelay
        for beat in self.beats: 
            beat.move(-10,0)
        self.clearScreen()
        #self.stopMomentum()
        #self.player.y += self.player.vy * self.counter # test of gravity

    def jump(self): #has to have time component
        if (self.player.isJumping):
            while (self.player.accY > 0): #inital upwards motion
                self.player.y += self.player.vy 
                self.player.accY -= 1 
            if (self.player.collidesWith(self.ground,self)):
                self.player.accY = 8 
                self.player.vy = 0

    def movePlayer(self,dx,dy):
        self.player.x += dx 
        self.player.y += dy
        if (self.player.collidesWith(self.ground,self)):
            self.player.x -= dx 
            self.player.y -= dy

    def stopMomentum(self):
        if (self.player.collidesWith(self.ground, self) and self.player.vy != 0):
            self.player.y = self.ground.y - self.player.size
            self.player.changeVelocity(0,0)
            

    def keyPressed(self,event):
        if (event.key == "Right"):
            self.movePlayer(+5,0)
        elif (event.key == "Left"):
            self.movePlayer(-5,0)
        elif (event.key == "Up"):
            self.player.isJumping = True
            self.jump()

            # "gravity", have to create floor and collisions to stop momentum

    def clearScreen(self): # gets rid of beats that are off the screen
        #tempBeats = copy.copy(beats) # creates lots of lists, how to do this more efficiently?
        newBeats = set()
        for beat in beats: 
            if (beat.x > 0):
                newBeats.add(beat)
        self.beats = newBeats
    
    def boundsIntersect(self, boundsA, boundsB):
        (ax0, ay0, ax1, ay1) = boundsA
        (bx0, by0, bx1, by1) = boundsB
        return ((ax1 >= bx0) and (bx1 >= ax0) and
                (ay1 >= by0) and (by1 >= ay0))

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
        canvas.create_rectangle(self.ground.x - self.ground.size, self.ground.y - self.ground.size//2, 
                               self.ground.x + self.ground.size, self.ground.y + self.ground.size//2, fill = "black")

        


def drawing_thread(name):
    global myApp 
    myApp = beatApp(width = 500, height = 500)


if __name__ == "__main__":
    

    threads = list()
    pyaudioStreamFlag = [True]
    streamThread = threading.Thread(target=pyaudio_stream_thread, args=(pyaudioStreamFlag,))
    threads.append(streamThread)
    streamThread.start()
    appThread = threading.Thread(target = drawing_thread, args=(1,))
    threads.append(appThread)
    appThread.start()
    pyaudioStreamFlag = [False]
    # how to synchronize threads? 
    
    