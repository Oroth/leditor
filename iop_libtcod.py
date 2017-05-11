from lib import libtcodpy as libtcod
import copy
from string import printable
import time


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
KEY_CHAR = libtcod.KEY_CHAR


class Colour(libtcod.Color):
    def __init__(self, *args, **kwargs):
        super(Colour, self).__init__(*args, **kwargs)

def defaultBG():
    return libtcod.console_get_default_background(0)

def defaultFG():
    return libtcod.console_get_default_foreground(0)

class Key():
    def __init__(self, keyObj):
        self.keyObj = keyObj

    vkCharMap = {
            KEY_ENTER: 13,
            KEY_ESCAPE: 27,
            KEY_BACKSPACE: 8,
            KEY_SPACE: 32,
            KEY_TAB: 9
        }

    shiftedKeys = '!"$%^&*()_+{}:@~|<>?'

    @classmethod
    def vk(cls, vk, ctrl=False, alt=False, shift=False):
        newKey = libtcod.Key()
        newKey.vk = vk
        if vk in Key.vkCharMap:
            newKey.c = Key.vkCharMap[vk]
        else:
            newKey.c = 0
        newKey.lctrl = ctrl
        newKey.lalt = alt
        newKey.shift = shift
        return cls(newKey)

    @classmethod
    def c(cls, c, ctrl=False, alt=False, shift=None):
        newKey = libtcod.Key()
        newKey.vk = libtcod.KEY_CHAR
        newKey.c = ord(c)
        newKey.lctrl = ctrl
        newKey.lalt = alt
        if shift is not None:
            newKey.shift = shift
        elif c.isupper() or c in Key.shiftedKeys:
            newKey.shift = True
        else:
            newKey.shift = False

        return cls(newKey)


    def __eq__(x, y):
        return x._key() == y._key()

    def __hash__(self):
        return hash(self._key())

    def _key(self):
        k = self.keyObj
        return (k.vk, k.c, k.lctrl or k.rctrl, k.lalt or k.ralt, k.shift)

    def code(self):
        return self.keyObj.vk

    def char(self):
        return chr(self.keyObj.c)

    def off(self):
        return self.keyObj.vk == 0

    def on(self):
        return self.keyObj.vk != 0

    def ctrl(self):
        return self.keyObj.lctrl or self.keyObj.rctrl

    def alt(self):
        return self.keyObj.lalt or self.keyObj.ralt

    def shift(self):
        return self.keyObj.shift

    def isPrintable(self):
        return chr(self.keyObj.c) in printable

class Mouse():
    def __init__(self, mouseObj=libtcod.Mouse()):
        self.mouseObj = mouseObj

    def lbuttonPressed(self):
        return self.mouseObj.lbutton_pressed

    def wheelScrolled(self):
        return self.mouseObj.wheel_up or self.mouseObj.wheel_down

    def wheelUp(self):
        return self.mouseObj.wheel_up

    def wheelDown(self):
        return self.mouseObj.wheel_down

    def on(self):
        m = self.mouseObj
        return m.lbutton_pressed or m.wheel_up or m.wheel_down

    def getPos(self):
        return self.mouseObj.cx, self.mouseObj.cy

    def getMouseWithRelativePosition(self, newX1, newY1):
        newMouseObj = copy.copy(self.mouseObj)
        newMouseObj.cx = newMouseObj.cx - newX1
        newMouseObj.cy = newMouseObj.cy - newY1
        return Mouse(newMouseObj)

    @property
    def x(self):
        return self.mouseObj.cx

    @property
    def y(self):
        return self.mouseObj.cy


class IOApplication(object):
    def __init__(self, screenCols, screenRows, bgcol, fgcol):
        self._key = libtcod.Key()
        self._mouse = libtcod.Mouse()
        self._loopActive = True
        self.screenCols = screenCols
        self.screenRows = screenRows
        self.setUp(screenCols, screenRows, 20, fgcol)

    def setUp(self, screenWidth, screenHeight, FPS, fgcol):
        libtcod.console_set_custom_font('fonts/terminal8x14_gs_ro.png',
                libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
        libtcod.console_init_root(screenWidth, screenHeight, 'List-editor', False)
        libtcod.sys_set_fps(FPS)
        libtcod.console_set_background_flag(0, libtcod.BKGND_SET)
        libtcod.console_set_default_foreground(0, fgcol)


    def eventLoopSetup(self, handleKey, handleMouse, draw):
        while not libtcod.console_is_window_closed() and self._loopActive:
            time.sleep(0.01)
            newKey, newMouse = self.getInput()
            if newMouse.on():
                handleMouse(newMouse)
                draw()
            elif newKey.on():
                handleKey(newKey)
                draw()

    def closeWindow(self):
        self._loopActive = False

    def toggleFullScreen(self):
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    def getInput(self):
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,self._key,self._mouse)
        return Key(self._key), Mouse(self._mouse)

    def screenPrint(self, x, y, cell):
        libtcod.console_put_char_ex(0, x, y, cell.character, cell.fgColour, cell.bgColour)

    def screenFlush(self):
        libtcod.console_flush()
