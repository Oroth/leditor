import iop
import windowManager
import eval
import os.path

# Size is in cells
SCREEN_WIDTH = 120
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
eval.wm = lambda: wm


while not iop.isWindowClosed():
    wm.draw()
    iop.screenFlush()
    newKey, newMouse = iop.getInput()

    # if newKey.keyObj.vk != 0:
    #     print "raw value ", newKey.code()
    #     print "c value ", newKey.keyObj.c
    #     #print newKey.__eq__
    #     print newKey._key()
    #
    #     #testKey = iop.Key.vk(iop.KEY_CHAR)
    #     testKey = iop.Key.c('L')
    #     print "test key value ", testKey.code()
    #     print "test c value ", testKey.keyObj.c
    #     print testKey._key()
    #
    #     print testKey == newKey

    result = wm.handleKeys(newKey, newMouse)
    if result:
        wm = result
    else:
        break