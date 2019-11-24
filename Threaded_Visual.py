import threading
import pyaudio 
import aubio
import random
import copy
import time
from cmu_112_graphics import *
from Surface import Surface
from level_generation import BeatCollector 
from tkinter import *
import numpy as np


# cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
win_s = 1024                # fft size
hop_s = win_s // 2    


filename = "Another One Bites The Dust.wav"

samplerate = 48000

a_source = aubio.source(filename, samplerate, hop_s)
samplerate = a_source.samplerate

# create aubio tempo detection
a_tempo = aubio.tempo("default", win_s, hop_s, samplerate)

class AudioCollector(object):
    #moved pyaudio stuff into class
    def __init__(self):
        self.beats = []
    # pyaudio callback and stream method from https://github.com/aubio/aubio/tree/master/python/demos
    # specifically tap_the_beat demo
    def pyaudio_callback(self,_in_data, _frame_count, _time_info, _status):
        samples, read = a_source()
        is_beat = a_tempo(samples)
        #if is_beat:
            #self.beats.append((Beat(500 + self.i * 30, 200, 10)))
             # hard coded based on current canvas
        audiobuf = samples.tobytes()
        if read < hop_s:
            return (audiobuf, pyaudio.paComplete)
        return (audiobuf, pyaudio.paContinue)


    def pyaudio_stream_thread(self,flagList):
        p = pyaudio.PyAudio()
        pyaudio_format = pyaudio.paFloat32
        frames_per_buffer = hop_s
        n_channels = 1
        stream = p.open(format=pyaudio_format, channels=n_channels, rate=samplerate,
                output=True, frames_per_buffer=frames_per_buffer,
                stream_callback=self.pyaudio_callback)

        stream.start_stream()
        while flagList[0] and not flagList[1] and stream.is_active():
            time.sleep(0.1)
        stream.stop_stream()
        stream.close()
        p.terminate()
    
    def getBeats(self):
        return self.beats

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



class Ground(Surface):
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width , self.y - self.height, 
                               self.x + self.width, self.y + self.height)
        return (x0,y0,x1,y1)

class Player(object): # basic player class represented by square
    def __init__(self, x, y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.vx = 0
        self.vy = 0 #test of gravity
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
    

    
            



class GameMode(Mode):
    GRAVITY = 3
    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
    
    def appStarted(mode):
        mode.pyaudioFlag = [True]
        mode.gameOver = False
        mode.pyaudioFlag.append(mode.gameOver)
        global streamThread
        mode.audioTest = AudioCollector()
        
        streamThread = threading.Thread(target=mode.audioTest.pyaudio_stream_thread, args=(mode.pyaudioFlag,))
        streamThread.start()
        threads.append(streamThread)
        beatCollector1 = BeatCollector("Another One Bites The Dust.wav", 48000)
        beatsTime = beatCollector1.collectBeats()
        beatCollector1.createPlatforms()
        mode.goal = beatCollector1.getGoal()
        mode.platforms = beatCollector1.getPlatforms() 
        mode.beats = mode.audioTest.getBeats()
        mode.counter = 0 
        mode.timerDelay = 100
        mode.score = 0
        mode.player = Player(mode.width//2, mode.height//2 -20, 20)
        mode.scrollX = 0 
        mode.ground = Ground(mode.width//2, mode.height, mode.width//2, mode.width//4)
        mode.platforms.insert(0,Surface(500, 230, 60, 10)) # initial test platform 
    

     
    def timerFired(mode):
        # go through beats and move them to the left
        if (mode.gameOver):
            return 
        mode.counter += mode.timerDelay
        #for beat in mode.beats: 
            #beat.move(-10,0)
        mode.update()
        mode.clearScreen()
        mode.checkCollisions()

    def update(mode):
        if (mode.counter >= 3000):
            mode.scrollX += 5
        if (mode.player.vy > 0): 
            mode.player.vy += GameMode.GRAVITY 
        elif (not mode.player.isOnPlatform and mode.player.vy <= 0):
            mode.player.vy -= -GameMode.GRAVITY 
            ## have to make sure can't go through when holding up key
        for platform in mode.platforms:
            if (not mode.player.isJumping and (mode.isOnTopOfPlatform(platform) or mode.isOnTopOfGround())):
                mode.player.isOnPlatform = True 
                mode.player.vy = 0
            else: 
                mode.player.isOnPlatform = False
        
        mode.player.y += mode.player.vy 
        mode.player.x += mode.player.vx 
    
    

    def movePlayer(mode,dx,dy):
        mode.player.x += dx 
        mode.player.y += dy
        if (mode.player.collidesWith(mode.ground,mode)):
            mode.player.x -= dx 
            mode.player.y -= dy
            
    def checkCollisions(mode):
        if (mode.player.collidesWith(mode.goal,mode)):
            mode.gameOver = True
            mode.pyaudioFlag[1] = True
            mode.app.setActiveMode(mode.app.wonMode)
        for platform in mode.platforms:
            if (mode.player.collidesWith(platform,mode)):
               mode.gameOver = True
               mode.pyaudioFlag[1] = True
               mode.app.setActiveMode(mode.app.gameOverMode)
        


    def isOnTopOfGround(mode): # keep player on top of the ground
        margin = mode.player.size//4
        (gx0, gy0, gx1, gy1)= mode.ground.getBounds()
        (Px0, Py0, Px1, Py1) = playerBounds = mode.player.getBounds()
        if (not mode.boundsIntersect((gx0, gy0, gx1, gy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= gx0  and Px1 <= gx1 and Py1 <= gy0 and Py1 > gy0 - mode.player.size - margin): 
                return True
        return False

    def isOnTopOfPlatform(mode,platform): # keep player on top of the platform 
        #right now the player can go through the platform when its just scrolling 
        (platx0, platy0, platx1, platy1)= platform.getBounds(mode)
        (Px0, Py0, Px1, Py1) = playerBounds = mode.player.getBounds()
        if (not mode.boundsIntersect((platx0, platy0, platx1, platy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= platx0 - mode.player.size and Px1 <= platx1 + mode.player.size and Py1 <= platy0 and Py1 > platy0 - mode.player.size): 
                return True
        return False

        

    def keyPressed(mode,event):
        if (mode.gameOver):
            return 
        if (event.key == "Right"):
            mode.movePlayer(+5,0)
            mode.player.isMoving = True 
            mode.player.vx = 5
        elif (event.key == "Left"):
            mode.movePlayer(-5,0)
            mode.player.isMoving = True 
            mode.player.vx = -5
        elif (event.key == "Up"):
            mode.player.isJumping = True
            mode.player.vy = -15
        elif (event.key == "S"): # speed up scrolling to see rest of level
            mode.scrollX += 1000

    def keyReleased(mode,event):
        if (event.key == "Right" or event.key == "Left"):
            mode.player.isMoving = False 
            mode.player.vx = 0
        elif (event.key == "Up"):
            mode.player.isJumping = False

            # "gravity", have to create floor and collisions to stop momentum

    def clearScreen(mode): # gets rid of beats that are off the screen
        #tempBeats = copy.copy(beats) # creates lots of lists, how to do this more efficiently?
        newBeats = set()
        newPlatforms = set()
        beats = mode.audioTest.getBeats()
        for beat in beats: 
            if (beat.x > 0):
                newBeats.add(beat)
        for platform in mode.platforms:
            if (platform.x - mode.scrollX > 0):
                newPlatforms.add(platform)
        mode.beats = newBeats
        mode.platforms = newPlatforms
    
    # cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part2.html
    def boundsIntersect(mode, boundsA, boundsB):
        (ax0, ay0, ax1, ay1) = boundsA
        (bx0, by0, bx1, by1) = boundsB
        return ((ax1 >= bx0) and (bx1 >= ax0) and
                (ay1 >= by0) and (by1 >= ay0))

    def mousePressed(mode, event): # click to remove beat and tap along to the beat
        # a little bit messed up by the scroll
        newBeats = set()
        for beat in mode.beats: 
            if (event.x in range(80,120) and GameMode.distance(beat.x, beat.y, event.x, event.y) <= beat.r):
                beats.remove(beat)
                mode.score += 5

        

    def redrawAll(mode,canvas): # draw player and beats
        canvas.create_line(100 - mode.scrollX, 0, 100 - mode.scrollX, mode.height) #baseline
        #countdown before game starts
        if (mode.counter == 1000):
            canvas.create_text(mode.width//2, mode.height//2, text = "3", font = "Solomon 30")
        elif (mode.counter == 2000):
            canvas.create_text(mode.width//2, mode.height//2, text = "2",font = "Solomon 30")
        elif (mode.counter == 3000):
            canvas.create_text(mode.width//2, mode.height//2, text = "1", font = "Solomon 30 ")

        for beat in mode.beats: 
            
            canvas.create_oval(beat.x - beat.r - mode.scrollX, beat.y - beat.r, 
                                beat.x + beat.r - mode.scrollX, beat.y + beat.r)
        canvas.create_text(mode.width//2, 30, text = f"Score: {mode.score}", 
        font = "Solomon 16")
        canvas.create_text(mode.width//2, 60, text = f"PlayerX: {mode.player.x + mode.scrollX}", 
        font = "Solomon 16")
        canvas.create_rectangle(mode.player.x - mode.player.size , mode.player.y - mode.player.size , 
                            mode.player.x + mode.player.size , mode.player.y + mode.player.size )
        canvas.create_rectangle(mode.ground.x - mode.ground.width, mode.ground.y - mode.ground.height, 
                               mode.ground.x + mode.ground.width, mode.ground.y + mode.ground.height, fill = "black")
        canvas.create_oval(mode.width//2 - mode.scrollX, mode.height//2, 
                            mode.width//2 - 10 - mode.scrollX, mode.height//2 - 10, fill = 'red')
        for platform in mode.platforms: 
            canvas.create_rectangle(platform.x - platform.width - mode.scrollX, platform.y - platform.height, 
                                platform.x + platform.width - mode.scrollX, platform.y + platform.height)
        canvas.create_oval(mode.goal.x - mode.goal.r - mode.scrollX, mode.goal.y - mode.goal.r ,
                        mode.goal.x + mode.goal.r - mode.scrollX, mode.goal.y + mode.goal.r , fill = "red")

class GameOverMode(Mode):
    def redrawAll(mode,canvas):
        canvas.create_text(mode.width//2, mode.height//2, text = "Game Over!", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height//2 + 20, text = "Press r to restart!", font = "Lato 16")
    def keyPressed(mode,event):
        if (event.key == "r"):
            mode.app.gameMode.appStarted()
            mode.app.setActiveMode(mode.app.gameMode)

class WonMode(Mode):
    def redrawAll(mode,canvas):
        canvas.create_text(mode.width//2, mode.height//2, text = "You Won!", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height//2 + 20, text = "Press r to restart!", font = "Lato 16")
    def keyPressed(mode,event):
        if (event.key == "r"):
            mode.app.gameMode.appStarted()
            mode.app.setActiveMode(mode.app.gameMode)
        

class beatModalApp(ModalApp):
    def __init__(self, width, height):
        super().__init__(width = width, height = height)
        self.gameMode.pyaudioFlag[0] = False
    def appStarted(self):
        self.gameMode = GameMode() 
        self.wonMode = WonMode()
        self.gameOverMode = GameOverMode()
        self.setActiveMode(self.gameMode)



def drawing_thread(name):
    myApp = beatModalApp(width = 500, height = 500)


if __name__ == "__main__":
    

    threads = list()
    
    appThread = threading.Thread(target = drawing_thread, args=(1,))
    threads.append(appThread)
    appThread.start()
     
    