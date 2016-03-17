import libtcodpy as libtcod
import TNode
import reader
import windowManager
import time
import Eval
import os.path

# version 0.2
#import peak.

#actual size of the window
SCREEN_WIDTH = 150
SCREEN_HEIGHT = 50

LIMIT_FPS = 20  # 20 frames-per-second maximum


#############################################
# Initialization & Main Loop
#############################################

libtcod.console_set_custom_font('fonts/terminal8x14_gs_ro.png',
        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'List-editor', False)
libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_set_background_flag(0, libtcod.BKGND_SET)
libtcod.console_set_default_foreground(0, libtcod.white)


if os.path.isfile("testIDImage"):
    imageFileName = "testIDImage"
else:
    imageFileName = "Image"

pyLoad = reader.loadFile(imageFileName)
pyImage = [0]
pyImage.append(pyLoad)
#nodeTree = TNode.createTreeFromNodeIDValueSexp(pyImage)
nodeTree = TNode.createTree(pyImage)

wm = windowManager.WindowManager(nodeTree, imageFileName)


Eval.wm = lambda: wm


print "width is: ", libtcod.console_get_width(0)
print "height is: ", libtcod.console_get_height(0)



def print_time(threadName, delay):
    count = 0
    while count < 5:
        time.sleep(delay)
        count += 1
        #print "%s: %s" % ( threadName, time.ctime(time.time()) )
        libtcod.console_print(0, 0, 30, "%s: %s" % ( threadName, time.ctime(time.time())))
        libtcod.console_flush()

def getKeypress():
    key = libtcod.console_check_for_keypress()
    if key.c:
        return chr(key.c)
    else:
        return key.vk

key = libtcod.Key()
mouse = libtcod.Mouse()

while not libtcod.console_is_window_closed():

    #libtcod.console_clear(0)
    wm.draw()
    libtcod.console_flush()

    #key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)

    result = wm.handleKeys(key, mouse)
    if result:
        wm = result
    else:
        break
