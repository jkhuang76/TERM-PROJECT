import time
from cmu_112_graphics import *
from tkinter import *
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

class Player(object): # basic player class represented by square
    def __init__(self, x, y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.vx = 0
        self.vy = 0  #test of gravity
        self.isJumping = False
        self.isMoving = False
        self.isOnPlatform = False
        self.isFalling = False
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
        if (isinstance(other, Ground)):
            otherBounds = other.getBounds()
        else: 
            otherBounds = other.getBounds(app)
        if (app.boundsIntersect(playerBounds, otherBounds)): 
            return True
        return False

class Ground(Surface):
    def getBounds(self):
        (x0,y0,x1,y1) = (self.x - self.width , self.y - self.height, 
                               self.x + self.width, self.y + self.height)
        return (x0,y0,x1,y1)

    
class GravityApp(App):
    GRAVITY = 3
    def appStarted(self):
        self.counter = 0 
        self.timerDelay = 100
        self.score = 0
        self.scrollX = 0 
        self.player = Player(50, 100, 20)
        self.ground = Ground(self.width//2, self.height*0.8, self.width//2, self.width//4)
        self.platform = Surface(500, 230, 60, 10)


    def update(self):
        self.scrollX += 5
        if (self.player.vy > 0): 
            self.player.vy += GravityApp.GRAVITY
        elif (not self.player.isOnPlatform and self.player.vy <= 0):
            self.player.vy -= -GravityApp.GRAVITY
            ## have to make sure can't go through when holding up key
        #if ( self.isOnTopOfPlatform() ):
           # self.player.vy = 0 
            
        self.player.y += self.player.vy 
        self.player.x += self.player.vx 

    def isOnTopOfPlatform(self):
        margin = 10
        (platx0, platy0, platx1, platy1)= self.platform.getBounds(self)
        (Px0, Py0, Px1, Py1) = playerBounds = self.player.getBounds()
        if (not self.boundsIntersect((platx0, platy0, platx1, platy1),(Px0, Py0, Px1, Py1))):
            if (Px0 >= platx0 and Px1 <= platx1 + self.player.size and Py1 <= platy0 and Py1 > platy0 - self.player.size ):
                #Py0 >= platy0 - self.player.size - margin
                return True 
        return False

    def timerFired(self):
        # go through beats and move them to the left
        self.counter += self.timerDelay
        if (not self.player.isJumping and self.isOnTopOfPlatform()):
            self.player.isOnPlatform = True 
            self.player.vy = 0
            
        else: 
            self.player.isOnPlatform = False
        self.update()
        

        #self.stopMomentum()
        


            

    def movePlayer(self,dx,dy):
        self.player.x += dx 
        self.player.y += dy
        if (self.player.collidesWith(self.ground,self)):
            self.player.x -= dx 
            self.player.y -= dy


            

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
            self.player.vy = -10
            # "gravity", have to create floor and collisions to stop momentum
    def keyReleased(self,event):
        if (event.key == "Right" or event.key == "Left"):
            self.player.isMoving = False 
            self.player.vx = 0
        if (event.key == "Up"):
            self.player.isJumping = False
        
    
    def boundsIntersect(self, boundsA, boundsB):
        (ax0, ay0, ax1, ay1) = boundsA
        (bx0, by0, bx1, by1) = boundsB
        return ((ax1 >= bx0) and (bx1 >= ax0) and
                (ay1 >= by0) and (by1 >= ay0))


        

    def redrawAll(self,canvas): # draw player nad beats
        canvas.create_line(100, 0, 100, self.height) #baseline
    

        canvas.create_rectangle(self.player.x - self.player.size, self.player.y - self.player.size, 
                            self.player.x + self.player.size, self.player.y + self.player.size)
        canvas.create_rectangle(self.ground.x - self.ground.width, self.ground.y - self.ground.height, 
                               self.ground.x + self.ground.width, self.ground.y + self.ground.height, fill = "black")

        canvas.create_rectangle(self.platform.x - self.platform.width - self.scrollX, self.platform.y - self.platform.height, 
                               self.platform.x + self.platform.width - self.scrollX, self.platform.y + self.platform.height)

myApp = GravityApp(width = 500, height = 500)

        