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
from Portal import Portal, OnPortal, OffPortal
import numpy as np
from numpy import median, diff

# cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html

class Spike(GameObject):
    image = Image.open("spike.png")
    def __init__(self, x, y, image, size):
        super().__init__(x,y,size)
        self.image = Spike.image.resize(size)
startTime = time.time()

class JumpPad(GameObject):
    image = Image.open("YellowPad.png")
    def __init__(self,x,y,image, size):
        super().__init__(x,y,size)
        self.image = JumpPad.image.resize(size)

class Coin(GameObject):
    image = Image.open("SecretCoin.png")
    def __init__(self,x,y,image, size):
        super().__init__(x,y,size)
        self.image = Coin.image.resize(size)


class Block(GameObject):
    image = Image.open("BeamBlock06.png")
    def __init__(self,x,y,image, size):
        super().__init__(x,y,size)
        self.image = Block.image.resize(size)


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
        self.jumps = []
        self.coins = set()
        self.portals = set() 
        self.blocks = set()
        self.goal = None
        self.defaultGap = 35
        self.bpm = self.beats_to_bpm()
        self.scrollSpeed = int((self.bpm/60) *10)
        self.height = 500
        self.spikeImage = Image.open('spike.png')

    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5

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
                self.goal = Goal(beats[i], 200, 20, self.height * (2/3))
            elif (i == 0):
                beats[i] += 500 
                self.platforms.append(Surface(beats[i], defaultY, 30, 10))
            else: 
                platY = defaultY
                timeDif = beats[i+1] - beats[i]
                platWidth = round(timeDif * self.scrollSpeed,2)
                platWidth *= 4 # how wide the platform is based on how fast the scrolling is and time dif
                spikeSize = int(platWidth)
                beats[i] = round(beats[i-1] + platWidth) + self.defaultGap*2
                # add descending and ascending platforms
                if (volumes[i+1] > volumes[i]):
                    platY = self.platforms[i-1].y - 10
                elif(volumes[i+1] < volumes[i]):
                    platY = self.platforms[i-1].y + 10 
                if (platY >= groundHeight):
                    platY = self.platforms[i-1].y - 50 
                    self.obstacles.append(Spike(beats[i], platY - 35, Spike.image, (spikeSize,spikeHeight)))
                    newX = (beats[i-1] + beats[i])//2
                    print(newX)
                    newSpikeY = 375 - spikeHeight/2
                    self.obstacles.append(Spike(newX, newSpikeY , Spike.image, (spikeSize, spikeHeight)))
                    self.jumps.append(JumpPad(newX, groundHeight - 30 - 15, JumpPad.image, (30,30) ))
                if (i %10 == 0 ):
                    spikeHeight = int(abs(volumes[i])* 10)
                    if spikeHeight > 50 or spikeHeight < 10:
                        spikeHeight = 30
                    self.obstacles.append(Spike(beats[i], platY - 35, Spike.image, (spikeSize,spikeHeight)))
                self.platforms.append(Surface(beats[i], platY, platWidth, 20))
    def createJumps(self):
        beats, volumes = self.collectBeats()
        groundHeight = 375
    
        for i in range(len(self.platforms)-1):
            if i == 0: 
                pass
                #self.jumps.append(JumpPad(beats[i], 280, JumpPad.image, (30,30)))
            elif (self.platforms[i].y - self.platforms[i-1].y < -20 ):
                #print('hi')
                jumpX = (beats[i+1] + beats[i])//2
                jumpY = random.randint(325, 350)
                #print(jumpX, jumpY)
                self.jumps.append(JumpPad(jumpX, jumpY, JumpPad.image, (30,30)))
        
    
    def createSpeedMode(self):
        third = len(self.platforms)//3
        half = len(self.platforms)//2
        print("Portal: " + str(self.platforms[third].x))
        self.portals.add(OnPortal(self.platforms[third].x+ self.defaultGap, self.height//5, Portal.image, (50,50)))
        seenX = set()
        seenY = set()
        for _ in range(half - third):
            
            while True: 
                blockX = random.randint(self.platforms[third].x + 100,self.platforms[half].x)
                blockY = random.randint(50, 300)
                if (blockX - 20 not in seenX and blockY - 20 not in seenY and 
                    blockX + 20 not in seenX and blockY + 20 not in seenY): 
                    self.blocks.add(Block(blockX,blockY, Block.image,(30,30)))
                    seenX.add(blockX)
                    seenY.add(blockY)
                    break
        self.portals.add(OffPortal(self.platforms[half].x, self.height//5, Portal.image, (50,50)))


    def createCoins(self):
        beats, volumes = self.collectBeats() 
        counter = 0
        groundHeight = 375
        for i in range(len(self.platforms)):
            if (i == (len(self.platforms)//3)):
                if (self.platforms[i].y >= 325 ):
                    self.coins.add(Coin(beats[i], self.height* (2/5), Coin.image, (50,50)))
                else: 
                    self.coins.add(Coin(beats[i], 150, Coin.image, (50,50)))
            elif (i == int(len(self.platforms)* (2/3))):
                if (self.platforms[i].width < 30):
                    self.coins.add(Coin(beats[i], self.platforms[i].y - 85, Coin.image,(50,50)))
            elif (i == len(self.platforms) - 50):
                if (self.platforms[i].y < 300):
                    self.coins.add(Coin(beats[i], self.platforms[i].y + 30, Coin.image, (50,50) ))
                else: 
                    self.coins.add(Coin(beats[i], self.platforms[i].y - 100, Coin.image, (50,50)))
        for coin in self.coins:
            print(coin.x)

    def getJumps(self):
        return self.jumps
    
    def getPortals(self):
        return self.portals
    
    def getPlatforms(self):
        return self.platforms
    def getGoal(self):
        return self.goal
    def getCoins(self):
        return self.coins

class Dot(object):
    def __init__(self,x,y,r,color):
        self.x = x
        self.y = y
        self.r = r 
        self.color = color 
        self.dx = random.randint(-30, -20) 
        self.dy = random.randint(-30,40)
    def move(self):
        self.x += self.dx
        self.y += self.dy

class Goal(object): # make goal into cyan rectangle, with animation
    # explode method to show level complete screen
    def __init__(self, x, y, width, height): 
        self.x = x 
        self.y = y 
        self.width = width
        self.height = height
        self.color = "cyan"
        self.dots = [Dot(self.x, self.y, random.randint(5,20), random.choice(["yellow", "red", "blue"])) for _ in range(20)]

    def explode(self):
        for dot in self.dots:
            dot.move()


    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.width - app.scrollX, self.y - self.height, 
                               self.x + self.width - app.scrollX, self.y + self.height)
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




