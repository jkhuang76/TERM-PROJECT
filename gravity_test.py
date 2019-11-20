import time
from cmu_112_graphics import *
from tkinter import *
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
        self.vy = -5  #test of gravity
        self.isJumping = False
        self.isMoving = False
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
    def jump(self):
        self.y += self.vy *3 #timestarted time ended 
        self.x += self.vx *3

        if (self.vy < 0):
            self.vy += 1
        else:
            self.vy = 5
            self.vy -=1 
        if (self.y > 300):
            self.isJumping = False
            self.y = 50 
            self.x = 50
            self.vy = -5
class GravityApp(App):
    
    def appStarted(self):
        self.counter = 0 
        self.timerDelay = 100
        self.score = 0
        self.player = Player(50, 100, 20)
        self.ground = Surface(self.width//2, self.height*0.8, self.width//2, True)

    

     
    def timerFired(self):
        # go through beats and move them to the left
        self.counter += self.timerDelay
        if self.player.isJumping == True:
            self.player.jump()
            

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

            # "gravity", have to create floor and collisions to stop momentum
    def keyReleased(self,event):
        if (event.key == "Right" or event.key == "Left"):
            self.player.isMoving = False 
            self.player.vx = 0 
        
    
    def boundsIntersect(self, boundsA, boundsB):
        (ax0, ay0, ax1, ay1) = boundsA
        (bx0, by0, bx1, by1) = boundsB
        return ((ax1 >= bx0) and (bx1 >= ax0) and
                (ay1 >= by0) and (by1 >= ay0))


        

    def redrawAll(self,canvas): # draw player nad beats
        canvas.create_line(100, 0, 100, self.height) #baseline
    

        canvas.create_rectangle(self.player.x - self.player.size, self.player.y - self.player.size, 
                            self.player.x + self.player.size, self.player.y + self.player.size)
        canvas.create_rectangle(self.ground.x - self.ground.size, self.ground.y - self.ground.size//2, 
                               self.ground.x + self.ground.size, self.ground.y + self.ground.size//2, fill = "black")

myApp = GravityApp(width = 500, height = 500)

        