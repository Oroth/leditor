
from iop_libtcod import *
from iop_pyglet import *


import pyglet
pyglet.lib.load_library('avbin')
pyglet.have_avbin=True


white = Colour(255, 255, 255)
black = Colour(0, 0, 0)
defaultBG = black
defaultFG = white

import screen


light_grey = Colour(159,159,159)
light_green= Colour(114,255,114)
light_sky = Colour(114,219,255)
light_purple = Colour(219,114,255)
azure = Colour(0,127,255)
grey = Colour(127,127,127)
dark_green = Colour(0,191,0)
dark_red = Colour(191,0,0)
darker_green = Colour(0,127,0)
darker_sky = Colour(0,95,127)


class Application(IOApplication):
    def __init__(self, screenCols, screenRows, bgcol=defaultBG, fgcol=defaultFG):
        super(Application, self).__init__(screenCols, screenRows, bgcol, fgcol)

        pyglet.options['audio'] = ('directsound', 'silent')
        self.screenGrid = screen.createBlank(screenCols, screenRows)

    def playMedia(self):
        source = pyglet.media.load('Front Line Assembly - Caustic Grip - 01 - Resist.mp3')
        source.play()


    def screenPrint(self, x, y, cell):
        if self.screenGrid[y][x] == cell:
            return

        self.screenGrid[y][x] = cell
        super(Application, self).screenPrint(x, y, cell)
