class gameObject(object):

    def __init__(self, x,y, size):
        self.x = x
        self.y = y 
        self.size = size
        self.width, self.height = self.size[0], self.size[1]

    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.width//2 - app.scrollX, self.y - self.height//2,
                        self.x + self.width//2 - app.scrollX, self.y + self.height//2)
        return (x0,y0,x1,y1)
    
    def __repr__(self):
        return f"{self.x}, {self.y} with {gameObject.image}"

