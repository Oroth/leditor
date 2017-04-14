"""
Note that for compatability with libtcod this requires Python-32bit to run

"""

import iop
import windowManager
import eval
import os.path



# Size is in cells
SCREEN_WIDTH = 120
SCREEN_HEIGHT = 70
LIMIT_FPS = 20

iop.setUp(SCREEN_WIDTH, SCREEN_HEIGHT, LIMIT_FPS)

if os.path.isfile("testIDImage"):
    imageFileName = "testIDImage"
else:
    imageFileName = "Image"

#wm = windowManager.WindowManager(imageFileName)
wm = windowManager.WindowManager().cmdLoadLatestAll()
wm.draw()
iop.screenFlush()

# Make definitions in the window manager available to the base environment in eval, so that they can be called
# as part of our programs
eval.wm = lambda: wm

while not iop.isWindowClosed():

    newKey, newMouse = iop.getInput()

    if newMouse.on():
        result = wm.handleMouse(newMouse)
    elif newKey.on():
        result = wm.handleKeys(newKey)
    else:
        result = 'NO-INPUT'

    if result == 'QUIT-WM':
        break
    elif result != 'NO-INPUT':
        wm = result
        wm.draw()
        iop.screenFlush()
