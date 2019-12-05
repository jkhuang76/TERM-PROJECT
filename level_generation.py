import threading
import random # python built in random module
import aubio # module for audio file analysis, beat detection 
import copy
import time # python time module for calculating time passed
from cmu_112_graphics import * # cmu 112 graphics from https://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
from Surface import Surface
from GameObject import GameObject
from tkinter import * #tkinter graphics module https://docs.python.org/3/library/tkinter.html#tkinter-modules
from PIL import Image # Pillow image manipulation https://pillow.readthedocs.io/en/stable/reference/Image.html
from Portal import Portal, OnPortal, OffPortal
import numpy as np #numpy for numerical operations 
from numpy import median, diff # https://numpy.org/


# create GameObject classes, attach images to them
class Spike(GameObject):
    image = Image.open("Images/spike.png")
    def __init__(self, x, y, image, size):
        super().__init__(x,y,size)
        self.image = Spike.image.resize(size)
startTime = time.time()

class JumpPad(GameObject):
    image = Image.open("Images/YellowPad.png")
    def __init__(self,x,y,image, size):
        super().__init__(x,y,size)
        self.image = JumpPad.image.resize(size)

class Coin(GameObject):
    image = Image.open("Images/SecretCoin.png")
    def __init__(self,x,y,image, size):
        super().__init__(x,y,size)
        self.image = Coin.image.resize(size)


class Block(GameObject):
    image = Image.open("Images/BeamBlock06.png")
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
        self.portals = [] 
        self.blocks = set()
        self.goal = None
        self.defaultGap = 25
        self.bpm = self.beats_to_bpm()
        self.scrollSpeed = int((self.bpm/60) *10)
        self.height = 500

    @staticmethod
    def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5

    def collectBeats(self): # collectBeats basic idea from https://github.com/aubio/aubio/tree/master/python/demos, tempo demo
        self.music_source = aubio.source(self.fileName, self.samplingRate, self.hop_size)
        self.music_tempo = aubio.tempo("default", self.fft_size, self.hop_size, self.samplingRate)
        while True: # collect location of beats in the song, in terms of the time in the song
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

    def calculateDuration(self):
        self.collectBeats() #read in all the frames
        #total duration is total frames divided by sampling rate
        totalSeconds = self.total_frames/self.samplingRate 
        minutes = int(totalSeconds//60.0)
        seconds = round(totalSeconds % 60 )
        return f"{minutes} minutes {seconds} seconds"

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
                self.platforms.append(Surface(beats[i], defaultY, 30, 20))
            else: 
                platY = defaultY
                timeDif = beats[i+1] - beats[i]
                platWidth = round(timeDif * self.scrollSpeed,2)
                platWidth *= 4 # how wide the platform is based on how fast the scrolling is and time difference
                spikeSize = int(platWidth)
                beats[i] = round(beats[i-1] + platWidth) + self.defaultGap*2
                # add descending and ascending platforms
                # based on the sound level
                if (volumes[i+1] > volumes[i]):
                    platY = self.platforms[i-1].y - 10
                elif(volumes[i+1] < volumes[i]):
                    platY = self.platforms[i-1].y + 10 
                if (platY >= groundHeight):
                    # have to move platform up if it goes inside the ground
                    platY = self.platforms[i-1].y - 50 
                    self.obstacles.append(Spike(beats[i], platY - 35, Spike.image, (spikeSize,spikeHeight)))
                    newX = (beats[i-1] + beats[i])//2 # adding jumpPad to make up for height difference
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
            if (self.platforms[i].y - self.platforms[i-1].y < -20 ):
                jumpX = (beats[i+1] + beats[i])//2
                jumpY = random.randint(325, 350)
                self.jumps.append(JumpPad(jumpX, jumpY, JumpPad.image, (30,30)))
        
    
    def createSpeedMode(self):
        third = len(self.platforms)//3
        half = len(self.platforms)//2
        # entrance portal
        self.portals.append(OnPortal(self.platforms[third].x+ self.defaultGap, self.height//5, Portal.image, (50,50)))
        seenX = set()
        seenY = set()
        for _ in range(half - third):
            
            while True: #generating block obstacle course
                blockX = random.randint(self.platforms[third].x + 200,self.platforms[half].x)
                blockY = random.randint(90, 300)
                if (blockX - 30 not in seenX and blockY - 30 not in seenY and 
                    blockX + 30 not in seenX and blockY + 30 not in seenY): 
                    self.blocks.add(Block(blockX,blockY, Block.image,(30,30)))
                    seenX.add(blockX)
                    seenY.add(blockY)
                    break
        #exit portal
        self.portals.append(OffPortal(self.platforms[half].x, self.height//5, Portal.image, (50,50)))


    def createCoins(self): # create the 3 special coins that determine number of stars in the level 
        beats, volumes = self.collectBeats() 
        counter = 0
        groundHeight = 375
        # approximately distributed in each third of the level
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
        if (len(self.coins) != 3):
            for i in range (3 - len(self.coins)):
                randomIndex = random.randint(0, len(self.platforms))
                self.coins.add(Coin(beats[randomIndex], self.platforms[randomIndex].y - 60, Coin.image, (50,50)))

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
    def generateDots(self): #dots for explosion animation 
        self.dots = [Dot(self.x, self.y, random.randint(5,20), random.choice(["yellow", "red", "blue", "green"])) for _ in range(20)]

    def explode(self):
        for dot in self.dots:
            dot.move()


    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.width - app.scrollX, self.y - self.height, 
                               self.x + self.width - app.scrollX, self.y + self.height)
        return (x0,y0,x1,y1)

       
    
#level = LevelApp(width = 500, height = 500) # previous levelApp to see how level looked




