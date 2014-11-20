__author__ = 'chephren'

import TNode
import libtcodpy as libtcod
import utility
import reader

class Cell(TNode.FuncObject):
    def __init__(self, character=' ', nodeReference=None, bgColour=utility.defaultBG(), fgColour=utility.defaultFG()):
        self.character = character
        self.nodeReference = nodeReference
        self.bgColour = bgColour
        self.fgColour = fgColour

def createBlank(maxx, maxy):
    return [[Cell() for x in range(0, maxx)] for x in range(0, maxy)]

def putNodeOnImage(image, x, y, text, node, bgcol):
    newImage = [list(row) for row in image]

    for i in text:
        (newImage[y][x]).character = i
        (newImage[y][x]).nodeReference = node
        (newImage[y][x]).bgColour = bgcol
        x += 1

    return newImage

def printToScreen(image):
    maxy = len(image) - 1
    maxx = len(image[0]) - 1

    for x in xrange(0, maxx):
        for y in xrange(0, maxy):
            cell = image[y][x]
            libtcod.console_set_default_background(0, cell.bgColour)
            libtcod.console_set_default_foreground(0, cell.fgColour)
            libtcod.console_print(0, x, y, cell.character)


# ======================== Creating the List =======================================================

def sliceFakeWindow(fakeWindow, topline, maxHeight):
    return fakeWindow[topline:topline+maxHeight]


class lineItemNode(TNode.FuncObject):
    def __init__(self, nodeReference, text=None, isCursor=False, stringSplit=None):
        self.nodeReference = nodeReference
        if text is None:
            self.text = reader.to_string(nodeReference.child)
        else:
            self.text = text
        self.isCursor = isCursor
        self.stringSplit = stringSplit

    def nodeToString(self):
        return self.text
        #if self.parenSymbol is not None:
            #return self.parenSymbol
        #else:
            #return self.nodeReference.child
            #return reader.to_string(self.nodeReference.child)

class lineListNode(TNode.FuncObject):
    def __init__(self, lineNumber, indent, nodeList=[]):
        self.lineNumber = lineNumber
        self.indent = indent
        self.nodeList = list(nodeList)

    #def __str__(self):
       # return "(lineListNode " + str(self.indent) + " " + str(self.startNode) + ")"

    def addLineItem(self, nodeReference, parenSymbol=None, isCursor=False):
        self.nodeList += lineItemNode(nodeReference, parenSymbol, isCursor)


def drawLineList(lineList):
    image = createBlank(80, 512)
    hlcol = libtcod.azure
    standardBG = utility.defaultBG()

    for line in lineList:
        x = line.indent
        y = line.lineNumber

        if line.indent > 0:
            firstItem = line.nodeList[0]
            if firstItem.isCursor:
                bgcol = hlcol
            else:
                bgcol = standardBG
            indentString = ''.join([' ' for i in xrange(line.indent)])
            image = putNodeOnImage(image, 0, y, indentString, firstItem, bgcol)

        for item in line.nodeList:
            if item.isCursor:
                bgcol = hlcol
            else:
                bgcol = standardBG

            text = item.nodeToString()
            if text == ')':
                x -= 1

            image = putNodeOnImage(image, x, y, text, item.nodeReference, bgcol)
            x += len(text)

            if text != '(' and item != line.nodeList[-1]:
                image = putNodeOnImage(image, x, y, ' ', item.nodeReference, bgcol)
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

            # reindenting rule:
            # if there are two or more expressions after the current expression
            # and one of those expressions is complex - is a sexp with one subnested sexp
            # then start a new line and increase the indentation
            # Q: should this only apply at the start?

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



def createStucturalLineIndentList3(buffer):

    def isComplex(node):
        if node.next:
            for i in node:
                if i.isSubNode():
                    for subi in i.child:
                        if subi.isSubNode(): return True

        return False

    def recur(node, nesting, isParentCursor=False, indent=False):

        if node == buffer.cursor:
            isCursor = True
        else:
            isCursor = isParentCursor

        if node.isSubNode():
            ret = [lineItemNode(node, '(', isCursor)]
            ret.extend(recur(node.child, nesting, isCursor))
            ret.append(lineItemNode(node, ')', isCursor))
        elif node.child is None:
            ret = [lineItemNode(node, '(', isCursor), lineItemNode(node, ')', isCursor)]
        else:
            #ret = [lineItemNode(node, node.child, isCursor)]
            ret = [lineItemNode(node, None, isCursor)]

        reindent = False
        if node.next and isComplex(node.next):
            reindent = True

        # new rule: if only two values (exp1 exp2) and exp2 is very complex, indent anyway
        if node.next and node.next.isSubNode() and isComplex(node.next.child):
            reindent = True

        if node.next:
            if indent:
                ret.append(lineListNode(0, nesting))
                ret.extend(recur(node.next, nesting, isCursor, indent=True))
            elif reindent:        # can only apply to the first expression
                ret.append(lineListNode(0, nesting+1))
                ret.extend(recur(node.next, nesting+1, isCursor, indent=True))
            else:
                ret.extend(recur(node.next, nesting, isCursor, indent))

        return ret

    def splitStringAcrossLines(string, firstBoundary, remainingBoundary):
        stringList = []
        lastSpaceFirstLine = string.rfind(' ', 0, firstBoundary)
        if lastSpaceFirstLine != -1:
            stringList.append(string[:lastSpaceFirstLine])
            curLineStart = lastSpaceFirstLine + 1
        else:
            stringList.append('')
            curLineStart = 0

        curLineFind = string.rfind(' ', curLineStart, remainingBoundary)

        while curLineFind != -1 and curLineStart+remainingBoundary < len(string):
            #curLineEnd = curLineStart + curLineFind
            curLineEnd = curLineFind
            stringList.append(string[curLineStart:curLineEnd])
            curLineStart = curLineEnd+1
            curLineFind = string.rfind(' ', curLineStart, curLineStart+remainingBoundary)

        stringList.append(string[curLineStart:])

        return stringList



    def unflatten(stream):
        lines = [lineListNode(0, 0)]
        currentLineNumber = 1
        currentLineLength = 0
        currentLineIndent = 0
        for i in stream:
            if isinstance(i, lineListNode):
                lines.append(lineListNode(currentLineNumber, i.indent))
                currentLineNumber += 1
                currentLineLength = i.indent
                currentLineIndent = i.indent
            else:
                itemNodeLength = len(i.nodeToString()) + 1  ## technically parens will only be 1 char
                if (currentLineLength + itemNodeLength) > 80: ## Line Width
                    lineLengthLeft = 80 - currentLineLength

                    if isinstance(i.nodeReference.child, str):
                        stringList = splitStringAcrossLines(i.text, lineLengthLeft, 80)
                        if stringList[0] != '':
                            currentLineNode = lineItemNode(i.nodeReference, stringList[0], i.isCursor, 'start')
                            lines[-1].nodeList.append(currentLineNode)

                        for string in stringList[1:]:
                            currentLineNode = lineItemNode(i.nodeReference, string, i.isCursor, 'start')
                            lines.append(lineListNode(currentLineNumber, 0))
                            currentLineNumber += 1

                            lines[-1].nodeList.append(currentLineNode)

                        currentLineLength = len(currentLineNode.text)

#                        lastSpace = i.text.rfind(' ', 0, lineLengthLeft)
#                        if lastSpace != -1:
#                            start = i.text[:lastSpace]
#                            end = i.text[lastSpace+1:]
#                            currentLineNode = lineItemNode(i.nodeReference, start, i.isCursor, 'start')
#                            newlineNode = lineItemNode(i.nodeReference, end, i.isCursor, 'end')
#                            lines[-1].nodeList.append(currentLineNode)
#                        else:   ## need to check at some point about carrying across multiple lines
#                            newlineNode = lineItemNode(i.nodeReference, i.text, i.isCursor)
                    #else:
                    #    newlineNode = i
                    else:
                        lines.append(lineListNode(currentLineNumber, 0))
                        currentLineNumber += 1
                        currentLineLength = 0

                        lines[-1].nodeList.append(i)
                        currentLineLength += len(i.nodeToString())

                else:
                    lines[-1].nodeList.append(i)
                    currentLineLength += itemNodeLength

        return lines

    lineStream = recur(buffer.view, isParentCursor=False, nesting=0)
    lineList = unflatten(lineStream)
    return lineList


if __name__ == '__main__':
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    LIMIT_FPS = 20


    #############################################
    # Initialization & Main Loop
    #############################################

    libtcod.console_set_custom_font('fonts/terminal8x14_gs_ro.png',
                libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'List-editor', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    libtcod.console_set_background_flag(0, libtcod.BKGND_SET)
    libtcod.console_set_default_foreground(0, libtcod.white)

    #lst = ['some', 'text', ['code', 'words'], 'to', 'write']
    lst = [[reader.Symbol('function'), ['let', ['x', 15], ['y', 10], \
                                        ['+', ['*', 'x', 'x'], ['*', 'y', 'y'], \
                                        "This is a very long string designed" \
                                        ,"Yetanother fairly long test string to see if it workslikepromised" \
                        ,"Finally a super long string that won't fit on two lines, let alone one, just to make"
                        "sure it works like the good lord intended it should, if this is long enough"]]]]

#    lst = [["one very long string indeed unencumbered by any other strings in the"
#           ,"vicinity shall we say, but if this one grows exponentially, terribly, indeed horribly"
#           ", unstoppably, and revoltingly without rhyme or reason, folly or madness only wonderment"]]

    tree = TNode.createTreeFromSexp(lst)
    buff = TNode.Buffer(tree)
    buff.cursor = buff.cursor.child
    lineList = createStucturalLineIndentList3(buff)
    fakeWin = drawLineList(lineList)

    finalWin = sliceFakeWindow(fakeWin, 0, SCREEN_HEIGHT)
    libtcod.console_clear(0)

    printToScreen(finalWin)
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(libtcod.KEY_RELEASED)

