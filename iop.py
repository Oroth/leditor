from lib import libtcodpy as libtcod
import copy
from string import printable

KEY_ENTER = libtcod.KEY_ENTER
KEY_ESCAPE = libtcod.KEY_ESCAPE
KEY_BACKSPACE = libtcod.KEY_BACKSPACE
KEY_DELETE = libtcod.KEY_DELETE
KEY_SPACE = libtcod.KEY_SPACE
KEY_TAB = libtcod.KEY_TAB
KEY_ALT = libtcod.KEY_ALT
KEY_F1 = libtcod.KEY_F1
KEY_F2 = libtcod.KEY_F2
KEY_F5 = libtcod.KEY_F5
KEY_F8 = libtcod.KEY_F8
KEY_F9 = libtcod.KEY_F9
KEY_F10 = libtcod.KEY_F10
KEY_F11 = libtcod.KEY_F11
KEY_F12 = libtcod.KEY_F12
KEY_LEFT = libtcod.KEY_LEFT
KEY_RIGHT = libtcod.KEY_RIGHT
KEY_UP = libtcod.KEY_UP
KEY_DOWN = libtcod.KEY_DOWN

black = libtcod.black
white = libtcod.white
light_green = libtcod.light_green
light_sky = libtcod.light_sky
light_purple = libtcod.light_purple
azure = libtcod.azure
light_grey = libtcod.light_grey
grey = libtcod.grey
dark_green = libtcod.dark_green
dark_red = libtcod.dark_red
darker_green = libtcod.darker_green
darker_sky = libtcod.darker_sky


class Key():
    def __init__(self, keyObj):
        self.keyObj = keyObj

    def code(self):
        return self.keyObj.vk

    def char(self):
        return chr(self.keyObj.c)

    def lctrl(self):
        return self.keyObj.lctrl

    def lalt(self):
        return self.keyObj.lalt
        #return self.keyObj.vk == KEY_ALT

    def shift(self):
        return self.keyObj.shift

    def isPrintable(self):
        return chr(self.keyObj.c) in printable

class Mouse():
    def __init__(self, mouseObj):
        self.mouseObj = mouseObj

    def lbuttonPressed(self):
        return self.mouseObj.lbutton_pressed

    def wheelUp(self):
        return self.mouseObj.wheel_up

    def wheelDown(self):
        return self.mouseObj.wheel_down

    def getPos(self):
        return self.mouseObj.cx, self.mouseObj.cy

    def getMouseWithRelativePosition(self, newX1, newY1):
        newMouseObj = copy.copy(self.mouseObj)
        newMouseObj.cx = newMouseObj.cx - newX1
        newMouseObj.cy = newMouseObj.cy - newY1
        return Mouse(newMouseObj)

    # positions on console
    def x(self):
        return self.mouseObj.cx

    def y(self):
        return self.mouseObj.cy


key = libtcod.Key()
mouse = libtcod.Mouse()

def defaultBG():
    return libtcod.console_get_default_background(0)

def defaultFG():
    return libtcod.console_get_default_foreground(0)

def screenWidth():
    return libtcod.console_get_width(0)

def screenHeight():
    return libtcod.console_get_height(0)

def screenFlush():
    libtcod.console_flush()

def setUp(screenWidth, screenHeight, FPS):
    libtcod.console_set_custom_font('fonts/terminal8x14_gs_ro.png',
            libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
    libtcod.console_init_root(screenWidth, screenHeight, 'List-editor', False)
    libtcod.sys_set_fps(FPS)
    libtcod.console_set_background_flag(0, libtcod.BKGND_SET)
    libtcod.console_set_default_foreground(0, libtcod.white)

def isWindowClosed():
    return libtcod.console_is_window_closed()

def toggleFullScreen():
    libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

def getInput():
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
    return Key(key), Mouse(mouse)

def screenPrint(x, y, fmt, bgcolour=defaultBG(), fgcolour=defaultFG()):
    libtcod.console_set_default_background(0, bgcolour)
    libtcod.console_set_default_foreground(0, fgcolour)
    libtcod.console_print(0, x, y, fmt)