import funobj as fo
import iop


class Cell(fo.FuncObject):
    def __init__(self, character=' ', characterReference = 0, lineItemNodeRef=None,
                 bgColour=iop.defaultBG(), fgColour=iop.defaultFG()):
        self.character = character
        self.characterReference = characterReference
        self.lineItemNodeReference = lineItemNodeRef
        self.bgColour = bgColour
        self.fgColour = fgColour


def createBlank(maxx, maxy, bgColour=iop.defaultBG(), fgColour=iop.defaultFG()):
    return [[Cell(bgColour=bgColour, fgColour=fgColour) for x in range(0, maxx)] for x in range(0, maxy)]


def putNodeOnImage(image, x, y, text, lineItemNodeRef, bgcol, fgcol):
    for cdx, c in enumerate(text):
        (image[y][x]).character = c
        (image[y][x]).characterReference = cdx
        (image[y][x]).lineItemNodeReference = lineItemNodeRef
        (image[y][x]).bgColour = bgcol
        (image[y][x]).fgColour = fgcol
        x += 1


def printToScreen(image, posx, posy):
    maxy = len(image) - 1
    maxx = len(image[0]) - 1

    for x in xrange(maxx):
        for y in xrange(maxy):
            cell = image[y][x]
            iop.screenPrint(posx + x, posy + y, cell.character, cell.bgColour, cell.fgColour)


