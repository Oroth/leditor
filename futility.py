__author__ = 'chephren'

import TNode
import libtcodpy as libtcod
import utility
import reader

class Cell(TNode.FuncObject):
    def __init__(self, character=' ', lineItemNodeRef=None, bgColour=utility.defaultBG(), fgColour=utility.defaultFG()):
        self.character = character
        self.lineItemNodeReference = lineItemNodeRef
        self.bgColour = bgColour
        self.fgColour = fgColour

def createBlank(maxx, maxy, bgColour=utility.defaultBG(), fgColour=utility.defaultFG()):
    return [[Cell(bgColour=bgColour, fgColour=fgColour) for x in range(0, maxx)] for x in range(0, maxy)]

# Functional version
#def putNodeOnImage(image, x, y, text, node, bgcol):
#    newImage = [list(row) for row in image]
#
#    for i in text:
#        (newImage[y][x]).character = i
#        (newImage[y][x]).nodeReference = node
#        (newImage[y][x]).bgColour = bgcol
#        (newImage[y][x]).bgColour = bgcol
#        x += 1
#
#    return newImage

def putNodeOnImage2(image, x, y, text, lineItemNodeRef, bgcol, fgcol):

    for i in text:
        (image[y][x]).character = i
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
            libtcod.console_set_default_background(0, cell.bgColour)
            libtcod.console_set_default_foreground(0, cell.fgColour)
            libtcod.console_print(0, posx+x, posy+y, cell.character)


# ======================== Creating the List =======================================================

def sliceFakeWindow(fakeWindow, topline, maxHeight):
    return fakeWindow[topline:topline+maxHeight]


class lineItemNode(TNode.FuncObject):
    def __init__(self, nodeReference, nodeAddress, text=None, isCursor=False, stringSplit=None):
        self.nodeReference = nodeReference
        if text is None:
            self.text = reader.to_string(nodeReference.child)
        else:
            self.text = str(text)
        self.isCursor = isCursor
        self.stringSplit = stringSplit
        self.printRule = None
        self.highlightIndex = None
        self.nodeAddress = nodeAddress

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

    #def addLineItem(self, nodeReference, parenSymbol=None, isCursor=False):
    #    self.nodeList += lineItemNode(nodeReference, parenSymbol, isCursor)


def drawLineList(lineList, winWidth, winHeight, standardBG, standardFG, hlcol=libtcod.azure):
    image = createBlank(winWidth, winHeight, standardBG, standardFG)
    #hlcol = libtcod.azure
    #standardBG = utility.defaultBG()
    #standardFG = utility.defaultFG()

    prevLine = None
    y = 0
    for line in lineList[:winHeight]:
        x = line.indent
        #y = line.lineNumber

        # highlight the indented space if it is part of the cursor
        if line.indent > 0:
            firstItem = line.nodeList[0]
            if firstItem.isCursor and prevLine and prevLine.nodeList[-1].isCursor:
                bgcol = hlcol
            else:
                bgcol = standardBG
            indentString = ''.join([' ' for i in xrange(line.indent)])
            #image = putNodeOnImage(image, 0, y, indentString, firstItem, bgcol)
            putNodeOnImage2(image, 0, y, indentString, firstItem, bgcol, standardFG)

        prevLine = line

        prevItem = None
        for item in line.nodeList:

            #Add space between symbols
            if prevItem and prevItem.nodeToString() != '(' and item.nodeToString() != ')':
                if item.isCursor and prevItem.isCursor:
                    bgcol = hlcol
                else:
                    bgcol = standardBG
                putNodeOnImage2(image, x, y, ' ', item, bgcol, standardFG)
                x += 1


            if item.isCursor:
                bgcol = hlcol
            else:
                bgcol = standardBG

            if isinstance(item.nodeReference.child, reader.Symbol):
                fgcol = standardFG
            elif isinstance(item.nodeReference.child, str) and item.printRule != 'cellEditorNonString':
                fgcol = libtcod.light_green
            elif isinstance(item.nodeReference.child, int):
                fgcol = libtcod.light_sky
            else:
                fgcol = standardFG

            text = item.nodeToString()
            #if text == ')' and prevItem and prevItem.text != '(':
            #    x -= 1

            #image = putNodeOnImage(image, x, y, text, item.nodeReference, bgcol)
            putNodeOnImage2(image, x, y, text, item, bgcol, fgcol)
            if item.printRule in [ 'cellEditorString', 'cellEditorNonString']:
                (image[y][x+item.highlightIndex]).bgColour = libtcod.azure
                x += 1
            x += len(text)

#            #Add space between symbols
#            if text != '(' and item != line.nodeList[-1]:
#                #image = putNodeOnImage(image, x, y, ' ', item.nodeReference, bgcol)
#                putNodeOnImage2(image, x, y, ' ', item, bgcol, fgcol)
#                x += 1

            prevItem = item

        y += 1

    return image


def createStucturalLineIndentList(editor, winWidth, winHeight):

    def isComplex(node):
        if node.next:
            for i in node:
                if i.isSubNode() and not (i.nodeID in editor.zippedNodes and editor.zippedNodes[i.nodeID]):
                    for subi in i.child:
                        if subi.isSubNode() and \
                           not (subi.nodeID in editor.zippedNodes and editor.zippedNodes[subi.nodeID]):
                            return True

        return False

    # Everything is printed without linebreaks
    def recurHorizontal(ret, node, newAddress, nesting, isParentCursor=False, indent=False, topNode=False):
        newAddress[-1] += 1
        if node.next:
            ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent))

        return ret

    def recurVerticalTemplate(ret, node, newAddress, nesting, isParentCursor=False, indent=False, topNode=False,
                              reindent=False):
        if node.next:
            newAddress[-1] += 1
            if indent:
                ret.append(lineListNode(0, nesting))
                ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent=True))
            elif reindent:        # can only apply to the first expression
                ret.append(lineListNode(0, nesting+1))
                ret.extend(recur(node.next, newAddress, nesting+1, isParentCursor, indent=True))
            else:
                ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent))

        return ret

    def recurCode(ret, node, newAddress, nesting, isParentCursor=False, indent=False, topNode=False):
        reindent = False
        if node.next and isComplex(node.next):
            reindent = True

        # new rule: if only two values (exp1 exp2) and exp2 is very complex, indent anyway
        if node.next and node.next.isSubNode() and isComplex(node.next.child):
            reindent = True

        return recurVerticalTemplate(ret, node, newAddress, nesting, isParentCursor, indent, topNode, reindent)

    # Add linebreaks for everything apart from the last sexp
    def recurVertical(ret, node, newAddress, nesting, isParentCursor=False, indent=False, topNode=False):
        reindent = False
        if node.next and node.next.isSubNode():
            reindent = True

        return recurVerticalTemplate(ret, node, newAddress, nesting, isParentCursor, indent, topNode, reindent)

    def recur(node, address, nesting, isParentCursor=False, indent=False, topNode=False):
        newAddress = list(address)

        if node == editor.buffer.cursor:
            isCursor = True
        else:
            isCursor = isParentCursor

        if node.nodeID in editor.zippedNodes and editor.zippedNodes[node.nodeID]:
            ret = [lineItemNode(node, address, '...', isCursor)]
            return ret

        if node == editor.buffer.cursor and editor.editing:
            # slightly hacky, isCursor is technically True, but we call it false to stop it
            # from highlighting the entire node. need to re-engineer the rules really
            ret = [lineItemNode(node, address, editor.cellEditor.getContentAsString(), False)]
            if editor.cellEditor.isString:
                ret[0].printRule = 'cellEditorString'
                ret[0].highlightIndex = editor.cellEditor.index + 1
            else:
                ret[0].printRule = 'cellEditorNonString'
                ret[0].highlightIndex = editor.cellEditor.index
        elif node.isSubNode():
            ret = [lineItemNode(node, address, '(', isCursor)]
            subAddress = list(newAddress)
            subAddress.append(0)
            ret.extend(recur(node.child, subAddress, nesting, isCursor))
            ret.append(lineItemNode(node, address, ')', isCursor))
        elif node.child is None:
            ret = [lineItemNode(node, address, '(', isCursor),
                   lineItemNode(node, address, ')', isCursor)]
        else:
            #ret = [lineItemNode(node, node.child, isCursor)]
            ret = [lineItemNode(node, address, None, isCursor)]

        # code editor, needs to go with the code editor code
        try:
            if editor.revealedNodes[node]:
                ret.append(lineItemNode(node, address, '=>', isCursor))
                ret.append(lineItemNode(node, address, reader.to_string(editor.nodeValues[node]), isCursor))
        except KeyError: pass
        except AttributeError: pass


        if topNode:
            return ret

        modeRet = recurMode(ret, node, newAddress, nesting, isParentCursor, indent)

        return modeRet

#        reindent = False
#        if node.next and isComplex(node.next):
#            reindent = True
#
#        # new rule: if only two values (exp1 exp2) and exp2 is very complex, indent anyway
#        if node.next and node.next.isSubNode() and isComplex(node.next.child):
#            reindent = True
#
#        if node.next:
#            newAddress[-1] += 1
#            if indent:
#                ret.append(lineListNode(0, nesting))
#                ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent=True))
#            elif reindent:        # can only apply to the first expression
#                ret.append(lineListNode(0, nesting+1))
#                ret.extend(recur(node.next, newAddress, nesting+1, isParentCursor, indent=True))
#            else:
#                ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent))
#
#        return ret

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
        bottomNodeFound = False
        cursorTopLine = None
        cursorBottomLine = None

        newTopLine = editor.topLine

        for i in stream:

            if isinstance(i, lineListNode):
                if editor.drawMode == 'cursor':
                    if cursorTopLine is not None and cursorBottomLine is not None:
                        if cursorTopLine <= editor.topLine:
                            newTopLine = cursorTopLine - 1
                        elif cursorTopLine >= editor.topLine + winHeight:
                            newTopLine = cursorBottomLine - winHeight +1

                        if currentLineNumber >= newTopLine + winHeight:
                            break


                lines.append(lineListNode(currentLineNumber, i.indent))
                currentLineNumber += 1
                currentLineLength = i.indent
                currentLineIndent = i.indent
            else:


#                if i.nodeReference.nodeID == positionNode.nodeID:
#                    if nodeDescriptor == 'topNode':
#                        newTopLine = currentLineNumber
#                    elif nodeDescriptor == 'bottomNode':
#                        bottomNodeFound = True

                if i.isCursor:
                    if cursorTopLine is None:
                        cursorTopLine = currentLineNumber
                    cursorBottomLine = currentLineNumber

                itemNodeLength = len(i.nodeToString()) + 1  ## technically parens will only be 1 char
                if (currentLineLength + itemNodeLength) > winWidth:
                    lineLengthLeft = winWidth - currentLineLength

                    if isinstance(i.nodeReference.child, str):
                        stringList = splitStringAcrossLines(i.text, lineLengthLeft, winWidth)
                        if stringList[0] != '':
                            currentLineNode = lineItemNode(i.nodeReference, i.nodeAddress,
                                stringList[0], i.isCursor, 'start')
                            lines[-1].nodeList.append(currentLineNode)

                        for string in stringList[1:]:
                            currentLineNode = lineItemNode(i.nodeReference, i.nodeAddress,
                                string, i.isCursor, 'start')
                            lines.append(lineListNode(currentLineNumber, 0))
                            currentLineNumber += 1

                            lines[-1].nodeList.append(currentLineNode)

                        currentLineLength = len(currentLineNode.text)

                    else:
                        lines.append(lineListNode(currentLineNumber, 0))
                        currentLineNumber += 1
                        currentLineLength = 0

                        lines[-1].nodeList.append(i)
                        currentLineLength += len(i.nodeToString())

                else:
                    lines[-1].nodeList.append(i)
                    currentLineLength += itemNodeLength

        #check if we found the last line
        if cursorTopLine >= editor.topLine + winHeight:
            newTopLine = cursorBottomLine - winHeight +1

        return lines, newTopLine

    if editor.printingMode == 'code':
        recurMode = recurCode
    elif editor.printingMode == 'horizontal':
        recurMode = recurHorizontal
    elif editor.printingMode == 'vertical':
        recurMode = recurVertical

    lineStream = recur(editor.buffer.view, [0], nesting=0, isParentCursor=False, topNode=True)
    lineList, topLine = unflatten(lineStream)
    toppedLineList = lineList[topLine:]
    return toppedLineList


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
    lst = [[reader.Symbol('function'), ['let', ['x', 15], ['y', 10],
                                        ['+', ['*', 'x', 'x'], ['*', 'y', 'y'],
                                        "This is a very long string designed"
                                        ,"Yetanother fairly long test string to see if it workslikepromised"
                        ,"Finally a super long string that won't fit on two lines, let alone one, just to make"
                        "sure it works like the good lord intended it should, if this is long enough"]]]]

#    lst = [["one very long string indeed unencumbered by any other strings in the"
#           ,"vicinity shall we say, but if this one grows exponentially, terribly, indeed horribly"
#           ", unstoppably, and revoltingly without rhyme or reason, folly or madness only wonderment"]]

    tree = TNode.createTreeFromSexp(lst)
    buff = TNode.Buffer(tree)
    buff.cursor = buff.cursor.child
    lineList = createStucturalLineIndentList(buff, 50)
    fakeWin = drawLineList(lineList)

    finalWin = sliceFakeWindow(fakeWin, 0, SCREEN_HEIGHT)
    libtcod.console_clear(0)

    printToScreen(finalWin)
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(libtcod.KEY_RELEASED)

