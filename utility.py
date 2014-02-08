__author__ = 'chephren'
import libtcodpy as libtcod

def defaultBG():
    return libtcod.console_get_default_background(0)

def screenWidth():
    return libtcod.console_get_width(0)

def screenHeight():
    return libtcod.console_get_height(0)

def get_key(key):
    if key.vk == libtcod.KEY_CHAR:
        return chr(key.c)
    else:
        return key.vk

def cprint(x, y, fmt, bgcolour=defaultBG()):
    defaultbg = defaultBG()
    libtcod.console_set_default_background(0, bgcolour)
    libtcod.console_print(0, x, y, fmt)
    libtcod.console_set_default_background(0, defaultbg)


class Pen(object):
    def __init__(self, x1, y1, x2=None, y2=None):
        self.x1 = x1
        self.y1 = y1
        if x2 is None:
            self.x2 = libtcod.console_get_width(0)
        else:
            self.x2 = x2
        if y2 is None:
            self.y2 = libtcod.console_get_height(0)
        else:
            self.y2 = y2

    def skip(self, x, y):
        self.x1 += x
        self.y1 += y

    def write(self, input, bgcolour=defaultBG()):
        if self.x1 + len(input) < self.x2:
            cprint(self.x1, self.y1, input, bgcolour)
            self.x1 += len(input)
        elif self.y1 < self.y2:
            self.y1 += 1
            self.x1 = 0
            cprint(self.x1, self.y1, input, bgcolour)
            self.x1 = len(input)
        else:
            raise OverflowError

    #def writeVert(self, input, bgcolour=defaultBG()):


    def writeOffset(self, input, x, y):
        self.x1 += x
        self.y1 += y
        self.write(input)

    def writeNL(self):
        if self.y1 + 1 != self.y2:
            self.y1 += 1
            self.x1 = 0
        else: raise OverflowError

    def writeHL(self, input, bgcolour, index):
        self.write(input)
        libtcod.console_set_char_background(0, self.x1 + index - len(input), self.y1, bgcolour)

        #defaultbg = defaultBG()
        #libtcod.console_set_default_background(0, bgcolour)
        #libtcod.console_print(0, self.x1 + index - len(input), self.y1, input[index])
        #libtcod.console_set_default_background(0, defaultbg())


