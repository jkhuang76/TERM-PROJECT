from GameObject import GameObject
from PIL import Image
class Portal(GameObject):
    image = Image.open("ShipPortal.png")
    def __init__(self,x,y,image,size):
        super().__init__(x,y,size)
        self.image = Portal.image.resize(size)

class OnPortal(Portal):
    def turnOnSpeed(self, mode):
        mode.isSpeedMode = True

class OffPortal(Portal):
    def turnOffSpeed(self, mode):
        mode.isSpeedMode = False