import iop
import TNode
import reader
import windowManager
import Eval
import os.path


#actual size of the window
SCREEN_WIDTH = 150
SCREEN_HEIGHT = 50

LIMIT_FPS = 20  # 20 frames-per-second maximum


#############################################
# Initialization & Main Loop
#############################################

iop.setUp(SCREEN_WIDTH, SCREEN_HEIGHT, LIMIT_FPS)


if os.path.isfile("testIDImage"):
    imageFileName = "testIDImage"
else:
    imageFileName = "Image"

pyLoad = reader.loadFile(imageFileName)
pyImage = [0]
pyImage.append(pyLoad)
nodeTree = TNode.createTree(pyImage)

wm = windowManager.WindowManager(nodeTree, imageFileName)


Eval.wm = lambda: wm


while not iop.isWindowClosed():
    wm.draw()
    iop.screenFlush()

    newKey, newMouse = iop.getInput()

    result = wm.handleKeys(newKey, newMouse)
    if result:
        wm = result
    else:
        break
