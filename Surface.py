class Surface(object): #surfaces - "ground", platforms, rectangles
    def __init__(self, x, y, width, height):
        self.x = x 
        self.y = y 
        self.width = width
        self.height = height

    def __repr__(self):
        return f"Surface at {self.x}, {self.y} with width {self.width} and {self.height} height"
    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.width - app.scrollX, self.y - self.height, 
                               self.x + self.width - app.scrollX, self.y + self.height)
        return (x0,y0,x1,y1)