from PIL import Image
class Surface(object): #surfaces - "ground", platforms, rectangles
    image = Image.open("RegularPlatform01.png")
    def __init__(self, x, y, width, height):
        self.x = x 
        self.y = y 
        self.width = width
        self.height = height
        self.image = Surface.image.resize((int(self.width), int(self.height)))

    def __repr__(self):
        return f"Surface at {self.x}, {self.y} with width {self.width} and {self.height} height"
    def getBounds(self,app):
        (x0,y0,x1,y1) = (self.x - self.width//2 - app.scrollX, self.y - self.height//2, 
                               self.x + self.width//2 - app.scrollX, self.y + self.height//2)
        return (x0,y0,x1,y1)