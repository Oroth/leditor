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


class TokenNode(fo.FuncObject):
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

    def nodeToString(self):
        return self.text


class LineNode(fo.FuncObject):
    def __init__(self, lineNumber, indent, tokenList=[], parenAlignment=0):
        self.lineNumber = lineNumber
        self.indent = indent
        self.tokenList = list(tokenList)
        self.parenAlignment = parenAlignment

    def length(self):
        text = [token.text for token in self.tokenList]
        spaces = len(self.tokenList)
        return self.indent + self.parenAlignment + len(''.join(text)) + spaces


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
            firstItem = line.tokenList[0]
            if firstItem.isCursor and prevLine and prevLine.tokenList[-1].isCursor:
                bgcol = hlcol
            else:
                bgcol = colScheme.bgCol
            indentString = ''.join([' ' for i in xrange(totalLineIndent)])
            #image = putNodeOnImage(image, 0, y, indentString, firstItem, bgcol)
            putNodeOnImage2(image, 0, y, indentString, firstItem, bgcol, colScheme.symbolCol)

        prevLine = line

        prevItem = None
        for item in line.tokenList:

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
            if item.printRule in [ 'cellEditorString', 'cellEditorNonString'] and item.highlightIndex:
                (image[y][x+item.highlightIndex]).bgColour = hlcol
                x += 1
            x += len(text)

#            #Add space between symbols
#            if text != '(' and item != line.tokenList[-1]:
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

    def recurHorizontal(parseState):
        return parseState

    def recurVertical(parseState):
        node = parseState.cursor
        if node.next and node.next.isSubNode():
            ps = parseState.set('newline')
            if node.isSubNode():
                return ps.update('parenAlignment', 1)
            else:
                return ps.incNesting()

        return parseState

    def recurCode(parseState):
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


    def makeLineTokenStream(parseState):

        if parseState.cursor == editor.buffer.cursor:
            ps = parseState.update('isCursor', True)
        else:
            ps = parseState

        if editor.nodeIsZipped(ps.cursor) and editor.printingMode != 'help':
            ret = [TokenNode(ps, '...')]
            return ret

        if ps.cursor == editor.buffer.cursor and editor.editing:
            # slightly hacky, isCursor is technically True, but we call it false to stop it
            # from highlighting the entire node. need to re-engineer the rules really
            editingNode = TokenNode(ps.reset('isCursor'), editor.cellEditor.getContentAsString())
            if editor.cellEditor.isString:
                editingNode.printRule = 'cellEditorString'
                editingNode.highlightIndex = editor.cellEditor.index + 1
            else:
                editingNode.printRule = 'cellEditorNonString'
                editingNode.highlightIndex = editor.cellEditor.index
            ret = [editingNode]

        elif ps.onSubNode():
            ret = [TokenNode(ps, '(')]
            ret.extend(makeLineTokenStream(ps.curChild().reset('newline', 'reindent')))
            ret.append(TokenNode(ps, ')'))

        elif ps.cursor.child is None:
            ret = [TokenNode(ps, '('),
                   TokenNode(ps, ')')]

        else:
            ret = [TokenNode(ps)]

        # code editor, needs to go with the code editor code
        try:
            if editor.revealedNodes[ps.cursor]:
                ret.append(TokenNode(ps, '=>'))
                ret.append(TokenNode(ps, reader.to_string(editor.nodeValues[ps.cursor])))
        except KeyError: pass
        except AttributeError: pass

        # pass the original state to maintain the same cursor highlighting
        if parseState.cursor.next:
            modeps = recurMode(parseState)
            if modeps.newline:
                ret.append(LineNode(0,  modeps.nesting, parenAlignment= modeps.parenAlignment))

            ret.extend(makeLineTokenStream(modeps.curNext()))

        return ret


    # Takes a string and tries to split it across two or more lines depending on where the spaces are in
    # the string and how much space is left to the end of the line and on subsequent lines
    def splitStringAcrossLines(string, curLineSpaceLeft, maxLineLength):
        stringList = []
        curLineStartIndex = 0                # The position in string from which to start taking words
        curLineLastSpaceIndex = string.rfind(' ', curLineStartIndex, curLineSpaceLeft)

        # if there is space on the current line, append the maximum number of words
        if curLineLastSpaceIndex != -1:
            stringList.append(string[:curLineLastSpaceIndex])
            curLineStartIndex = curLineLastSpaceIndex + 1
        # Otherwise start from the next line
        else:
            stringList.append('')

        # Find the index of the rightmost space within the search index
        curLineMaxSpaceIndex = string.rfind(' ', curLineStartIndex, curLineStartIndex+maxLineLength)

        # While we can find words that will fit and not everything will fit on the line
        while curLineMaxSpaceIndex != -1 and curLineStartIndex+maxLineLength < len(string):
            stringList.append(string[curLineStartIndex:curLineMaxSpaceIndex])
            curLineStartIndex = curLineMaxSpaceIndex+1
            curLineMaxSpaceIndex = string.rfind(' ', curLineStartIndex, curLineStartIndex + maxLineLength)

        stringList.append(string[curLineStartIndex:])

        return stringList

    def findHighlightPosition(stringList, highlightIndex):
        currentLen = 0
        for stringIndex, string in enumerate(stringList):
            if currentLen + len(string) <  highlightIndex:
                currentLen += len(string) +1
            else:
                return stringIndex, highlightIndex - currentLen



    # Walk through the stream of line and node items to put each node on a line
    def makeLineList(stream):
        lines = [LineNode(0, 0)]
        currentLineNumber = 1
        cursorTopLine = None
        cursorBottomLine = None
        newTopLine = editor.topLine

        for node in stream:

            if isinstance(node, LineNode):
                if editor.drawMode == 'cursor':
                    if cursorTopLine is not None and cursorBottomLine is not None:
                        if cursorTopLine <= editor.topLine:
                            newTopLine = cursorTopLine - 1
                        elif cursorTopLine >= editor.topLine + winHeight:
                            newTopLine = cursorBottomLine - winHeight +1

                        if currentLineNumber >= newTopLine + winHeight:
                            break


                lines.append(LineNode(currentLineNumber, node.indent, parenAlignment=node.parenAlignment))
                currentLineNumber += 1

            # TokenNode
            else:
                if node.isCursor:
                    if cursorTopLine is None:
                        cursorTopLine = currentLineNumber
                    cursorBottomLine = currentLineNumber

                tokenLength = len(node.nodeToString()) + 1  ## technically parens will only be 1 char
                currentLineLength = lines[-1].length()
                if (currentLineLength + tokenLength) > winWidth:

                    if isinstance(node.nodeReference.child, str):
                        #appendStringTokenToLineList(lines, node)
                        lineLengthLeft = winWidth - currentLineLength
                        stringList = splitStringAcrossLines(node.text, lineLengthLeft, winWidth)
                        nodeList = [node.updateList(('text', string), ('highlightIndex', None)) for string in stringList]
                        if node.highlightIndex:
                            hlStringListIndex, hlIndex = findHighlightPosition(stringList, node.highlightIndex)
                            nodeList[hlStringListIndex].highlightIndex = hlIndex

                        if stringList[0] != '':
                            lines[-1].tokenList.append(nodeList[0])

                        for node in nodeList[1:]:
                            lines.append(LineNode(currentLineNumber, indent=lines[-1].indent))
                            currentLineNumber += 1
                            lines[-1].tokenList.append(node)

                    else:
                        lines.append(LineNode(currentLineNumber, 0))
                        currentLineNumber += 1

                        lines[-1].tokenList.append(node)

                else:
                    lines[-1].tokenList.append(node)

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
    lineStream = makeLineTokenStream(parseState)
    lineList, topLine = makeLineList(lineStream)
    toppedLineList = lineList[topLine:]
    return toppedLineList


