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
    p = pyaudio.PyAudio()
    pyaudio_format = pyaudio.paFloat32
    frames_per_buffer = hop_s
    n_channels = 1
    stream = p.open(format=pyaudio_format, channels=n_channels, rate=samplerate,
            output=True, frames_per_buffer=frames_per_buffer,
            stream_callback=pyaudio_callback)

    stream.start_stream()
    while flagList[0] and stream.is_active():
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
    def __init__(self, x, y, width, height):
        self.x = x 
        self.y = y 
        self.width = width
        self.height = height
    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.width - app.scrollX, self.y - self.height, 
                               self.x + self.width - app.scrollX, self.y + self.height)
        return (x0,y0,x1,y1)

class Ground(Surface):
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width , self.y - self.height, 
                               self.x + self.width, self.y + self.height)
        return (x0,y0,x1,y1)

class Player(object): # basic player class represented by square
    DEFAULT_VELOCITY = -5
    DEFAULT_SPEED = 10
    JUMP_ACCEL = 3
    def __init__(self, x, y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.vx = 0
        self.vy = Player.DEFAULT_VELOCITY  #test of gravity
        self.speed = Player.DEFAULT_SPEED
        self.isJumping = False
        self.isMoving = False
        self.isOnPlatform = False
    def changeVelocity(self, vx, vy): 
        self.vx = vx 
        self.vy = vy
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.size, self.y - self.size, 
                            self.x + self.size, self.y + self.size)
        return (x0,y0,x1,y1)

    def move(self):
        self.x += self.speed

    def collidesWith(self,other,app):
        playerBounds = self.getBounds()
        if (isinstance(other, Ground)):
            otherBounds = other.getBounds()
        else: 
            otherBounds = other.getBounds(app)
        if (app.boundsIntersect(playerBounds, otherBounds)): 
            return True
        return False
    def jump(self,app):
        self.y += self.vy *Player.JUMP_ACCEL #timestarted time ended to be added
        self.x += self.vx *Player.JUMP_ACCEL
        if (self.vy < 0):
            self.vy += 1
        else:
            self.vy = -Player.DEFAULT_VELOCITY
            self.vy -=1 
        if self.collidesWith(app.ground, app):
            self.isJumping = False 
            self.y = 250
            self.vy = Player.DEFAULT_VELOCITY

    
            



class beatApp(App):
    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
    def __init__(self, width, height):
        super().__init__(width = width, height = height)
        print("bye")
        self.pyaudioFlag[0] = False
    def appStarted(self):
        self.pyaudioFlag = [True]
        global streamThread
        streamThread = threading.Thread(target=pyaudio_stream_thread, args=(self.pyaudioFlag,))
        streamThread.start()
        threads.append(streamThread)
        self.beats = beats
        self.counter = 0 
        self.timerDelay = 100
        self.score = 0
        self.player = Player(self.width//2, self.height//2 -20, 20)
        self.scrollX = 0 
        self.ground = Ground(self.width//2, self.height*0.8, self.width//2, self.width//4)
        self.platform = Surface(500, 230, 60, 10)
    

     
    def timerFired(self):
        # go through beats and move them to the left
        self.counter += self.timerDelay
        for beat in self.beats: 
            beat.move(-10,0)
        if (self.player.isJumping == True):
            self.player.jump(self)
        
            
        self.scroll()
        self.onTop()
        self.clearScreen()
        #self.checkCollisions()

    def scroll(self):
        self.scrollX += 5

    def movePlayer(self,dx,dy):
        self.player.x += dx 
        self.player.y += dy
        if (self.player.collidesWith(self.ground   ,self)):
            self.player.x -= dx 
            self.player.y -= dy
    """         
    def checkCollisions(self):
        if (self.player.collidesWith(self.platform,self)):
            self.player.y = self.platform.y - self.platform.height - self.player.size
    """
    def onTop(self): # keep player on top of the platform 
        #right now the player can go through the platform when its just scrolling 
        (px0, py0, px1, py1)= self.platform.getBounds(self)
        (Px0, Py0, Px1, Py1) = playerBounds = self.player.getBounds()
        if (not self.boundsIntersect((px0, py0, px1, py1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= px0 and Px1 <= px1 and Py1 < py0): 
                self.player.isJumping = False
                self.player.isOnPlatform = True
                #self.player.y = self.platform.y - self.platform.height - self.player.size

    def keyPressed(self,event):
        if (event.key == "Right"):
            self.movePlayer(+5,0)
            self.player.isMoving = True 
            self.player.vx = 5
        elif (event.key == "Left"):
            self.movePlayer(-5,0)
            self.player.isMoving = True 
            self.player.vx = -5
        elif (event.key == "Up"):
            self.player.isJumping = True

    def keyReleased(self,event):
        if (event.key == "Right" or event.key == "Left"):
            self.player.isMoving = False 
            self.player.vx = 0

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
        # a little bit messed up by the scroll
        newBeats = set()
        for beat in self.beats: 
            if (event.x in range(80,120) and beatApp.distance(beat.x, beat.y, event.x, event.y) <= beat.r):
                beats.remove(beat)
                self.score += 5

        

    def redrawAll(self,canvas): # draw player nad beats
        canvas.create_line(100 - self.scrollX, 0, 100 - self.scrollX, self.height) #baseline
        for beat in self.beats: 
            
            canvas.create_oval(beat.x - beat.r - self.scrollX, beat.y - beat.r, 
                                beat.x + beat.r - self.scrollX, beat.y + beat.r)
        canvas.create_text(self.width//2, 30, text = f"Score: {self.score}", 
        font = "Solomon 16")
        canvas.create_rectangle(self.player.x - self.player.size , self.player.y - self.player.size , 
                            self.player.x + self.player.size , self.player.y + self.player.size )
        canvas.create_rectangle(self.ground.x - self.ground.width, self.ground.y - self.ground.height, 
                               self.ground.x + self.ground.width, self.ground.y + self.ground.height, fill = "black")
        canvas.create_oval(self.width//2 - self.scrollX, self.height//2, 
                            self.width//2 - 10 - self.scrollX, self.height//2 - 10, fill = 'red')
        canvas.create_rectangle(self.platform.x - self.platform.width - self.scrollX, self.platform.y - self.platform.height, 
                               self.platform.x + self.platform.width - self.scrollX, self.platform.y + self.platform.height)

        


def drawing_thread(name):
    myApp = beatApp(width = 500, height = 500)


if __name__ == "__main__":
    

    threads = list()
    
    appThread = threading.Thread(target = drawing_thread, args=(1,))
    threads.append(appThread)
    appThread.start()
    # how to synchronize threads? 
    
    