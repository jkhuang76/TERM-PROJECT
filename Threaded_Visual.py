import threading
import pyaudio 
import aubio
import random
import copy
import time
import os 
from cmu_112_graphics import *
from Surface import Surface
from GameObject import GameObject
from Portal import Portal, OnPortal, OffPortal
from Level_Generation import BeatCollector 
from Level_Generation import Coin
from tkinter import *
from PIL import Image
import numpy as np
from numpy import diff, median



# cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html

class AudioCollector(object):
    #moved pyaudio stuff into class
    def __init__(self):
        self.beats = []
        self.win_s = 1024                # fft size
        self.hop_s = self.win_s // 2    
        self.filename = "Another One Bites The Dust.wav"
        self.samplerate = 48000
        self.a_source = aubio.source(self.filename, self.samplerate, self.hop_s)
        self.samplerate = self.a_source.samplerate
        self.pyaudioFlag = [True]
        # create aubio tempo detection # 
        self.a_tempo = aubio.tempo("default", self.win_s, self.hop_s, self.samplerate)
        self.spec_tempo = aubio.tempo("specdiff", self.win_s, self.hop_s, self.samplerate) #spectral difference method
    # pyaudio callback and stream method from https://github.com/aubio/aubio/tree/master/python/demos
    # specifically tap_the_beat demo
    def pyaudio_callback(self,_in_data, _frame_count, _time_info, _status):
        samples, read = self.a_source()
        is_beat = self.a_tempo(samples)
        #if is_beat:
            #self.beats.append((Beat(500 + self.i * 30, 200, 10)))
             # hard coded based on current canvas
        audiobuf = samples.tobytes()
        if read < self.hop_s:
            return (audiobuf, pyaudio.paComplete)
        return (audiobuf, pyaudio.paContinue)


    def pyaudio_stream_thread(self,flagList):
        p = pyaudio.PyAudio()
        pyaudio_format = pyaudio.paFloat32
        frames_per_buffer = self.hop_s
        n_channels = 1
        stream = p.open(format=pyaudio_format, channels=n_channels, rate=self.samplerate,
                output=True, frames_per_buffer=frames_per_buffer,
                stream_callback=self.pyaudio_callback)

        stream.start_stream()
        while flagList[0] and not flagList[1] and stream.is_active():
            time.sleep(0.1)
        print("bye")
        stream.stop_stream()
        stream.close()
        p.terminate()
    
    def beats_to_bpm(self): # bpm extract modeled off https://github.com/aubio/aubio/tree/master/python/demos 
        b_source = aubio.source(self.filename, self.samplerate, self.hop_s) # different source for bpm analysis 
        while True:  # demo_bpm_extract.py
            samples, read = b_source()
            is_beat = self.spec_tempo(samples)
            if (is_beat):
                this_beat = self.spec_tempo.get_last_s()
                self.beats.append(this_beat)
            if (read < self.hop_s):
                break
        if (len(self.beats) > 4):
            bpms = 60./diff(self.beats)# convert beats into periods 
            return median(bpms)
    
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

class Button(GameObject):
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width//2 , self.y - self.height//2,
                        self.x + self.width//2 , self.y + self.height//2)
        return (x0,y0,x1,y1)

class Star(GameObject):
    colorImage = Image.open("StarB.png")
    outlineImage = Image.open("StarOutline.png")
    def __init__(self, x, y, image, size):
        super().__init__(x,y,size)
        self.image = image.resize(size)
    def draw(self, canvas):
        canvas.create_image(self.x, self.y, image = ImageTk.PhotoImage(self.image))
    def resize(self):
        self.image = self.image.resize(self.size)


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
        self.vy = 0 
        self.isJumping = False
        self.isMoving = False
        self.isOnPlatform = False
        self.isFalling = False
    def changeVelocity(self, vx, vy): 
        self.vx = vx 
        self.vy = vy
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.size, self.y - self.size, 
                            self.x + self.size, self.y + self.size)
        return (x0,y0,x1,y1)


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
    GRAVITY = 6
    Attempts = 1
    background = Image.open("bg-banner2.jpg")
    complete = Image.open("levelComplete2.png")
    complete = complete.resize((500,100))
    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
    
    
    def appStarted(mode):
        mode.pyaudioFlag = [True]
        mode.gameOver = False
        #mode.pyaudioFlag.append(mode.gameOver)
        global streamThread
        mode.audioTest = AudioCollector()
        mode.audioTest.pyaudioFlag.append(mode.gameOver) #has to use a different flag to properly restart 
        streamThread = threading.Thread(target=mode.audioTest.pyaudio_stream_thread, args=(mode.audioTest.pyaudioFlag,))
        streamThread.start()
        threads.append(streamThread)
        mode.beatCollector1 = BeatCollector("Another One Bites The Dust.wav", 48000)
        mode.bpm = mode.audioTest.beats_to_bpm()
        mode.scrollSpeed = int((mode.bpm/60) * 10)  # beats per second then multiplied based on timerDelay
        beatsTime = mode.beatCollector1.collectBeats()
        mode.beatCollector1.createPlatforms()
        mode.beatCollector1.createCoins()
        mode.goal = mode.beatCollector1.getGoal()
        mode.goalCounter = 0
        mode.platforms = mode.beatCollector1.getPlatforms() 
        mode.obstacles = mode.beatCollector1.obstacles
        mode.beatCollector1.createJumps()
        mode.jumps = mode.beatCollector1.getJumps()
        mode.beatCollector1.createSpeedMode()
        mode.portals = mode.beatCollector1.getPortals()
        mode.blocks = mode.beatCollector1.blocks
        mode.collidedWithGoal = False
        mode.isHolding = False
        mode.keyCounter = 0
        mode.spikeImage = mode.loadImage("spike.png")
        mode.counter = 0 
        mode.timerDelay = 100
        mode.score = 0
        mode.coins = mode.beatCollector1.getCoins()
        mode.coinCount = 0
        mode.player = Player(mode.width//2, mode.height//2 -20, 20)
        mode.player2 = Player(mode.width//3, mode.height//2 -20, 20)
        mode.isSpeedMode = False
        mode.scrollX = 0 
        mode.isPaused = False
        mode.ground = Ground(mode.width//2, mode.height, mode.width//2, mode.width//4)
    def appStopped(mode):
        mode.pyaudioFlag[0] = False
        

    
    def restart(mode):
        mode.counter = 0
        mode.score = 0
        mode.collidedWithGoal = False
        mode.platforms = mode.beatCollector1.getPlatforms()
        mode.obstacles = mode.beatCollector1.obstacles
        mode.coins = mode.beatCollector1.getCoins()
        mode.portals = mode.beatCollector1.getPortals()
        mode.coinCount = 0
        mode.goalCounter = 0
        mode.gameOver = False
        mode.isSpeedMode = False
        mode.audioTest = AudioCollector()
        mode.audioTest.pyaudioFlag.append(mode.gameOver)
        global streamThread
        streamThread = threading.Thread(target=mode.audioTest.pyaudio_stream_thread, args=(mode.audioTest.pyaudioFlag,))
        streamThread.start()
        print(len(threads))
        mode.player.x, mode.player.y = mode.width//2, mode.height//2
        mode.player2.x, mode.player2.y = mode.width//3, mode.height//2
        mode.scrollX = 0 
        #mode.player = Player(mode.width//2, mode.height//2 -20, 20)
        GameMode.Attempts +=1 

    def resetObjects(mode):
        mode.obstacles = mode.beatCollector1.obstacles
        mode.platforms = mode.beatCollector1.getPlatforms()
        mode.coins = mode.beatCollector1.getCoins()
        mode.jumps = mode.beatCollector1.getJumps()

         
     
    def timerFired(mode): # future implementation to add, key held down 
        # go through beats and move them to the left
        if (mode.gameOver):
            return 
        if (mode.counter >= 3000 and mode.counter %1000 == 0):
            mode.score += 5            
        mode.counter += mode.timerDelay
        mode.update()
        mode.clearScreen()
        mode.checkCollisions(mode.player)
        #mode.checkCollisions(mode.player2)

    def update(mode):
        if (mode.goal.x - mode.goal.width - mode.scrollX >= 400 and mode.goal.x + mode.goal.width - mode.scrollX <= 500):
            if (mode.collidedWithGoal):
                mode.goalCounter += mode.timerDelay
                mode.goal.explode()
            mode.scrollX = mode.scrollX
        
        elif (mode.counter >= 3000):
            mode.scrollX += mode.scrollSpeed
        if (mode.goalCounter >= 2000):
            mode.gameOver = True
            mode.audioTest.pyaudioFlag[1] = True
            mode.audioTest.pyaudioFlag[0] = False
            mode.app.setActiveMode(mode.app.wonMode)
        if (mode.player.y - mode.player.size <= 0 ): # can't go up off the screen
            mode.player.y = mode.player.size
        if (mode.player2.y - mode.player2.size <= 0):
             mode.player2.y = mode.player2.size
        if (mode.player.vy > 0 ): 
            mode.player.vy += GameMode.GRAVITY 
            
            mode.player.isFalling = True
        elif (not mode.player.isOnPlatform and mode.player.vy <= 0):
            mode.player.vy -= -GameMode.GRAVITY 
            ## have to make sure can't go through when holding up key
            # add more conditions to case on previous state to current state 
        if (mode.player2.vy > 0):
            mode.player2.vy += GameMode.GRAVITY
        elif (not mode.player2.isOnPlatform and mode.player2.vy <= 0):
            mode.player2.vy -= -GameMode.GRAVITY 
        if (mode.isOnTopOfGround(mode.player)):
            if (not mode.player.isJumping):
                mode.player.isOnPlatform = True 
                mode.player.vy = 0
                mode.player.isFalling = False
            else: 
                mode.player.isFalling = True
                mode.player.isOnPlatform = False
        if (mode.isOnTopOfGround(mode.player2)):
            if (not mode.player2.isJumping):
                mode.player2.isOnPlatform = True 
                mode.player2.vy = 0
                mode.player2.isFalling = False
            else: 
                mode.player2.isFalling = True
                mode.player2.isOnPlatform = False
        for platform in mode.platforms:
            if (not mode.player.isJumping and (mode.isOnTopOfPlatform(platform,mode.player) or mode.isOnTopOfGround(mode.player))):
                mode.player.isOnPlatform = True 
                mode.player.vy = 0
                mode.player.isFalling = False
            else: 
                mode.player.isFalling = True
                mode.player.isOnPlatform = False
        for platform in mode.platforms:
            if (not mode.player2.isJumping and (mode.isOnTopOfPlatform(platform, mode.player2) or mode.isOnTopOfGround(mode.player2))):
                mode.player2.isOnPlatform = True 
                mode.player2.vy = 0
                mode.player2.isFalling = False
            else: 
                mode.player2.isFalling = True
                mode.player2.isOnPlatform = False

        mode.player.y += mode.player.vy 
        mode.player.x += mode.player.vx 
        mode.player2.y += mode.player2.vy 
        mode.player2.x += mode.player2.vx 
        mode.fallProperly(mode.player)
        mode.fallProperly(mode.player2)
    
    def fallProperly(mode,player):
        velocityReducer = 8
        for platform in mode.platforms:
            if (player.collidesWith(platform,mode)):
                if(player.vy > 20):
                    player.vy -= velocityReducer
                player.y -= player.vy  
        if (player.collidesWith(mode.ground, mode)):
            if(player.vy > 30):
                    player.vy -= velocityReducer
            player.y -= player.vy

    def movePlayer(mode,player,dx,dy):
        player.x += dx 
        player.y += dy
        if (player.collidesWith(mode.ground,mode)):
            player.x -= dx 
            player.y -= dy

    def changeSpeed(mode):
        GameMode.GRAVITY = 10
        mode.scrollSpeed *= 2
            
    def checkCollisions(mode,player):
        if (player.collidesWith(mode.goal,mode)):
            print(mode.collidedWithGoal)
            mode.collidedWithGoal = True
        for portal in mode.portals: 
            if (player.collidesWith(portal,mode)):
                if (isinstance(portal, OnPortal)):
                    portal.turnOnSpeed(mode)
                elif (isinstance(portal, OffPortal)):
                    portal.turnOffSpeed(mode)
        for platform in mode.platforms:
            if (player.collidesWith(platform,mode)):
                print(mode.player.x, mode.player.y)
                print(platform.y)
                mode.gameOver = True
                mode.audioTest.pyaudioFlag[0] = False
                mode.audioTest.pyaudioFlag[1] = True
                mode.restart()        
        for obstacle in mode.obstacles:
            if (player.collidesWith(obstacle,mode)):
               mode.gameOver = True
               mode.audioTest.pyaudioFlag[1] = True
               mode.audioTest.pyaudioFlag[0] = False
               mode.restart()     
        newCoins = set() 
        for coin in mode.coins: 
            if (player.collidesWith(coin,mode)):
                mode.coinCount += 1
            else:
                newCoins.add(coin)
        mode.coins = newCoins
        #for block in mode.blocks:
           # if (player.collidesWith(block,mode)):
               # mode.gameOver = True
                #mode.audioTest.pyaudioFlag[1] = True
                #mode.audioTest.pyaudioFlag[0] = False
                #mode.restart() 
        for jump in mode.jumps: 
            if (player.collidesWith(jump, mode)):
                player.vy = -50

    def isOnTopOfGround(mode,player): # keep player on top of the ground
        margin = mode.player.size//4
        (gx0, gy0, gx1, gy1)= mode.ground.getBounds()
        (Px0, Py0, Px1, Py1) = playerBounds = player.getBounds()
        if (not mode.boundsIntersect((gx0, gy0, gx1, gy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= gx0  and Px1 <= gx1 and Py1 <= gy0 and Py1 > gy0 - player.size): 
                return True
        return False

    def isOnTopOfPlatform(mode,platform,player): # keep player on top of the platform 
        (platx0, platy0, platx1, platy1)= platform.getBounds(mode)
        (Px0, Py0, Px1, Py1) = playerBounds = player.getBounds()
        if (not mode.boundsIntersect((platx0, platy0, platx1, platy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= platx0 - mode.player.size and Px1 <= platx1 + player.size and Py1 <= platy0 and Py1 > platy0 - player.size): 
                return True
        return False
    

    def keyPressed(mode,event):
        if (mode.gameOver or mode.counter < 3000):
            return 
        if (event.key == "d"):
            mode.movePlayer(mode.player2,+5,0)
            mode.player2.isMoving = True 
            mode.player2.vx = 5
        elif (event.key == "a"):
            mode.movePlayer(mode.player2,-5,0)
            mode.player2.isMoving = True 
            mode.player2.vx = -5
        elif (event.key == "w"):
            
            mode.keyCounter += mode.timerDelay
            if (mode.keyCounter >= 1000):
                mode.isHolding = True
            
            mode.player2.isJumping = True
            mode.player2.vy = -25      
        if (event.key == "Right"):
            mode.movePlayer(mode.player,+5,0)
            mode.player.isMoving = True 
            mode.player.vx = 5
        elif (event.key == "Left"):
            mode.movePlayer(mode.player,-5,0)
            mode.player.isMoving = True 
            mode.player.vx = -5
        elif (event.key == "Up"):
            
            mode.keyCounter += mode.timerDelay
            if (mode.keyCounter >= 1000):
                mode.isHolding = True
            
            mode.player.isJumping = True
            mode.player.vy = -25
            
        elif (event.key == "S"): # speed up scrolling to see rest of level
            mode.scrollX += 1000
        elif (event.key == "W"):
            mode.scrollX = mode.goal.x - 1000
        elif (event.key == "Escape"):
            mode.isPaused = True
            mode.audioTest.pyaudioFlag[0] = False
            mode.app.setActiveMode(mode.app.splashScreenMode)

    def keyReleased(mode,event):
        if (event.key == "d" or event.key == "a"):
            mode.player2.isMoving = False 
            mode.player2.vx = 0
        elif (event.key == "w"):
            mode.keyCounter = 0
            mode.isHolding = False
            mode.player2.isJumping = False
        if (event.key == "Right" or event.key == "Left"):
            mode.player.isMoving = False 
            mode.player.vx = 0
        elif (event.key == "Up"):
            mode.keyCounter = 0
            mode.isHolding = False
            mode.player.isJumping = False

            # "gravity", have to create floor and collisions to stop momentum

    def clearScreen(mode): # gets rid of beats that are off the screen
        #tempBeats = copy.copy(beats) # creates lots of lists, how to do this more efficiently?
        newPlatforms = set()
        beats = mode.audioTest.getBeats()
        newSpikes = set()
        for platform in mode.platforms:
            if (platform.x - mode.scrollX > 0):
                newPlatforms.add(platform)
        for obstacle in mode.obstacles:
            if (obstacle.x - mode.scrollX > 0):
                newSpikes.add(obstacle)
        mode.platforms = newPlatforms
        mode.obstacles = newSpikes
    
    #  from https://www.cs.cmu.edu/~112/notes/notes-animations-part2.html
    def boundsIntersect(mode, boundsA, boundsB):
        (ax0, ay0, ax1, ay1) = boundsA
        (bx0, by0, bx1, by1) = boundsB
        return ((ax1 >= bx0) and (bx1 >= ax0) and
                (ay1 >= by0) and (by1 >= ay0))


    def redrawAll(mode,canvas): # draw player and beats
        if (mode.isPaused):
            return
        canvas.create_line(100 - mode.scrollX, 0, 100 - mode.scrollX, mode.height) #baseline
        #countdown before game starts
        if (mode.counter == 1000):
            canvas.create_text(mode.width//2, mode.height//2, text = "3", font = "Solomon 30")
        elif (mode.counter == 2000):
            canvas.create_text(mode.width//2, mode.height//2, text = "2",font = "Solomon 30")
        elif (mode.counter == 3000):
            canvas.create_text(mode.width//2, mode.height//2, text = "1", font = "Solomon 30 ")

        canvas.create_text(mode.width//2, 30, text = f"Score: {mode.score}", 
        font = "Solomon 16")
        canvas.create_text(mode.width//2, 60, text = f"PlayerX: {mode.player.x + mode.scrollX}", 
        font = "Solomon 16")
        canvas.create_text(100, 50, text = f"Attempts: {GameMode.Attempts}", font = "Lato 16")
        canvas.create_rectangle(mode.player.x - mode.player.size , mode.player.y - mode.player.size , 
                            mode.player.x + mode.player.size , mode.player.y + mode.player.size )
        canvas.create_rectangle(mode.player2.x - mode.player2.size , mode.player2.y - mode.player2.size , 
                            mode.player2.x + mode.player2.size , mode.player2.y + mode.player2.size, fill = "red" )
        canvas.create_rectangle(mode.ground.x - mode.ground.width, mode.ground.y - mode.ground.height, 
                               mode.ground.x + mode.ground.width, mode.ground.y + mode.ground.height, fill = "black")
        for portal in mode.portals:
            if (portal.x - portal.width - mode.scrollX >= 0 and portal.x + portal.width - mode.scrollX <= 500):
                portal.draw(canvas,mode)
        if (mode.isSpeedMode):
            for block in mode.blocks:
                block.draw(canvas,mode)
                mode.platforms = []
                mode.obstacles = []
                mode.jumps = []
        else: 
            mode.resetObjects()
        
        for platform in mode.platforms: # draw only when seen on screen
            if (platform.x - platform.width - mode.scrollX >= 0 and platform.x + platform.width - mode.scrollX <= 500):
                #canvas.create_rectangle(platform.x - platform.width - mode.scrollX, platform.y - platform.height, 
                                   # platform.x + platform.width - mode.scrollX, platform.y + platform.height)
                canvas.create_image(platform.x - mode.scrollX, platform.y, image = ImageTk.PhotoImage(platform.image))
        canvas.create_rectangle(mode.goal.x - mode.goal.width - mode.scrollX, mode.goal.y - mode.goal.height, 
                                    mode.goal.x + mode.goal.width - mode.scrollX, mode.goal.y + mode.goal.height, fill = mode.goal.color)
        for obstacle in mode.obstacles:
            if (obstacle.x - obstacle.width - mode.scrollX >= 0 and obstacle.x + obstacle.width - mode.scrollX <= 500):
                obstacle.draw(canvas, mode)
        for jump in mode.jumps:
            if (jump.x - jump.width - mode.scrollX >= 0 and jump.x + jump.width - mode.scrollX <= 500):
                jump.draw(canvas,mode)
        for coin in mode.coins:
            if (coin.x - coin.width - mode.scrollX >= 0 and coin.x + coin.width - mode.scrollX <= 500):
                coin.draw(canvas,mode)
       
        for dot in mode.goal.dots:
            if (mode.collidedWithGoal):
                canvas.create_oval(dot.x - dot.r - mode.scrollX, dot.y - dot.r, 
                                    dot.x + dot.r - mode.scrollX, dot.y + dot.r, fill = dot.color)
        if (mode.collidedWithGoal):
            canvas.create_image(mode.width//2, mode.height//5, image = ImageTk.PhotoImage(GameMode.complete))


class SplashScreenMode(Mode):
    background = Image.open("background.png")
    title = Image.open("title2.png")
    play = Image.open("play.png")
    def appStarted(mode):
        SplashScreenMode.background = SplashScreenMode.background.resize((500,500))
        SplashScreenMode.title = SplashScreenMode.title.resize((400,100))
        mode.playButton = Button(mode.width//2, mode.height//2, SplashScreenMode.play.size)

    def redrawAll(mode,canvas): 
        canvas.create_image(mode.width//2,mode.height//2,image = ImageTk.PhotoImage(SplashScreenMode.background))
        canvas.create_image(mode.width//2,mode.height//10,image = ImageTk.PhotoImage(SplashScreenMode.title))
        canvas.create_image(mode.width//2,mode.height//2,image = ImageTk.PhotoImage(SplashScreenMode.play))

    def mouseInBounds(mode, eventx, eventy, bounds):
        # check mouse position is inside bounds
        (x0,y0,x1,y1) = bounds
        return (eventx >= x0 and eventx <= x1 and 
                eventy >= y0 and eventy <= y1)
    def mousePressed(mode,event):
        if (mode.mouseInBounds(event.x, event.y, mode.playButton.getBounds())):
            mode.app.gameMode.isPaused = False
            mode.app.appStarted()
            mode.app.setActiveMode(mode.app.gameMode)

# level select mode


class GameOverMode(Mode):
    def redrawAll(mode,canvas):
        canvas.create_text(mode.width//2, mode.height//2, text = "Game Over!", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height//2 + 20, text = "Press r to restart!", font = "Lato 16")
    def keyPressed(mode,event):
        if (event.key == "r"):
            mode.app.gameMode.appStarted()
            mode.app.setActiveMode(mode.app.splashScreenMode)
            

class WonMode(Mode):
    def modeActivated(mode):
        mode.highScore = mode.getScore("score.txt")
        mode.stars = [Star(mode.width//2 - 30, mode.height//2 + 100, Star.outlineImage, (30,30)),
                        Star(mode.width//2, mode.height//2 + 100, Star.outlineImage, (30,30)),
                        Star(mode.width//2 + 30, mode.height//2 + 100, Star.outlineImage, (30,30))]
        print("Coin Count" + str(mode.app.gameMode.coinCount))
        if (mode.app.gameMode.coinCount == 1):
            mode.stars[0].image = Star.colorImage
            mode.stars[0].resize()
        elif (mode.app.gameMode.coinCount == 2):
            mode.stars[0].image = Star.colorImage
            mode.stars[0].resize()
            mode.stars[1].image = Star.colorImage
            mode.stars[1].resize()
        elif (mode.app.gameMode.coinCount == 3):
            mode.stars[0].image = Star.colorImage
            mode.stars[1].resize()
            mode.stars[1].image = Star.colorImage
            mode.stars[1].resize()
            mode.stars[2].image = Star.colorImage
            mode.stars[2].resize()
        print(len(mode.stars))

    def redrawAll(mode,canvas):
        canvas.create_image(mode.width//2, mode.height//5, image = ImageTk.PhotoImage(GameMode.complete))
        canvas.create_text(mode.width//2, mode.height//2, text = "You Won!", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height//2 + 40, text = f"Score: {mode.app.gameMode.score}", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height//2 + 60, text = f"High Score: {mode.highScore}", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height//2 + 20, text = "Press r to restart!", font = "Lato 16")
        for star in mode.stars:
            star.draw(canvas)
    def resetScore(mode,path):
        with open(path, "wt") as file: 
            file.write("0")

    def keyPressed(mode,event):
        if (event.key == "r"):
            mode.updateScore("score.txt")        
            GameMode.Attempts = 1
            mode.app.setActiveMode(mode.app.splashScreenMode)


    # modeled after functions in https://www.cs.cmu.edu/~112/notes/notes-strings.html#basicFileIO
    def getScore(mode,path):
        with open(path) as file: 
            return file.read()
    def updateScore(mode, path):
        with open(path, "wt") as file: 
            currScore = (mode.app.gameMode.score)
            if (currScore > int(mode.highScore)):
                file.write(str(currScore))
        

class beatModalApp(ModalApp):
    #def __init__(self, width, height):
       # super().__init__(width = width, height = height)
        #self.gameMode.pyaudioFlag[0] = False
    def appStopped(self):
        self.gameMode.audioTest.pyaudioFlag[0] = False
        self.wonMode.resetScore("score.txt")
    def appStarted(self):
        self.gameMode = GameMode() 
        self.wonMode = WonMode()
        self.gameOverMode = GameOverMode()
        self.splashScreenMode = SplashScreenMode()
        self.setActiveMode(self.splashScreenMode)



def drawing_thread(name):
    myApp = beatModalApp(width = 500, height = 500)


if __name__ == "__main__":
    

    threads = list()
    appThread = threading.Thread(target = drawing_thread, args=(1,))
    threads.append(appThread)
    appThread.start()
     
    