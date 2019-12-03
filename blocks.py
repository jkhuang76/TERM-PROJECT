import random
def distance(x1,y1,x2,y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5
seenXY = set()
blocks = set()
for _ in range(100):
            
    blockX = random.randint(300 + 100,500)
    blockY = random.randint(50, 300)
    for (x,y) in seenXY:
        if distance(blockX, blockY, x,y) > 15: 
            blocks.add((blockX, blockY))
            seenXY.add((blockX, blockY))
            break 
print(blocks)