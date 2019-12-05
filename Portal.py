from GameObject import GameObject
from PIL import Image # Pillow image manipulation https://pillow.readthedocs.io/en/stable/reference/Image.html
#access modeApp to turn on the actual mode
class Portal(GameObject):
    image = Image.open("Images/ShipPortal.png")
    def __init__(self,x,y,image,size):
        super().__init__(x,y,size)
        self.image = Portal.image.resize(size)

class OnPortal(Portal):
    def turnOnSpeed(self, mode):
        mode.isSpeedMode = True

class OffPortal(Portal):
    def turnOffSpeed(self, mode):
        mode.isSpeedMode = False