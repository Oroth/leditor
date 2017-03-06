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

def setCellColour(image, x, y, bgcol, fgcol):
    (image[y][x]).bgColour = bgcol
    (image[y][x]).fgColour = fgcol

def overlayLinesOnImage(bottomImage, y, topImage):
    for line in topImage:
        bottomImage[y] = line
        y += 1

def createImageFromStringList(lst, maxx, maxy):
    image = createBlank(maxx, maxy)

    for idx, string in enumerate(lst[:maxy]):
        # temp hack [:-1] to remove newlines read in from file, need to move to read section
        # also need constraint on overruning line length [:maxx]
        putNodeOnImage(image, 0, idx, string[:-1], None, iop.black, iop.white)

    return image

def stringToImage(text, maxx, maxy, bgCol=iop.defaultBG(), fgCol=iop.defaultFG()):
    image = createBlank(maxx, maxy)

    if len(text) > 0:
        textList = [text[start:start+maxx] for start in xrange(0, len(text), maxx)]
    else:
        textList = [' ']

    for y in range(0, min(maxy, len(textList))):
        putNodeOnImage(image, 0, y, textList[y], None, bgCol, fgCol)
    return image

def printToScreen(image, posx, posy):
    maxy = len(image) - 1
    maxx = len(image[0]) - 1

    for x in xrange(maxx):
        for y in xrange(maxy):
            cell = image[y][x]
            iop.screenPrint(posx + x, posy + y, cell.character, cell.bgColour, cell.fgColour)
