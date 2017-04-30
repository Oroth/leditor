import funobj as fo
import iop
import copy

class Cell(fo.FuncObject):
    def __init__(self, character=' ', characterReference = 0, lineItemNodeRef=None,
                 bgColour=iop.defaultBG(), fgColour=iop.defaultFG()):
        self.character = character
        self.characterReference = characterReference
        self.lineItemNodeReference = lineItemNodeRef
        self.bgColour = bgColour
        self.fgColour = fgColour

defaultCell = Cell()
defaultScreenRow = [Cell(bgColour=iop.black, fgColour=iop.white) for x in xrange(0, 120)]

def createBlank(maxx, maxy, bgColour=iop.defaultBG(), fgColour=iop.defaultFG()):
    return [[Cell(bgColour=bgColour, fgColour=fgColour) for x in xrange(0, maxx)] for y in xrange(0, maxy)]


def fnPutNodeOnImage(image, x, y, text):
    newImage = [list(line) for line in image]
    for cdx, c in enumerate(text):
        #if x < maxx:
        (newImage[y][x+cdx]).character = c
        #(image[y][x]).characterReference = cdx
        #(image[y][x]).lineItemNodeReference = lineItemNodeRef
        #(image[y][x]).bgColour = bgcol
        #(image[y][x]).fgColour = fgcol
        #x += 1

    return newImage

def putNodeOnImage(image, x, y, text, lineItemNodeRef, bgcol, fgcol):
    maxx = len(image[0])
    maxy = len(image)
    for cdx, c in enumerate(text):
        if x < maxx:
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

def overlayTextOnImage(bottomImage, x, y, text):
    for cdx, c in enumerate(text):
        (bottomImage[y][x+cdx]).character = c

def overlayImage(bottomImage, x, y, topImage):
    maxx = len(bottomImage[0])
    for lidx, line in enumerate(topImage):
        for cdx, cell in enumerate(line):
            if x+cdx < maxx:
                bottomImage[y+lidx][x+cdx] = cell

def createImageFromStringList(lst, maxx, maxy):
    image = createBlank(maxx, maxy)

    for idx, string in enumerate(lst[:maxy]):
        # temp hack [:-1] to remove newlines read in from file, need to move to read section
        stringMinusNewLine = string[:-1] if string[-1] == '\n' else string
        stringWithLimit = stringMinusNewLine[:maxx]
        putNodeOnImage(image, 0, idx, stringWithLimit, None, iop.black, iop.white)

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

# def printToScreen(image, posx, posy):
#     maxy = len(image) - 1
#     maxx = len(image[0]) - 1
#
#     for x in xrange(maxx):
#         for y in xrange(maxy):
#             cell = image[y][x]
#             iop.screenPrint(posx + x, posy + y, cell.character, cell.bgColour, cell.fgColour)
