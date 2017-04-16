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


if os.path.isfile("testIDImage"):
    imageFileName = "testIDImage"
else:
    imageFileName = "Image"

app = iop.Application(SCREEN_WIDTH, SCREEN_HEIGHT)
#wm = windowManager.WindowManager(imageFileName)
wm = windowManager.WindowManager(app).cmdLoadLatestAll()

# Make definitions in the window manager available to the base environment in eval, so that they can be called
# as part of our programs
eval.wm = lambda: wm

def handleKey(key):
    global wm
    result = wm.handleKeys(key)
    if result == 'QUIT-WM':
        app.closeWindow()
    else:
        wm = result

def handleMouse(mouse):
    global wm
    wm = wm.handleMouse(mouse)

def draw():
    wm.draw()
    app.screenFlush()

def main():
    draw()
    app.eventLoopSetup(handleKey, handleMouse, draw)


def profile_main():
    cProfile.run('main()', 'profstats')
    stream = open('pstats.txt', 'w')
    stats = pstats.Stats('profstats', stream=stream)
    stats.strip_dirs().sort_stats('cumulative').print_stats()
    stream.close()

main()


