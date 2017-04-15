"""
Note that for compatability with libtcod this requires Python-32bit to run

"""
import iop
import windowManager
import eval
import os.path

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


#wm = windowManager.WindowManager(imageFileName)
wm = windowManager.WindowManager().cmdLoadLatestAll()

# Make definitions in the window manager available to the base environment in eval, so that they can be called
# as part of our programs
eval.wm = lambda: wm

def handleKey(key):
    global wm
    result = wm.handleKeys(key)
    if result == 'QUIT-WM':
        iop.closeWindow()
    else:
        wm = result

def handleMouse(mouse):
    global wm
    wm = wm.handleMouse(mouse)

def draw():
    wm.draw()
    iop.screenFlush()

def main():
    draw()
    iop.eventLoopSetup(handleKey, handleMouse, draw)


def profile_main():
    cProfile.run('main()', 'profstats')
    stream = open('pstats.txt', 'w')
    stats = pstats.Stats('profstats', stream=stream)
    stats.strip_dirs().sort_stats('cumulative').print_stats()
    stream.close()

main()


