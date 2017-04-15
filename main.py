"""
Note that for compatability with libtcod this requires Python-32bit to run

"""

import iop
import windowManager
import eval
import os.path
import time

import cProfile
import pstats

# Size is in cells
SCREEN_WIDTH = 120
SCREEN_HEIGHT = 70
LIMIT_FPS = 20

iop.setUp(SCREEN_WIDTH, SCREEN_HEIGHT, LIMIT_FPS)

if os.path.isfile("testIDImage"):
    imageFileName = "testIDImage"
else:
    imageFileName = "Image"

class Box(object):
    def __init__(self, obj):
        self.o = obj

#wm = windowManager.WindowManager(imageFileName)
wmi = windowManager.WindowManager().cmdLoadLatestAll()
WM = Box(wmi)

# Make definitions in the window manager available to the base environment in eval, so that they can be called
# as part of our programs
eval.wm = lambda: WM.o

def handleKey(key):
    result = WM.o.handleKeys(key)

    if result == 'QUIT-WM':
        return False
        #iop.closeWindow()

    WM.o = result



def main():
    #wm = WM.o
    WM.o.draw()
    iop.screenFlush()

    while not iop.isWindowClosed():

        time.sleep(0.01)
        newKey, newMouse = iop.getInput()

        if newMouse.on():
            result = WM.o.handleMouse(newMouse)
        elif newKey.on():
            result = WM.o.handleKeys(newKey)
        else:
            result = 'NO-INPUT'

        if result == 'QUIT-WM':
            break
        elif result != 'NO-INPUT':
            WM.o = result
            WM.o.draw()
            iop.screenFlush()

def profile_main():
    cProfile.run('main()', 'profstats')
    stream = open('pstats.txt', 'w')
    stats = pstats.Stats('profstats', stream=stream)
    stats.strip_dirs().sort_stats('cumulative').print_stats()
    stream.close()

main()


