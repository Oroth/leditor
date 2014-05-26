import libtcodpy as libtcod
import TNode
import reader
import windowManager
import time
import Eval

#import peak.

#actual size of the window
SCREEN_WIDTH = 80
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


rootNode = TNode.TNode()
rootNode.setChild(TNode.createTreeFromSexp(reader.loadFile("image")))
wm = windowManager.WindowManager(rootNode)
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

while not libtcod.console_is_window_closed():

    libtcod.console_clear(0)
    wm.draw()
    libtcod.console_flush()

    #handle keys and exit game if needed
    key = libtcod.console_check_for_keypress(libtcod.KEY_PRESSED)

    result = wm.handleKeys(key)
    if result:
        wm = result
    else:
        break

#    exit = wm.handleKeys(key)
#    if exit:
#        break