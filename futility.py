__author__ = 'chephren'
import iop
import reader
import buffer
import funobj as fo 

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

class ParseState(buffer.Buffer):
    def __init__(self, node, address, nesting=0, isCursor=False):
        self.nesting = nesting
        self.isCursor = isCursor
        self.newline = False        # While True will start a newline at each node
        self.reindent = False       # While true will increase the amount of nesting...
        self.parenAlignment = 0
        self.letSyntax = False
        super(ParseState, self).__init__(node, [0], address)

    def incNesting(self):
        return self.update('nesting', self.nesting+1)

    def reset(self, *lst):
        args = zip(lst, [False]*len(lst))
        return wrapper(self.updateList, args)

    def set(self, *lst):
        args = zip(lst, [True]*len(lst))
        return wrapper(self.updateList, args)

def wrapper(func, args):
    return func(*args)


class LineItemNode(fo.FuncObject):
    def __init__(self, ps, text=None, stringSplit=None):
        self.nodeReference = ps.cursor
        if text is None:
            self.text = reader.to_string(ps.cursor.child)
        else:
            self.text = str(text)
        self.isCursor = ps.isCursor
        self.stringSplit = stringSplit
        self.printRule = None
        self.highlightIndex = None
        self.nodeAddress = ps.cursorAdd

    @classmethod
    def fromParts(cls, nodeReference, nodeAddress, text=None, isCursor=False, stringSplit=None):
        ps = ParseState(nodeReference, nodeAddress, 0, isCursor)
        return cls(ps, text, stringSplit)

    def nodeToString(self):
        return self.text


class LineNode(fo.FuncObject):
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

    # filter lst?, flatten, filter lst?-
    def isComplex(node):
        if node.next:
            for i in node:
                if i.isSubNode() and not editor.nodeIsZipped(i):
                    for subi in i.child:
                        if subi.isSubNode() and not editor.nodeIsZipped(subi):
                            return True

        return False

    # Everything is printed without linebreaks
    def recurHorizontal(ret, ps):
        if ps.cursor.next:
            ret.extend(recur(ps.curNext()))
        return ret

    def recurVerticalTemplate(ret, parseState):
        if parseState.cursor.next:
            ps = parseState.curNext()

            if ps.newline:
                ret.append(LineNode(0, ps.nesting, parenAlignment=ps.parenAlignment))
                ret.extend(recur(ps))
            else:
                ret.extend(recur(ps))

        return ret


    def recurCode2(parseState):
        node = parseState.cursor

        if editor.nodeIsZipped(node.next):
            return parseState
        elif isComplex(node.next) or (node.next.isSubNode() and isComplex(node.next.child)):
            ps = parseState.set('newline')
            # if the first node is a list, assume it is part of a let-syntax, so we know not to reindent
            if node.isSubNode():
                return ps.update('parenAlignment', 1)
            else:
                return ps.incNesting()

        return parseState


    def recurCode(ret, parseState):
        node = parseState.cursor
        newline = parseState.newline
        reindent = False
        pa = parseState.parenAlignment

        if node.next:
            if editor.nodeIsZipped(node.next):
                pass
            elif isComplex(node.next) or (node.next.isSubNode() and isComplex(node.next.child)):
                newline = True
                # if the first node is a list, assume it is part of a let-syntax, so we know not to reindent
                if node.isSubNode():
                    pa = 1
                else:
                    reindent = True

        ps = parseState.updateList(
            ('newline', newline),
            ('parenAlignment', pa))

        ps2 = ps.incNesting() if reindent else ps

        return recurVerticalTemplate(ret, ps2)

    # Add linebreaks for everything apart from the last sexp
    def recurVertical(ret, parseState):
        node = parseState.cursor
        newline = parseState.newline
        reindent = parseState.reindent
        pa = parseState.parenAlignment


        if node.next and node.next.isSubNode():
            newline = True
            if node.isSubNode():
                pa = 1
            else:
                reindent = True

        ps = parseState.updateList(
            ('newline', newline),
            ('parenAlignment', pa))

        ps2 = ps.incNesting() if reindent else ps

        return recurVerticalTemplate(ret, ps2)

    def recur(parseState):

        if parseState.cursor == editor.buffer.cursor:
            ps = parseState.update('isCursor', True)
        else:
            ps = parseState

        if editor.nodeIsZipped(ps.cursor) and editor.printingMode != 'help':
            ret = [LineItemNode(ps, '...')]
            return ret

        if ps.cursor == editor.buffer.cursor and editor.editing:
            # slightly hacky, isCursor is technically True, but we call it false to stop it
            # from highlighting the entire node. need to re-engineer the rules really
            editingNode = LineItemNode(ps.reset('isCursor'), editor.cellEditor.getContentAsString())
            if editor.cellEditor.isString:
                editingNode.printRule = 'cellEditorString'
                editingNode.highlightIndex = editor.cellEditor.index + 1
            else:
                editingNode.printRule = 'cellEditorNonString'
                editingNode.highlightIndex = editor.cellEditor.index
            ret = [editingNode]

        elif ps.onSubNode():
            ret = [LineItemNode(ps, '(')]
            ret.extend(recur(ps.curChild().reset('newline', 'reindent')))
            ret.append(LineItemNode(ps, ')'))

        elif ps.cursor.child is None:
            ret = [LineItemNode(ps, '('),
                   LineItemNode(ps, ')')]

        else:
            ret = [LineItemNode(ps)]

        # code editor, needs to go with the code editor code
        try:
            if editor.revealedNodes[ps.cursor]:
                ret.append(LineItemNode(ps, '=>'))
                ret.append(LineItemNode(ps, reader.to_string(editor.nodeValues[ps.cursor])))
        except KeyError: pass
        except AttributeError: pass



        if parseState.cursor.next:
            modeps = recurCode2(parseState)
            # pass the original state to maintain the same cursor highlighting
            if modeps.newline:
                ret.append(LineNode(0,  modeps.nesting, parenAlignment= modeps.parenAlignment))

            ret.extend(recur(modeps.curNext()))

        return ret
        # modeRet = recurMode(ret, parseState)
        #
        # return modeRet


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
        lines = [LineNode(0, 0)]
        currentLineNumber = 1
        currentLineLength = 0
        currentLineIndent = 0
        bottomNodeFound = False
        cursorTopLine = None
        cursorBottomLine = None

        newTopLine = editor.topLine

        for i in stream:

            if isinstance(i, LineNode):
                if editor.drawMode == 'cursor':
                    if cursorTopLine is not None and cursorBottomLine is not None:
                        if cursorTopLine <= editor.topLine:
                            newTopLine = cursorTopLine - 1
                        elif cursorTopLine >= editor.topLine + winHeight:
                            newTopLine = cursorBottomLine - winHeight +1

                        if currentLineNumber >= newTopLine + winHeight:
                            break


                lines.append(LineNode(currentLineNumber, i.indent, parenAlignment=i.parenAlignment))
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
                            currentLineNode = LineItemNode.fromParts(i.nodeReference, i.nodeAddress,
                                                           stringList[0], i.isCursor, 'start')
                            lines[-1].nodeList.append(currentLineNode)

                        for string in stringList[1:]:
                            currentLineNode = LineItemNode.fromParts(i.nodeReference, i.nodeAddress,
                                                           string, i.isCursor, 'start')
                            lines.append(LineNode(currentLineNumber, 0))
                            currentLineNumber += 1

                            lines[-1].nodeList.append(currentLineNode)

                        currentLineLength = len(currentLineNode.text)

                    else:
                        lines.append(LineNode(currentLineNumber, 0))
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

    #recurMode = recurHorizontal

    parseState = ParseState(editor.buffer.view, [0])
    lineStream = recur(parseState)
    lineList, topLine = unflatten(lineStream)
    toppedLineList = lineList[topLine:]
    return toppedLineList


