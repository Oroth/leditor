__author__ = 'chephren'

import TNode
import libtcodpy as libtcod

def createBlank(maxx, maxy):
    return [[' ' for x in range(0, maxx)] for x in range(0, maxy)]

def addText(image, x, y, text):
    newImage = [list(row) for row in image]

    for i in text:
        newImage[y][x] = i
        x += 1

    return newImage

def printToScreen(image):
    maxy = len(image) - 1
    maxx = len(image[0]) - 1

    for x in xrange(0, maxx):
        for y in xrange(0, maxy):

            libtcod.console_print(0, x, y, image[y][x])

# convert symbol list into a print-structure
# (text (line indent (symbols)) (line indent (symbols)) ...)
# symbols example: [leftParen '+' '1' '2' rightParen]
def makeSimplePrintList(lst, maxx):
    printList = []
    newLine = []
    x = 0
    y = 0

    for i in lst:
        if x + len(i) >= maxx:
            printList.append([0, newLine])
            y += 1
            x = 0
            newLine = []

        newLine.append(i)
        x += len(i)

    printList.append([0, newLine])

    return printList



def simpleBufferPrint(buffer, maxx):
    return

# draw entire lst to window
def drawPrintListToFakeWin(printList):
    image = createBlank(50, 256)
    y = 0

    #def drawCycle(lst, image):
    for line in printList:
        x = line[0]
        for symbol in line[1]:
            image = addText(image, x, y, symbol)
            x += len(symbol)
        y += 1

    return image

def sliceFakeWindow(fakeWindow, topline, maxHeight):
    return fakeWindow[topline:topline+maxHeight]


class lineItemNode(TNode.FuncObject):
    def __init__(self, nodeReference, parenSymbol=None, isCursor=False):
        self.nodeReference = nodeReference
        self.isCursor = isCursor
        self.parenSymbol = parenSymbol

    def nodeToString(self):
        if self.parenSymbol is not None:
            return self.parenSymbol
        else:
            return self.nodeReference.child

class lineListNode(TNode.FuncObject):
    def __init__(self, lineNumber, indent, nodeList=[]):
        self.lineNumber = lineNumber
        self.indent = indent
        self.nodeList = list(nodeList)
        #self.startNode = startNode
        #self.endNode = endNode
        #self.isCursor = isCursor

    #def __str__(self):
       # return "(lineListNode " + str(self.indent) + " " + str(self.startNode) + ")"

    def addLineItem(self, nodeReference, parenSymbol=None, isCursor=False):
        self.nodeList += lineItemNode(nodeReference, parenSymbol, isCursor)



#    def nodeToString(self):
#        def drawr(node):
#            curString = ""
#            if node.isSubNode():
#                curString = "(" + drawr(node.child) + ")"
#            else:
#                curString = node.child
#
#            if node == self.endNode:
#                return curString
#            elif node.next:
#                rest = drawr(node.next)
#                return curString + " " + rest
#            else:
#                return curString
#
#        return drawr(self.startNode)



def drawLineList(lineList):
    image = createBlank(50, 256)
    y = 0

    for line in lineList:
        x = line.indent
        y = line.lineNumber

        for item in line.nodeList:
            text = item.nodeToString()
            if text == ')':
                x -= 1
            image = addText(image, x, y, text)
            x += len(text)
            if text != '(':
                x += 1

    return image

def createStucturalLineIndentList(buffer):

    def prepareList(node):
        lineList = []
        currentLineNumber = 0

        while node:
            if node.isSubNode():
                newLineItems = [(lineItemNode(node, '('))]
                newLineItems.extend(buildLineItems(node.child))
                newLineItems.append(lineItemNode(node, ')'))
            else:
                newLineItems = [lineItemNode(node)]
            newLineNode = lineListNode(currentLineNumber, 0, newLineItems)
            lineList.append(newLineNode)
            currentLineNumber = currentLineNumber + 1
            node = node.next

        return lineList

    def buildLineItems(node):
        newLineItems = []
        if node.isSubNode():
            #newLineItems = [lineItemNode(node, '('), buildLineItems(node.child), lineItemNode(node, ')')]
            newLineItems.append(lineItemNode(node, '('))
            newLineItems.extend(buildLineItems(node.child))
            newLineItems.append(lineItemNode(node, ')'))
        else:
            newLineItems = [lineItemNode(node)]
            #newLineItems.append(lineItemNode(node.child)

        if node.next:
            newLineItems.extend(buildLineItems(node.next))
            return newLineItems
        else:
            return newLineItems

    return prepareList(buffer.view)

#    def drawChild(node, nesting, parentCol=libtcod.black):
#
#        if node == buffer.cursor:
#            bgcolour = hlcol
#        else:
#            bgcolour = parentCol
#
#
#        if node.isSubNode():
#
#            pen.write('(', bgcolour)
#            drawr(node.child, nesting, bgcolour)
#            pen.write(')', bgcolour)
#
#        elif node.child is None:
#            pen.write('()', bgcolour)
#
#        else:
#            output = reader.to_string(node.child)
#
#            if node == self.buffer.cursor and self.editing:
#                self.cellEditor.draw(pen)
#            else:
#                pen.write(output, bgcolour)
#
#
#    def drawr(node, nesting, parentCol=libtcod.black, reindent=False):
#
#        try:
#            if self.zippedNodes[node.nodeID]:
#                pen.write("...", hlcol if node == self.buffer.cursor else parentCol)
#                return
#        except KeyError: pass
#
#        drawChild(node, nesting + 1, parentCol)
#        #reindent = False
#
#        if node.next and node.next.next:
#            for i in node.next:
#                if i.isSubNode():
#                    for subi in i.child:
#                        if subi.isSubNode(): reindent = True
#
#
#        if node.next:
#            if indent and reindent:
#                newNode = lineListNode(currentLineNumber, (2*nesting), node)    #end
#                lineList += newNode
#                pen.write(' ' * (2 * nesting), parentCol)
#
#            # try to avoid hiding the cursor in a cell editor
#            #elif node == self.buffer.cursor and self.editing:
#            #    pen.skip(1, 0)
#            else:
#                pen.write(' ', parentCol)
#
#            drawr(node.next, nesting, parentCol, reindent)
#
#    if self.buffer.view.isSubNode():
#        drawChild(self.buffer.view, 1)
#    else:
#        pen.write(str(self.buffer.view.child))

# convert list to print-instructions

# print list-section (window, top-row, window-height)

# draw first x lines on window
# draw after first x lines to window
# draw around cursor

# calculate cursor line position
#

if __name__ == '__main__':
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

    lst = ['some', 'text', ['code', 'words'], 'to', 'write']


    #printLst = makeSimplePrintList(lst, SCREEN_WIDTH)
    #fakeWin = drawPrintListToFakeWin(printLst)


    tree = TNode.createTreeFromSexp(lst)
    buff = TNode.Buffer(tree)
    lineList = createStucturalLineIndentList(buff)
    fakeWin = drawLineList(lineList)
    # draw(lst)
    # draw((make-screen lst, cursorAddress, topRowNum))

    finalWin = sliceFakeWindow(fakeWin, 0, SCREEN_HEIGHT)
    libtcod.console_clear(0)

    #blankImage = createBlank(SCREEN_WIDTH, SCREEN_HEIGHT)
    #writtenImage = addText(blankImage, 3, 3, "some text")
    #printToScreen(writtenImage)

    printToScreen(finalWin)
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(libtcod.KEY_RELEASED)

