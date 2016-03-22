__author__ = 'chephren'

import TNode
import iop
import reader

class Cell(TNode.FuncObject):
    def __init__(self, character=' ', characterReference = 0, lineItemNodeRef=None,
                 bgColour=iop.defaultBG(), fgColour=iop.defaultFG()):
        self.character = character
        self.characterReference = characterReference
        self.lineItemNodeReference = lineItemNodeRef
        self.bgColour = bgColour
        self.fgColour = fgColour

def createBlank(maxx, maxy, bgColour=iop.defaultBG(), fgColour=iop.defaultFG()):
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


class lineListNode(TNode.FuncObject):
    def __init__(self, lineNumber, indent, nodeList=[], parenAlignment=0):
        self.lineNumber = lineNumber
        self.indent = indent
        self.nodeList = list(nodeList)
        self.parenAlignment = parenAlignment



def drawLineList(lineList, winWidth, winHeight, colScheme, isActive):
    image = createBlank(winWidth, winHeight, colScheme.bgCol, colScheme.symbolCol)
    hlcol = colScheme.activeHiCol if isActive else colScheme.idleHiCol

    indentWidth = 2


    prevLine = None
    y = 0
    for line in lineList[:winHeight]:
        pa = line.parenAlignment
        #if pa > 0:
        #    print 'paddingAlign'
        totalLineIndent = line.indent * indentWidth + line.parenAlignment
        x = totalLineIndent

        #y = line.lineNumber

        # highlight the indented space if it is part of the cursor
        if line.indent > 0:
            firstItem = line.nodeList[0]
            if firstItem.isCursor and prevLine and prevLine.nodeList[-1].isCursor:
                bgcol = hlcol
            else:
                bgcol = colScheme.bgCol
            indentString = ''.join([' ' for i in xrange(totalLineIndent)])
            #image = putNodeOnImage(image, 0, y, indentString, firstItem, bgcol)
            putNodeOnImage2(image, 0, y, indentString, firstItem, bgcol, colScheme.symbolCol)

        prevLine = line

        prevItem = None
        for item in line.nodeList:

            #Add space between symbols
            if prevItem and prevItem.nodeToString() != '(' and item.nodeToString() != ')':
                if item.isCursor and prevItem.isCursor:
                    bgcol = hlcol
                else:
                    bgcol = colScheme.bgCol
                putNodeOnImage2(image, x, y, ' ', item, bgcol, colScheme.symbolCol)
                x += 1


            if item.isCursor:
                bgcol = hlcol
            else:
                bgcol = colScheme.bgCol

            if isinstance(item.nodeReference.child, reader.Symbol):
                fgcol = colScheme.symbolCol
            elif isinstance(item.nodeReference.child, str) and item.printRule != 'cellEditorNonString':
                fgcol = colScheme.stringCol
            elif isinstance(item.nodeReference.child, int):
                fgcol = colScheme.numberCol
            else:
                fgcol = colScheme.symbolCol

            text = item.nodeToString()

            # Truncate long strings (e.g. evaluation results)
            if len(text) >= winWidth:
                text = text[0:winWidth - 5] + '...'

            putNodeOnImage2(image, x, y, text, item, bgcol, fgcol)
            if item.printRule in [ 'cellEditorString', 'cellEditorNonString']:
                (image[y][x+item.highlightIndex]).bgColour = hlcol
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
    def recurHorizontal(ret, node, newAddress, nesting,
                        isParentCursor=False, indent=False, topNode=False, pa=0):
        newAddress[-1] += 1
        if node.next:
            ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent))

        return ret

    def recurVerticalTemplate(ret, node, newAddress, nesting, isParentCursor=False, indent=False, topNode=False,
                              reindent=False, pa=0):
        if node.next:
            newAddress[-1] += 1
            if indent:
                ret.append(lineListNode(0, nesting, parenAlignment=pa))
                ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent=True, pa=pa))
            elif reindent:        # can only apply to the first expression
                ret.append(lineListNode(0, nesting+1, parenAlignment=pa))
                ret.extend(recur(node.next, newAddress, nesting+1, isParentCursor, indent=True, pa=pa))
            else:
                ret.extend(recur(node.next, newAddress, nesting, isParentCursor, indent, pa=pa))

        return ret

    def recurCode(ret, node, newAddress, nesting,
                  isParentCursor=False, indent=False, topNode=False, pa=0):
        reindent = False
        #parenAlignment = 0

        if node.next:
            if node.next.nodeID in editor.zippedNodes and editor.zippedNodes[node.next.nodeID]:
                reindent = False
            elif isComplex(node.next):
                if node.isSubNode():
                    if node.child.isSubNode():
                        pa = 1
                    pa = 1
                    indent = True
                else:
                    reindent = True
            # new rule: if only two values (exp1 exp2) and exp2 is very complex, indent anyway
            elif node.next.isSubNode() and isComplex(node.next.child):
                if node.isSubNode():
                    if node.child.isSubNode():
                        pa = 1
                    #pa = 1
                    indent = True
                else:
                    reindent = True

        return recurVerticalTemplate(ret, node, newAddress, nesting, isParentCursor,
                                     indent, topNode, reindent, pa=pa)

    # Add linebreaks for everything apart from the last sexp
    def recurVertical(ret, node, newAddress, nesting,
                      isParentCursor=False, indent=False, topNode=False, pa=0):
        reindent = False
        if node.next and node.next.isSubNode():
            if node.isSubNode():
                if node.child.isSubNode():
                    pa += 1
                indent = True
            else:
                reindent = True

        return recurVerticalTemplate(ret, node, newAddress, nesting, isParentCursor,
                                     indent, topNode, reindent, pa)

    def recur(node, address, nesting, isParentCursor=False, indent=False, topNode=False, pa=0):
        newAddress = list(address)

        if node == editor.buffer.cursor:
            isCursor = True
        else:
            isCursor = isParentCursor


        if node.nodeID in editor.zippedNodes and editor.zippedNodes[node.nodeID] and editor.printingMode != 'help':
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
            ret.extend(recur(node.child, subAddress, nesting, isCursor, pa=pa))
            ret.append(lineItemNode(node, address, ')', isCursor))
        elif node.child is None:
            ret = [lineItemNode(node, address, '(', isCursor),
                   lineItemNode(node, address, ')', isCursor)]
        else:
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

        modeRet = recurMode(ret, node, newAddress, nesting, isParentCursor, indent, pa=pa)

        return modeRet


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


                lines.append(lineListNode(currentLineNumber, i.indent, parenAlignment=i.parenAlignment))
                currentLineNumber += 1
                currentLineLength = i.indent + i.parenAlignment
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
    elif editor.printingMode in ['vertical', 'help']:
        recurMode = recurVertical

    lineStream = recur(editor.buffer.view, [0], nesting=0, isParentCursor=False, topNode=True)
    lineList, topLine = unflatten(lineStream)
    toppedLineList = lineList[topLine:]
    return toppedLineList


