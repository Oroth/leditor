__author__ = 'chephren'
import libtcodpy as libtcod

def defaultBG():
    return libtcod.console_get_default_background(0)

def defaultFG():
    return libtcod.console_get_default_foreground(0)

def screenWidth():
    return libtcod.console_get_width(0)

def screenHeight():
    return libtcod.console_get_height(0)

#def setScreenHeight():


def get_key(key):
    if key.vk == libtcod.KEY_CHAR:
        return chr(key.c)
    else:
        return key.vk

class windowBorderException(Exception):
    pass

def cprint(x, y, fmt, bgcolour=defaultBG(), fgcolour=defaultFG()):
    #defaultbg = defaultBG()
    #defaultfg = defaultFG()
    libtcod.console_set_default_background(0, bgcolour)
    libtcod.console_set_default_foreground(0, fgcolour)
    libtcod.console_print(0, x, y, fmt)
    #libtcod.console_print_ex(0, x, y, libtcod.TCOD_BKGND_SET, libtcod.TCOD_LEFT, )
    #libtcod.console_set_default_background(0, defaultbg)
    #libtcod.console_set_default_foreground(0, defaultfg)


class Pen(object):
    def __init__(self, x1, y1, x2=None, y2=None, top=0):
        self.x1 = x1
        self.y1 = y1
        self.top = top
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

    def topPrint(self, x, y, fmt, bgcolour, fgcolour):
        if self.y1 < self.top:
            self.x1 += len(fmt)
        else:
            defaultbg = defaultBG()
            #cprint(x, y - self.top, fmt, bgcolour, fgcolour)
            libtcod.console_set_default_background(0, bgcolour)
            libtcod.console_set_default_foreground(0, fgcolour)
            libtcod.console_print(0, x, y - self.top, fmt)

            libtcod.console_set_default_background(0, defaultbg)

    def write(self, input, bgcolour=defaultBG()):
        if len(input) > 0 and input[0] == '"':
            self.writeString(input, bgcolour)
        else: self.write2(input, bgcolour)

    def writeString(self, input, bgcolour):
        if bgcolour != defaultBG():
            stringCol = libtcod.light_green
        else:
            stringCol = libtcod.dark_green

        wordList = input.split(' ')
        self.write2(wordList[0], bgcolour, stringCol)

        if len(wordList) > 1:
            for i in wordList[1:]:
                self.write2(' ', bgcolour)
                self.write2(i, bgcolour, stringCol)

    def write2(self, input, bgcolour=defaultBG(), fgcolour=defaultFG()):
        lineSpaceLeft = self.x2 - self.x1
        inputLength = len(input)
        if inputLength < lineSpaceLeft:
            self.topPrint(self.x1, self.y1, input, bgcolour, fgcolour)
            self.x1 += len(input)
        elif self.y1 - self.top < self.y2:

            if inputLength < screenWidth():
                self.y1 += 1
                self.x1 = 0
                self.topPrint(self.x1, self.y1, input, bgcolour, fgcolour)
                self.x1 = len(input)
            else:
                self.topPrint(self.x1, self.y1, input[0:lineSpaceLeft], bgcolour, fgcolour)
                self.y1 += 1
                self.x1 = 0
                self.write2(input[lineSpaceLeft:],bgcolour, fgcolour)
        else:
            raise windowBorderException




    #def writeVert(self, input, bgcolour=defaultBG()):


    def writeOffset(self, input, x, y):
        self.x1 += x
        self.y1 += y
        self.write(input)

    def writeNL(self):
        if self.y1 - self.top + 1 != self.y2:
            self.y1 += 1
            self.x1 = 0
        else: raise windowBorderException

    def writeHL(self, input, bgcolour, index):
        self.write(input)
        libtcod.console_set_char_background(0, self.x1 + index - len(input), self.y1, bgcolour)

        #defaultbg = defaultBG()
        #libtcod.console_set_default_background(0, bgcolour)
        #libtcod.console_print(0, self.x1 + index - len(input), self.y1, input[index])
        #libtcod.console_set_default_background(0, defaultbg())


