__author__ = 'chephren'
import iop

class windowBorderException(Exception):
    pass


class Pen(object):
    def __init__(self, x1, y1, x2=None, y2=None, top=0):
        self.x1 = x1
        self.y1 = y1
        self.top = top
        if x2 is None:
            self.x2 = iop.screenWidth()
        else:
            self.x2 = x2
        if y2 is None:
            self.y2 = iop.screenHeight()
        else:
            self.y2 = y2

    def skip(self, x, y):
        self.x1 += x
        self.y1 += y

    def topPrint(self, x, y, fmt, bgcolour, fgcolour):
        if self.y1 < self.top:
            self.x1 += len(fmt)
        else:
            #defaultbg = defaultBG()
            iop.screenPrint(x, y - self.top, fmt, bgcolour, fgcolour)
            # libtcod.console_set_default_background(0, bgcolour)
            # libtcod.console_set_default_foreground(0, fgcolour)
            # libtcod.console_print(0, x, y - self.top, fmt)
            #
            # libtcod.console_set_default_background(0, defaultbg)

    def write(self, input, bgcolour=iop.defaultBG()):
        if len(input) > 0 and input[0] == '"':
            self.writeString(input, bgcolour)
        else: self.write2(input, bgcolour)

    def writeString(self, input, bgcolour):
        if bgcolour != iop.defaultBG():
            stringCol = iop.light_green
        else:
            stringCol = iop.dark_green

        wordList = input.split(' ')
        self.write2(wordList[0], bgcolour, stringCol)

        if len(wordList) > 1:
            for i in wordList[1:]:
                self.write2(' ', bgcolour)
                self.write2(i, bgcolour, stringCol)

    def write2(self, input, bgcolour=iop.defaultBG(), fgcolour=iop.defaultFG()):
        lineSpaceLeft = self.x2 - self.x1
        inputLength = len(input)
        if inputLength < lineSpaceLeft:
            self.topPrint(self.x1, self.y1, input, bgcolour, fgcolour)
            self.x1 += len(input)
        elif self.y1 - self.top < self.y2:

            if inputLength < iop.screenWidth():
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


    def writeOffset(self, input, x, y):
        self.x1 += x
        self.y1 += y
        self.write(input)

    def writeNL(self):
        if self.y1 - self.top + 1 != self.y2:
            self.y1 += 1
            self.x1 = 0
        else: raise windowBorderException




