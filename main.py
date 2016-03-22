import iop
import windowManager
import Eval
import os.path

# Size is in cells
SCREEN_WIDTH = 150
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

iop.setUp(SCREEN_WIDTH, SCREEN_HEIGHT, LIMIT_FPS)

if os.path.isfile("testIDImage"):
    imageFileName = "testIDImage"
else:
    imageFileName = "Image"

wm = windowManager.WindowManager(imageFileName)

# Make definitions in the window manager available to the base environment in eval, so that they can be called
# as part of our programs
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