import threading
import pyaudio # module for audio playback https://people.csail.mit.edu/hubert/pyaudio/docs/
import aubio # module for audio file analysis, beat detection 
import random # python built in random module
import copy
import time # python time module for calculating time passed
import os # os module for reading in scores
from cmu_112_graphics import * # cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
from Surface import Surface
from GameObject import GameObject
from Portal import Portal, OnPortal, OffPortal
from Level_Generation import BeatCollector 
from Level_Generation import Coin
from tkinter import * #tkinter graphics module https://docs.python.org/3/library/tkinter.html#tkinter-modules
from PIL import Image # Pillow image manipulation https://pillow.readthedocs.io/en/stable/reference/Image.html
import numpy as np #numpy for some numerical operations
from numpy import diff, median # https://numpy.org/ 




class AudioCollector(object): #object for the pyaudio stream and bpm
    def __init__(self,filename, samplerate):
        self.beats = []
        self.win_s = 1024                # fft size
        self.hop_s = self.win_s // 2    
        self.filename = filename
        self.samplerate = samplerate
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
        audiobuf = samples.tobytes()
        # returning samples read to be played 
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
        stream.stop_stream()
        stream.close()
        p.terminate()
    
    def beats_to_bpm(self): # bpm extract modeled off https://github.com/aubio/aubio/tree/master/python/demos # demo_bpm_extract.py
        b_source = aubio.source(self.filename, self.samplerate, self.hop_s) # different source for bpm analysis 
        while True:  
            samples, read = b_source()
            is_beat = self.spec_tempo(samples)
            if (is_beat):
                this_beat = self.spec_tempo.get_last_s() #look at specific tempo of beat
                self.beats.append(this_beat)
            if (read < self.hop_s):
                break
        if (len(self.beats) > 4):
            bpms = 60./diff(self.beats)# convert beats into periods 
            return median(bpms)
    
    def getBeats(self):
        return self.beats


class Button(GameObject): #button does not have scroll
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width//2 , self.y - self.height//2,
                        self.x + self.width//2 , self.y + self.height//2)
        return (x0,y0,x1,y1)

class Star(GameObject):
    colorImage = Image.open("Images/StarB.png")
    outlineImage = Image.open("Images/StarOutline.png")
    def __init__(self, x, y, image, size):
        super().__init__(x,y,size)
        self.image = image.resize(size)
    def draw(self, canvas):
        canvas.create_image(self.x, self.y, image = ImageTk.PhotoImage(self.image))
    def resize(self):
        self.image = self.image.resize(self.size)


class Ground(Surface): #basic rectanlge
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width , self.y - self.height, 
                               self.x + self.width, self.y + self.height)
        return (x0,y0,x1,y1)

class Player(object): # player class with image and velocity attributes
    player1 = Image.open("Images/Player1.png")
    player2 = Image.open("Images/Player2.png")
    def __init__(self, x, y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.width, self.height = self.size[0], self.size[1]
        self.vx = 0
        self.vy = 0 
        self.isAlive = True
        self.isJumping = False
        self.isMoving = False
        self.isOnPlatform = False
        self.isFalling = False
        self.player1 = Player.player1.resize(self.size)
        self.player2 = Player.player2.resize(self.size)
    def changeVelocity(self, vx, vy): 
        self.vx = vx 
        self.vy = vy
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width//2, self.y - self.height//2, 
                            self.x + self.width//2, self.y + self.height//2)
        return (x0,y0,x1,y1)


    def collidesWith(self,other,app):
        playerBounds = self.getBounds()
        if (isinstance(other, Ground)):
            otherBounds = other.getBounds() #ground doesn't have scroll 
        else: 
            otherBounds = other.getBounds(app)
        if (app.boundsIntersect(playerBounds, otherBounds)): 
            return True
        return False
    

    
            

class GameMode(Mode): #main game mode
    GRAVITY = 7.5
    Attempts = 1 #keep attempting the level until complete
    background = Image.open("Images/bg-banner2.jpg")
    background = background.resize((500,500))
    complete = Image.open("Images/levelComplete2.png")
    complete = complete.resize((500,100))
    started = False
    count = 0 # count to keep track of whether app has been started yet
    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
    
    
    def appStarted(mode):
        GameMode.Attempts = 1
        GameMode.count += 1
        GameMode.started = True
        mode.modeSelected = LevelSelectMode.modeSelection
        mode.pyaudioFlag = [True] # mutable flag list to signal when the stream should stop
        mode.gameOver = False
        global streamThread
        #create object to play the pyaudio stream, each instance has its own source
        mode.audioPlayer = AudioCollector(mode.app.levelSelectMode.filename, int(mode.app.levelSelectMode.samplerate))
        mode.audioPlayer.pyaudioFlag.append(mode.gameOver) #has to use a different flag to properly restart 
        streamThread = threading.Thread(target=mode.audioPlayer.pyaudio_stream_thread, args=(mode.audioPlayer.pyaudioFlag,))
        threads.append(streamThread)
        mode.beatCollector1 = BeatCollector(mode.app.levelSelectMode.filename, int(mode.app.levelSelectMode.samplerate))
        mode.bpm = mode.audioPlayer.beats_to_bpm()
        mode.scrollSpeed = int((mode.bpm/60) * 10)  # beats per second then multiplied based on timerDelay
        mode.backgroundX, mode.backgroundY = mode.width//2, mode.height//2
        beatsTime = mode.beatCollector1.collectBeats()
        mode.beatCollector1.createPlatforms()
        mode.beatCollector1.createCoins()
        mode.goal = mode.beatCollector1.getGoal()
        mode.goal.generateDots()
        mode.goalCounter = 0
        mode.platforms = mode.beatCollector1.getPlatforms() 
        mode.obstacles = mode.beatCollector1.obstacles
        mode.beatCollector1.createJumps()
        mode.jumps = mode.beatCollector1.getJumps()
        mode.beatCollector1.createSpeedMode()
        mode.portals = mode.beatCollector1.getPortals()
        mode.blocks = mode.beatCollector1.blocks
        mode.collidedWithGoal = False
        mode.attemptCounter = 0 # time per attempt 
        mode.timeCounter = 0 #entire time played
        mode.timerDelay = 100
        mode.seconds = 0 
        mode.minutes = 0 
        mode.score = 0
        mode.coins = mode.beatCollector1.getCoins()
        mode.coinCount = 0
        mode.player = Player(mode.width//2, mode.height//2 -20, (40,40))
        if (mode.modeSelected == "multiplayer"):
            mode.player2 = Player(mode.width//3, mode.height//2 -20, (40,40))
        mode.isSpeedMode = False
        mode.scrollX = 0 
        mode.isPaused = False
        mode.ground = Ground(mode.width//2, mode.height, mode.width//2, mode.width//4)
    def appStopped(mode):
        mode.pyaudioFlag[0] = False

    def restart(mode):
        mode.attemptCounter = 0
        mode.score = 0
        mode.collidedWithGoal = False
        #don't need to recreate all the objects again
        mode.platforms = mode.beatCollector1.getPlatforms()
        mode.obstacles = mode.beatCollector1.obstacles
        mode.coins = mode.beatCollector1.getCoins()
        mode.portals = mode.beatCollector1.getPortals()
        mode.goal = mode.beatCollector1.getGoal()
        mode.goal.generateDots()
        mode.coinCount = 0
        mode.goalCounter = 0
        mode.gameOver = False
        mode.isPaused = False
        mode.isSpeedMode = False
        mode.audioPlayer = AudioCollector(mode.app.levelSelectMode.filename, int(mode.app.levelSelectMode.samplerate))
        mode.audioPlayer.pyaudioFlag.append(mode.gameOver)
        global streamThread
        streamThread = threading.Thread(target=mode.audioPlayer.pyaudio_stream_thread, args=(mode.audioPlayer.pyaudioFlag,))
        mode.player.x, mode.player.y = mode.width//2, mode.height//2
        if (mode.modeSelected == "multiplayer"): #spawn second player if it is multiplayer mode
            mode.player2.x, mode.player2.y = mode.width//3, mode.height//2
            mode.player2 = Player(mode.width//3, mode.height//2 -20, (40,40))
        mode.seconds = 0 
        mode.minutes = 0
        mode.scrollX = 0 
        mode.player = Player(mode.width//2, mode.height//2 -20, (40,40))
        GameMode.Attempts +=1 

    def modeDeactivated(mode):
        GameMode.count += 1 #has started at least one 

    def resetObjects(mode): #have to bring objects back after exiting portal 
        mode.obstacles = mode.beatCollector1.obstacles
        mode.platforms = mode.beatCollector1.getPlatforms()
        mode.jumps = mode.beatCollector1.getJumps()

         
     
    def timerFired(mode): #update positions of player and check for collisions
        if (mode.gameOver):
            return 
        if (mode.attemptCounter >= 3000 and mode.attemptCounter %1000 == 0):
            mode.score += 5         
        if (mode.attemptCounter == 3000):
            streamThread.start()

        mode.attemptCounter += mode.timerDelay #individual 
        mode.timeCounter += mode.timerDelay
        mode.update()
        if (mode.modeSelected == "multiplayer"):
            mode.updatePlayer2()
        mode.updateTime()
        mode.clearScreen()
        if (mode.player.isAlive):
            mode.checkCollisions(mode.player)
        if (mode.modeSelected == "multiplayer" and mode.player2.isAlive):  
            mode.checkCollisions(mode.player2)
    
    def updateTime(mode):
        mode.totalSeconds = mode.attemptCounter//1000
        mode.seconds = mode.totalSeconds - mode.minutes * 60
        if (mode.attemptCounter % 60000 == 0 ):
            mode.minutes += 1

        

    def update(mode):
        # check if reached goal
        if (mode.isSpeedMode):
            mode.player.vy = 0
            
        if (mode.goal.x - mode.goal.width - mode.scrollX >= mode.width//2 and mode.goal.x + mode.goal.width - mode.scrollX <= mode.width//2 + mode.goal.width *2+ mode.player.width//2):
            if (mode.collidedWithGoal):
                mode.goalCounter += mode.timerDelay
                mode.goal.explode() #little explode animation like confetti
            mode.scrollX = mode.scrollX
        
        elif (mode.attemptCounter >= 3000):
            mode.scrollX += mode.scrollSpeed
        if (mode.goalCounter >= 2000): # after collided for two seconds
            mode.gameOver = True
            mode.turnAudioOff()
            mode.app.setActiveMode(mode.app.wonMode)
        if (mode.player.y - mode.player.height <= 0 ): # can't go up off the screen
            mode.player.y = mode.player.height
        if (mode.player.vy > 0 ): 
            mode.player.vy += GameMode.GRAVITY 
            
            mode.player.isFalling = True
        
        elif (not mode.isSpeedMode and (not mode.player.isOnPlatform and mode.player.vy <= 0)):
            mode.player.vy -= -GameMode.GRAVITY 
        #gravity checks for ground and platforms for player 1
        if (mode.isOnTopOfGround(mode.player)):
            if (not mode.player.isJumping):
                mode.player.isOnPlatform = True 
                mode.player.vy = 0
                mode.player.isFalling = False
            else: 
                mode.player.isFalling = True
                mode.player.isOnPlatform = False
        
        for platform in mode.platforms:
            if (not mode.player.isJumping and (mode.isOnTopOfPlatform(platform,mode.player) or mode.isOnTopOfGround(mode.player))):
                mode.player.isOnPlatform = True 
                mode.player.vy = 0
                mode.player.isFalling = False
            else: 
                mode.player.isFalling = True
                mode.player.isOnPlatform = False
        

        mode.player.y += mode.player.vy 
        mode.player.x += mode.player.vx 
        
        mode.fallProperly(mode.player)

    def updatePlayer2(mode): #update function for player2
        if (mode.player2.y - mode.player2.height <= 0):
            mode.player2.y = mode.player2.height
        if (mode.isSpeedMode):
            mode.player2.vy = 0 
        if (mode.player2.vy > 0):
            mode.player2.vy += GameMode.GRAVITY
            mode.player2.isFalling = True
        elif (not mode.isSpeedMode and not mode.player2.isOnPlatform and mode.player2.vy <= 0):
            mode.player2.vy -= -GameMode.GRAVITY 
        if (mode.isOnTopOfGround(mode.player2)):
            if (not mode.player2.isJumping):
                mode.player2.isOnPlatform = True 
                mode.player2.vy = 0
                mode.player2.isFalling = False
            else: 
                mode.player2.isFalling = True
                mode.player2.isOnPlatform = False
        for platform in mode.platforms:
            if (not mode.player2.isJumping and (mode.isOnTopOfPlatform(platform, mode.player2) or mode.isOnTopOfGround(mode.player2))):
                mode.player2.isOnPlatform = True 
                mode.player2.vy = 0
                mode.player2.isFalling = False
            else: 
                mode.player2.isFalling = True
                mode.player2.isOnPlatform = False
        mode.player2.y += mode.player2.vy 
        mode.player2.x += mode.player2.vx 
        mode.fallProperly(mode.player2)

    
    def fallProperly(mode,player):
        #method to fall properly, when the player builds up velocity, they don't just collide with the platform
        #they can actually land on it properly
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
        if (mode.isSpeedMode):
            if (mode.player.x + mode.player.width//2 >= mode.width):
                mode.player.x = mode.width - mode.player.width//2
            elif (mode.player.x - mode.player.width//2 <= 0):
                mode.player.x = mode.player.width//2
            if (mode.modeSelected == "multiplayer" and mode.player2.x + mode.player2.width//2 >= mode.width):
                mode.player2.x = mode.width - mode.player2.width//2
            elif (mode.modeSelected == "multiplayer" and mode.player2.x - mode.player2.width//2 <= 0):
                mode.player2.x = mode.player2.width//2

    def turnAudioOff(mode):
        mode.audioPlayer.pyaudioFlag[0] = False
        mode.audioPlayer.pyaudioFlag[1] = True
            
    def checkCollisions(mode,player):
        if (player.collidesWith(mode.goal,mode)):
            mode.collidedWithGoal = True
        for portal in mode.portals: 
            if (player.collidesWith(portal,mode)):
                if (isinstance(portal, OnPortal)):
                    portal.turnOnSpeed(mode)
                elif (isinstance(portal, OffPortal)):
                    portal.turnOffSpeed(mode)
                    if (mode.modeSelected == "multiplayer"):
                        mode.player.x = mode.width//2
                        mode.player2.x = mode.width//3
                    else: 
                        mode.player.x = mode.width//2
        for platform in mode.platforms:
            if (player.collidesWith(platform,mode)):
                player.isAlive = False #die when you don't land on platform
        for obstacle in mode.obstacles: # or run into obstacle
            if (player.collidesWith(obstacle,mode)):
                player.isAlive = False
        for block in mode.blocks:
            if (player.collidesWith(block,mode)):
                player.isAlive = False
        #gameOver checks
        if (mode.modeSelected == "singleplayer" and not mode.player.isAlive ):
            mode.gameOver = True
            mode.turnAudioOff()
            mode.restart()        
        elif (mode.modeSelected == "multiplayer" and not mode.player.isAlive and not mode.player2.isAlive):
            mode.gameOver = True 
            mode.turnAudioOff()
            mode.restart()   
        
        newCoins = set()
        for coin in mode.coins: 
            if (player.collidesWith(coin,mode)):
                mode.coinCount += 1
                mode.score += 100
            else:
                newCoins.add(coin)
        mode.coins = newCoins
        
        for jump in mode.jumps: #launched when you touch a jump pad
            if (player.collidesWith(jump, mode)):
                player.vy = -50

    def isOnTopOfGround(mode,player): # keep player on top of the ground
        (gx0, gy0, gx1, gy1)= mode.ground.getBounds() 
        (Px0, Py0, Px1, Py1) = playerBounds = player.getBounds()
        if (not mode.boundsIntersect((gx0, gy0, gx1, gy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= gx0  and Px1 <= gx1 and Py1 <= gy0 and Py1 > gy0 - player.height//2): 
                return True
        return False

    def isOnTopOfPlatform(mode,platform,player): # keep player on top of the platform 
        (platx0, platy0, platx1, platy1)= platform.getBounds(mode) #different bounds because of scroll
        (Px0, Py0, Px1, Py1) = playerBounds = player.getBounds() 
        if (not mode.boundsIntersect((platx0, platy0, platx1, platy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= platx0 - mode.player.width and Px1 <= platx1 + player.width and Py1 <= platy0 and Py1 > platy0 - player.height//2): 
                return True
        return False
    

    def keyPressed(mode,event):
        if (mode.gameOver or mode.attemptCounter < 3000):
            return 
        # wasd for player 2
        if (mode.modeSelected == "multiplayer" and mode.player2.isAlive):
            if (event.key == "d" and mode.isSpeedMode):
                mode.movePlayer(mode.player2,+8,0)
                mode.player2.isMoving = True 
                mode.player2.vx = 8
            elif (event.key == "a" and mode.isSpeedMode):
                mode.movePlayer(mode.player2,-88,0)
                mode.player2.isMoving = True 
                mode.player2.vx = -8
            elif (event.key == "w"):
                
                if (mode.isSpeedMode):
                    mode.movePlayer(mode.player2, 0,-8)
                else:
                    mode.player.player2 = mode.player.player2.rotate(90)
                    mode.player2.isJumping = True
                    mode.player2.vy = -28    
            elif (event.key == "s"):
                if (mode.isSpeedMode):
                    mode.movePlayer(mode.player2, 0, 8)
        
        if (mode.player.isAlive):
            # arrow keys for player 1 
            if (event.key == "Right" and mode.isSpeedMode) :
                mode.movePlayer(mode.player,+8,0)
                mode.player.isMoving = True 
                mode.player.vx = 8
            elif (event.key == "Left" and mode.isSpeedMode):
                mode.movePlayer(mode.player,-8,0)
                mode.player.isMoving = True 
                mode.player.vx = -8
            
            if (event.key == "Up"):
                if (mode.isSpeedMode):
                    mode.movePlayer(mode.player,0,-8)
                else: 
                    mode.player.player1 = mode.player.player1.rotate(90)
                    mode.player.isJumping = True
                    mode.player.vy = -28
            elif (event.key == "Down"):
                if (mode.isSpeedMode):
                    mode.movePlayer(mode.player,0,8)
        ##Shortcut keys 
        if (event.key == "t"):
            mode.attemptCounter += 1000 #time speed up, for testing time trackers
        elif (event.key == "S"): # speed up scrolling to see rest of level
            mode.scrollX += 1000
        elif (event.key == "W"): #teleport to goal
            mode.scrollX = mode.goal.x - 1000
        elif (event.key == "P"): #on portal
            mode.scrollX = mode.portals[0].x - 500
        elif (event.key == "p"): # off portal
            mode.scrollX = mode.portals[1].x - 1000
        # back to main menu
        elif (event.key == "Escape"):
            mode.isPaused = True
            mode.audioPlayer.pyaudioFlag[0] = False
            mode.app.setActiveMode(mode.app.splashScreenMode)

    def keyReleased(mode,event):
        if (mode.modeSelected == "multiplayer"):
            if (event.key == "d" or event.key == "a"):
                mode.player2.isMoving = False 
                mode.player2.vx = 0
            elif (event.key == "w"):
                mode.player2.isJumping = False
        if (event.key == "Right" or event.key == "Left"):
            mode.player.isMoving = False 
            mode.player.vx = 0
        elif (event.key == "Up"):
            mode.player.isJumping = False

    def clearScreen(mode): # gets rid of objects off the screen 
        newPlatforms = set()
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
        canvas.create_image(mode.backgroundX, mode.height//2, image = ImageTk.PhotoImage(GameMode.background))
        #countdown before game starts
        if (mode.attemptCounter == 1000):
            canvas.create_text(mode.width//2, mode.height//2, text = "3", font = "Solomon 30")
        elif (mode.attemptCounter == 2000):
            canvas.create_text(mode.width//2, mode.height//2, text = "2",font = "Solomon 30")
        elif (mode.attemptCounter == 3000):
            canvas.create_text(mode.width//2, mode.height//2, text = "1", font = "Solomon 30 ")

        canvas.create_text(mode.width//2, 30, text = f"Score: {mode.score}", 
        font = "Solomon 16")
        canvas.create_text(100, 50, text = f"Attempts: {GameMode.Attempts}", font = "Lato 16")
        canvas.create_text(mode.width * 0.81, 30, text = f"Progress: {mode.minutes} Minutes", font = "Lato 10")
        canvas.create_text(mode.width * 0.86, 45, text = f"{mode.seconds} Seconds", font = "Lato 10")
        if (mode.player.isAlive):
            canvas.create_image(mode.player.x, mode.player.y,image = ImageTk.PhotoImage(mode.player.player1))
        if (mode.modeSelected == "multiplayer" and mode.player2.isAlive):
            canvas.create_image(mode.player2.x, mode.player2.y,image = ImageTk.PhotoImage(mode.player.player2))
        canvas.create_rectangle(mode.ground.x - mode.ground.width, mode.ground.y - mode.ground.height, 
                               mode.ground.x + mode.ground.width, mode.ground.y + mode.ground.height, fill = "black")
        for portal in mode.portals: # draw only when seen on screen
            if (portal.x - portal.width - mode.scrollX >= 0 and portal.x + portal.width - mode.scrollX <= 500):
                portal.draw(canvas,mode)
        if (mode.isSpeedMode):
            for block in mode.blocks:
                if (block.x - block.width - mode.scrollX >= 0 and block.x + block.width - mode.scrollX <= 500):
                    block.draw(canvas,mode)
                # disable the objects 
                mode.platforms = []
                mode.obstacles = []
                mode.jumps = []
        else: 
            mode.resetObjects()
        
        for platform in mode.platforms: # draw only when seen on screen
            if (platform.x - platform.width - mode.scrollX >= 0 and platform.x + platform.width - mode.scrollX <= 500):
                canvas.create_image(platform.x - mode.scrollX, platform.y, image = ImageTk.PhotoImage(platform.image))
        canvas.create_rectangle(mode.goal.x - mode.goal.width - mode.scrollX, mode.goal.y - mode.goal.height, 
                                    mode.goal.x + mode.goal.width - mode.scrollX, mode.goal.y + mode.goal.height, fill = mode.goal.color)
        for obstacle in mode.obstacles: # draw only when seen on screen
            if (obstacle.x - obstacle.width - mode.scrollX >= 0 and obstacle.x + obstacle.width - mode.scrollX <= 500):
                obstacle.draw(canvas, mode)
        for jump in mode.jumps: # draw only when seen on screen
            if (jump.x - jump.width - mode.scrollX >= 0 and jump.x + jump.width - mode.scrollX <= 500):
                jump.draw(canvas,mode)
        for coin in mode.coins:
            if (coin.x - coin.width - mode.scrollX >= 0 and coin.x + coin.width - mode.scrollX <= 500):
                coin.draw(canvas,mode)
       
        for dot in mode.goal.dots: #detection for "explosion animation" when level completed
            if (mode.collidedWithGoal):
                canvas.create_oval(dot.x - dot.r - mode.scrollX, dot.y - dot.r, 
                                    dot.x + dot.r - mode.scrollX, dot.y + dot.r, fill = dot.color)
        if (mode.collidedWithGoal):
            canvas.create_image(mode.width//2, mode.height//5, image = ImageTk.PhotoImage(GameMode.complete))


class SplashScreenMode(Mode):
    background = Image.open("Images/background.png")
    title = Image.open("Images/title2.png")
    play = Image.open("Images/play.png")
    level = Image.open("Images/level2.png")
    generator = Image.open("Images/generator2.png")
    def appStarted(mode):
        # creating buttons and images for splashscreen
        # buttons just rectangles for area to click in 
        SplashScreenMode.background = SplashScreenMode.background.resize((500,500))
        SplashScreenMode.title = SplashScreenMode.title.resize((450,100))
        mode.playButton = Button(mode.width//2, mode.height* (0.4), SplashScreenMode.play.size)
        SplashScreenMode.level = SplashScreenMode.level.resize((300,80))
        SplashScreenMode.generator = SplashScreenMode.generator.resize((450, 100))
        ButtonSize = (SplashScreenMode.generator.width, SplashScreenMode.level.height*1.5)
        mode.levelHeight = mode.height * (0.7)
        mode.generatorHeight = mode.height * (0.82)
        mode.helpHeight = mode.height * (0.95)
        mode.levelButton = Button(mode.width//2, (mode.levelHeight + mode.generatorHeight)/2, ButtonSize )#font size here)
        mode.helpButton = Button(mode.width//2, mode.helpHeight, (120,30))

    def redrawAll(mode,canvas): 
        canvas.create_image(mode.width//2,mode.height//2,image = ImageTk.PhotoImage(SplashScreenMode.background))
        canvas.create_image(mode.width//2,mode.height//10,image = ImageTk.PhotoImage(SplashScreenMode.title))
        canvas.create_image(mode.width//2,mode.height * (0.4),image = ImageTk.PhotoImage(SplashScreenMode.play))
        canvas.create_image(mode.width//2, mode.levelHeight, image = ImageTk.PhotoImage(SplashScreenMode.level))
        canvas.create_image(mode.width//2, mode.generatorHeight, image = ImageTk.PhotoImage(SplashScreenMode.generator))
        canvas.create_text(mode.width//2, mode.helpHeight, text = "Help", font = "Pusab 36", fill = "lawn green")
    @staticmethod
    def mouseInBounds( eventx, eventy, bounds):
        # check mouse position is inside bounds
        (x0,y0,x1,y1) = bounds
        return (eventx >= x0 and eventx <= x1 and 
                eventy >= y0 and eventy <= y1)
    def mousePressed(mode,event):
        if (SplashScreenMode.mouseInBounds(event.x, event.y, mode.playButton.getBounds())):
            if (LevelSelectMode.modeSelection != None):
                mode.app.gameMode.isPaused = False
                mode.app.gameMode.appStarted()
                mode.app.setActiveMode(mode.app.gameMode)
            else:
                mode.app.showMessage("Please generate a level first!")
        elif (SplashScreenMode.mouseInBounds(event.x, event.y, mode.levelButton.getBounds())):
            mode.app.setActiveMode(mode.app.levelSelectMode)
        elif (SplashScreenMode.mouseInBounds(event.x, event.y, mode.helpButton.getBounds())):
            mode.app.setActiveMode(mode.app.helpMode)

# help mode, general game instructions 
class HelpMode(Mode):
    def appStarted(mode):
        mode.cancelButton = Button(50,50,(60,60))
    def redrawAll(mode,canvas):
        canvas.create_image(mode.width//2,mode.height//2,image = ImageTk.PhotoImage(SplashScreenMode.background))
        canvas.create_image(50, 50, image = ImageTk.PhotoImage(LevelSelectMode.cancel))
        canvas.create_text(mode.width//2, 50, text = "Help", font = "Pusab 50", fill = "lawn green")
        helptext = """Welcome to Geometry Sprint!
Press the level generator button on the home screen 
and input a music file to start playing! 
Singleplayer Controls - Up Arrow to Jump
(All Arrow keys to move after going through portal)
Multiplayer - Player 2 W to Jump 
(WASD keys to move after going through portal)
Look out for Coins throughout the level to collect! 
Avoid the spikes and complete the level/song!
R to restart after winning
Escape to exit out of the level"""
        canvas.create_text(mode.width//2, mode.height//2, text = helptext, font = ("Open Sans Regular", 14))
    def mousePressed(mode,event):
        if (SplashScreenMode.mouseInBounds(event.x,event.y, mode.cancelButton.getBounds())):
            mode.app.setActiveMode(mode.app.splashScreenMode)
    def keyPressed(mode,event):
        if (event.key == "r"):
            mode.app.setActiveMode(mode.app.splashScreenMode)

# level select mode
# have to generate the level and get the filename and samplerate
class LevelSelectMode(Mode):
    cancel = Image.open("Images/cancel.png")
    cancel = cancel.resize((60,60))
    instructions = Image.open("Images/instructions.png")
    grey = Image.open("Images/greyButton.png")
    grey = grey.resize((450, int(grey.height * (0.7))))
    smallgrey = grey.resize((int(grey.width * 0.25), int(grey.height * (0.4))))
    modeSelection = None
    def appStarted(mode):
        LevelSelectMode.instructions = LevelSelectMode.instructions.resize((400,100))
        mode.levelHeight = mode.height//2 + LevelSelectMode.grey.height//20
        mode.cancelButton = Button(50,50,(60,60))
        mode.playButton = Button(mode.width//2, mode.height * (0.9), LevelSelectMode.smallgrey.size)
        mode.levelButton = Button(mode.width//2, mode.levelHeight, LevelSelectMode.grey.size)
        mode.singleX = mode.width* 0.15
        mode.multiX = mode.width * 0.85 
        mode.singlePlayerButton = Button(mode.singleX, mode.height * (0.9), LevelSelectMode.smallgrey.size)
        mode.multiPlayerButton = Button(mode.multiX, mode.height * (0.9), LevelSelectMode.smallgrey.size)
        mode.modeSelection = None
        mode.filename = None
        mode.samplerate = None
        mode.levelGenerated = False

        
            
    def mousePressed(mode,event):

        if (SplashScreenMode.mouseInBounds(event.x, event.y, mode.cancelButton.getBounds())):
            mode.app.setActiveMode(mode.app.splashScreenMode)
        elif (SplashScreenMode.mouseInBounds(event.x,event.y, mode.levelButton.getBounds())):
            # making sure input is correct
            mode.filename = mode.getUserInput("What is the Filename?")
            mode.samplerate = mode.getUserInput("What is the samplerate?")
            while mode.filename == None or not mode.filename.endswith(".wav"):
                mode.filename = mode.getUserInput("The File has to end with .wav!")
            
            while mode.samplerate == None or not mode.samplerate.isdigit():
                mode.samplerate = mode.getUserInput("What is the samplerate?")
            mode.levelGenerated = True
            mode.duration = mode.getDuration()
        elif (SplashScreenMode.mouseInBounds(event.x,event.y, mode.playButton.getBounds())):
            mode.app.gameMode.isPaused = False
            if (LevelSelectMode.modeSelection != None):
                mode.app.setActiveMode(mode.app.gameMode)
            else: 
                mode.app.showMessage("You have to pick a mode!")
            if (GameMode.count > 1):
                if (mode.app.gameMode.modeSelected != LevelSelectMode.modeSelection):
                    mode.app.gameMode.appStarted()
                else:
                    mode.app.gameMode.restart()
                GameMode.Attempts = 1
        elif (SplashScreenMode.mouseInBounds(event.x, event.y, mode.singlePlayerButton.getBounds())):
            LevelSelectMode.modeSelection = "singleplayer"
        elif (SplashScreenMode.mouseInBounds(event.x, event.y, mode.multiPlayerButton.getBounds())):
            LevelSelectMode.modeSelection = "multiplayer"

    def getDuration(mode): #duration of overall level/music
        if (mode.levelGenerated):
            beatCollector = BeatCollector(mode.filename,int(mode.samplerate))
            duration = beatCollector.calculateDuration()
        return duration 

        
    
    def redrawAll(mode,canvas):
        canvas.create_image(mode.width//2,mode.height//2,image = ImageTk.PhotoImage(SplashScreenMode.background))
        canvas.create_image(50, 50, image = ImageTk.PhotoImage(LevelSelectMode.cancel))
        canvas.create_image(mode.width//2 + LevelSelectMode.instructions.width * 0.1, mode.height * (0.1), image = ImageTk.PhotoImage(LevelSelectMode.instructions))
        canvas.create_text(mode.width//2, LevelSelectMode.instructions.height + 50, text = """Please input your filename with .wav
and the sampling rate (e.g. 48000, 44100 Hz)
once you click on the button""", font = ("Open Sans Regular", 12), fill = "white")
        
        canvas.create_image(mode.width//2, mode.levelHeight, image = ImageTk.PhotoImage(LevelSelectMode.grey))
        if (mode.filename != None and mode.filename.endswith(".wav")):
            canvas.create_text(mode.width//2, mode.levelHeight, text = mode.filename, font = "Pusab 18", fill = "white")
        if (mode.levelGenerated):
            buttonHeight = mode.height * 0.9
            canvas.create_image(mode.width//2, buttonHeight, image = ImageTk.PhotoImage(LevelSelectMode.smallgrey))  
            canvas.create_image(mode.singleX, buttonHeight, image = ImageTk.PhotoImage(LevelSelectMode.smallgrey))
            canvas.create_image(mode.multiX, buttonHeight, image = ImageTk.PhotoImage(LevelSelectMode.smallgrey))
            canvas.create_text(mode.width//2, buttonHeight, text = "Play!", font = "Pusab 14")
            canvas.create_text(mode.singleX, buttonHeight, text = "Singleplayer", font = "Pusab 14")
            canvas.create_text(mode.multiX, buttonHeight, text = "Multiplayer", font = "Pusab 14")
            canvas.create_text(mode.width//2, mode.levelHeight + LevelSelectMode.grey.height//4, text = mode.duration, font = "Pusab 16", fill = "white")
        if (LevelSelectMode.modeSelection != None and LevelSelectMode.modeSelection == "singleplayer"):
            (x0,y0,x1,y1) = mode.singlePlayerButton.getBounds()
            canvas.create_rectangle(x0,y0,x1,y1, width = 7.5, outline = "goldenrod1")
        elif (LevelSelectMode.modeSelection != None and LevelSelectMode.modeSelection == "multiplayer"):
            (x0,y0,x1,y1) = mode.multiPlayerButton.getBounds()
            canvas.create_rectangle(x0,y0,x1,y1, width = 7.5, outline = "goldenrod1")
        
            

class WonMode(Mode):
    def modeActivated(mode):
        mode.highScore = mode.getScore("score.txt")
        mode.timeSpent = mode.app.gameMode.timeCounter
        mode.app.gameMode.timeCounter = 0 #reset play time
        totalSeconds = mode.timeSpent//1000 
        mode.minutes = totalSeconds//60 
        mode.seconds = totalSeconds%60
        # show statistics from level
        # stars based on the coins collected
        mode.stars = [Star(mode.width//2 - 30, mode.height//2 + 100, Star.outlineImage, (30,30)),
                        Star(mode.width//2, mode.height//2 + 100, Star.outlineImage, (30,30)),
                        Star(mode.width//2 + 30, mode.height//2 + 100, Star.outlineImage, (30,30))]
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
            mode.stars[0].resize()
            mode.stars[1].image = Star.colorImage
            mode.stars[1].resize()
            mode.stars[2].image = Star.colorImage
            mode.stars[2].resize()

    def redrawAll(mode,canvas):
        canvas.create_image(mode.width//2, mode.height//2, image = ImageTk.PhotoImage(GameMode.background))
        canvas.create_image(mode.width//2, mode.height//5, image = ImageTk.PhotoImage(GameMode.complete))
        canvas.create_text(mode.width//2, mode.height * (1/3), text = f"Time Spent: {mode.minutes} Minutes {mode.seconds} Seconds", font = "Lato 20")
        canvas.create_text(mode.width//2, mode.height * (0.4), text = f"Total Attempts: {mode.app.gameMode.Attempts}", font = "Lato 20")
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
            if (currScore >= int(mode.highScore)):
                file.write(str(currScore))
        

class beatModalApp(ModalApp):
    #def __init__(self, width, height): # previous method of stopping playback before
       # super().__init__(width = width, height = height)
        #self.gameMode.pyaudioFlag[0] = False
    def appStopped(self):
        if (GameMode.started):
            self.gameMode.audioPlayer.pyaudioFlag[0] = False
        self.wonMode.resetScore("score.txt")
    def appStarted(self):
        self.gameMode = GameMode() 
        self.wonMode = WonMode()
        self.helpMode = HelpMode()
        self.levelSelectMode = LevelSelectMode()
        self.splashScreenMode = SplashScreenMode()
        self.setActiveMode(self.splashScreenMode)



def drawing_thread(name):
    myApp = beatModalApp(width = 500, height = 500)


if __name__ == "__main__":
    

    threads = list()
    appThread = threading.Thread(target = drawing_thread, args=(1,))
    threads.append(appThread)
    appThread.start()
     
    