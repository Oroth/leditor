import funobj as fo
import tn, buffer
import reader
from screen import createBlank, putNodeOnImage
import textwrap

class ParseState(buffer.ViewBuffer):
    def __init__(self, node, address, nesting=0, isCursor=False, isMethodChain=False):
        self.nesting = nesting
        self.isCursor = isCursor
        self.newline = False        # While True will start a newline at each node
        self.parenAlignment = 0
        self.isMethodChain = isMethodChain
        super(ParseState, self).__init__(node, [0], address)

    def incNesting(self):
        return self.update('nesting', self.nesting+1)

    def setNewline(self):
        return self.update('newline', True)


class TokenNode(fo.FuncObject):
    def __init__(self, ps, text=None, stringSplit=None):
        self.nodeReference = ps.cursor
        if text is None:
            self.text = reader.to_string(ps.current)
        else:
            self.text = str(text)
        self.isCursor = ps.isCursor
        self.stringSplit = stringSplit
        self.printRule = None
        self.highlightIndex = None
        self.nodeAddress = ps.cursorAdd

    @property
    def isEditing(self):
        return self.highlightIndex is not None

    def editingLastCell(self):
        return self.highlightIndex is not None and self.highlightIndex == len(self.text)


class LineNode(fo.FuncObject):
    def __init__(self, indent, parenAlignment=0, tokenList=[]):
        self.indent = indent
        self.parenAlignment = parenAlignment
        self.tokenList = list(tokenList)

    def addToken(self, tokenNode):
        self.tokenList.append(tokenNode)

    def length(self):
        text = [token.text for token in self.tokenList]
        spaces = len(self.tokenList)
        return self.indent + self.parenAlignment + len(''.join(text)) + spaces


class LineList(list, fo.FuncObject):
    """ holds a bunch of lines """
    def __init__(self, lines, curTop, curBot, curAdd, topLine=0):
        super(LineList, self).__init__(lines)
        self.cursorTopLine = curTop if curTop is not None else 0
        self.cursorBottomLine = curBot if curBot is not None else 0
        self.cursorAdd = curAdd
        self.topLine = topLine

    def __getslice__(self, i, j):
        newList = list.__getslice__(self, i, j)
        return LineList(newList, self.cursorTopLine, self.cursorBottomLine, self.cursorAdd)

    def topped(self):
        return self[self.topLine]

    # switch to binary search maybe for extra efficiency
    def newCursorAdd(self, add):
        newTopLine = None
        newBottomLine = None

        for lineNumber, lineNode in enumerate(self):
            for tokenNode in lineNode.tokenList:
                if cursorMatch(add, tokenNode.nodeAddress):
                    if newTopLine is None:
                        newTopLine = lineNumber
                    newBottomLine = lineNumber
                elif newBottomLine is not None:
                    break

        return self.updateList(
            ('cursorAdd', add),
            ('cursorTopLine', newTopLine),
            ('cursorBottomLine', newBottomLine))

    #def wrap(self, width)

def spaceHighlighted(cursorAddress, tokenAddress):
    return cursorMatch(cursorAddress, tokenAddress) and cursorAddress != tokenAddress

# draws the indent space at the beginning of lines
# returns the size of the indent
def drawIndentSpace(line, indentWidth, colScheme, hlcol, image, x, y, cursorAdd):
    totalLineIndent = line.indent * indentWidth + line.parenAlignment

    # print the indentation space
    if line.indent > 0:
        firstItem = line.tokenList[0]
        if spaceHighlighted(cursorAdd, firstItem.nodeAddress):
            bgcol = hlcol
        else:
            bgcol = colScheme.bgCol
        indentString = totalLineIndent * ' '
        putNodeOnImage(image, 0, y, indentString, firstItem, bgcol, colScheme.symbolCol)

    return totalLineIndent

def cursorMatch(cursorAddress, targetAddress):
    return cursorAddress == targetAddress[:len(cursorAddress)]


def drawToken(token, prevToken, colScheme, hlcol, image, x, y, cursorAddress):
    fgcol = colScheme.lookupTokenFGColour(token)
    text = token.text

    if cursorMatch(cursorAddress, token.nodeAddress) and not token.isEditing:
        bgcol = hlcol

    elif text in ('.', ')') and prevToken and prevToken.editingLastCell():
        bgcol = hlcol

    else:
        bgcol = colScheme.bgCol

    # Truncate long strings (e.g. evaluation results)
    winWidth = len(image[0])
    if len(text) >= winWidth:
        text = text[0:winWidth - 7] + '...'

    putNodeOnImage(image, x, y, text, token, bgcol, fgcol)

    # highlight the current character if we are using the cell editor
    if token.isEditing:
        (image[y][x + token.highlightIndex]).bgColour = hlcol



def drawSymbolSpace(token, prevToken, colScheme, hlcol, image, x, y, cursorAdd):
    if spaceHighlighted(cursorAdd, token.nodeAddress):
        bgcol = hlcol
    elif prevToken.editingLastCell():
        bgcol = hlcol
    else:
        bgcol = colScheme.bgCol

    putNodeOnImage(image, x, y, ' ', token, bgcol, colScheme.symbolCol)

def blankRequired(prevToken, currentToken):
    if prevToken and prevToken.text not in ("'", '.', '(', '#') \
            and currentToken.text not in ('.', ')'):
        return True


def drawLineList(lineList, editor, isActive):
    cursorx, cursory = None, None
    winWidth = editor.maxx
    winHeight = editor.maxy
    colScheme = editor.colourScheme
    indentWidth = editor.indentWidth

    image = createBlank(winWidth, winHeight, colScheme.bgCol, colScheme.symbolCol)
    hlcol = colScheme.activeHiCol if isActive else colScheme.idleHiCol

    for y, line in enumerate(lineList[:winHeight]):
        x = drawIndentSpace(line, indentWidth, colScheme, hlcol, image, 0, y, lineList.cursorAdd)

        prevToken = None

        for token in line.tokenList:
            if blankRequired(prevToken, token):
                drawSymbolSpace(token, prevToken, colScheme, hlcol, image, x, y, lineList.cursorAdd)
                x += 1

            # cursor tracking
            if cursorMatch(lineList.cursorAdd, token.nodeAddress):
                if cursorx is None:
                    cursorx = x
                cursory = y

            drawToken(token, prevToken, colScheme, hlcol, image, x, y, lineList.cursorAdd)
            x += len(token.text)

            prevToken = token

    return image, cursorx, cursory

def getLine(string, lineLength, splitMidWord=True):
    if len(string) < lineLength:
        return string[:lineLength]

    finalBlankIndex = string.rfind(' ', 0, lineLength)
    if finalBlankIndex <= 1:
        if splitMidWord:
            return string[:lineLength]
        else:
            return ''
    else:
        return string[:finalBlankIndex]

def splitStringAcrossLines2(string, lineLength):
    strings = []
    totalLength = len(string)

    firstLine = getLine(string, lineLength)
    startIndex = len(firstLine)

    while startIndex < totalLength:
        remainingString = string[startIndex:]
        nextLine = getLine(remainingString, lineLength)
        strings.append(nextLine)
        startIndex += len(nextLine)

    return strings

def splitStringAcrossLines1(string, lineLength, startingIndex):
    initialLineLength = lineLength - startingIndex
    firstLine = getLine(string, initialLineLength, splitMidWord=False)
    firstLineLength = len(firstLine)

    remainingLines = splitStringAcrossLines2(string[firstLineLength:], lineLength)

    return [firstLine] + remainingLines

# Takes a string and tries to split it across two or more lines depending on where the blanks are in
# the string and how much space is left to the end of the line and on subsequent lines
def splitStringAcrossLines(string, remainingSpace, lineLength):
    stringList = []
    startIndex = 0                # The position in string from which to start taking words
    finalBlankIndex = string.rfind(' ', startIndex, remainingSpace)

    # if there is space on the current line, append the maximum number of words
    if finalBlankIndex != -1:
        stringList.append(string[:finalBlankIndex])
        startIndex = finalBlankIndex + 1
    # Otherwise start from the next line
    else:
        stringList.append('')

    # Find the index of the rightmost blank within the search index
    finalBlankIndex = string.rfind(' ', startIndex, startIndex + lineLength)

    # While we can find words that will fit and not everything will fit on the line
    while finalBlankIndex != -1 and startIndex+lineLength < len(string):
        stringList.append(string[startIndex:finalBlankIndex])
        startIndex = finalBlankIndex+1
        finalBlankIndex = string.rfind(' ', startIndex, startIndex + lineLength)

    stringList.append(string[startIndex:])

    return stringList

def findHighlightPosition(stringList, highlightIndex):
    currentLen = 0
    for stringIndex, string in enumerate(stringList):
        if currentLen + len(string) <  highlightIndex:
            currentLen += len(string) +1
        else:
            return stringIndex, highlightIndex - currentLen

def appendStringTokenToLineList(lines, node, winWidth):
    currentLineLength = lines[-1].length()
    lineLengthLeft = winWidth - currentLineLength
    stringList = splitStringAcrossLines(node.text, lineLengthLeft, winWidth)
    #stringList = splitStringAcrossLines1(node.text, winWidth, currentLineLength)
    nodeList = [node.updateList(('text', string), ('highlightIndex', None)) for string in stringList]

    if node.highlightIndex:
        hlStringListIndex, hlIndex = findHighlightPosition(stringList, node.highlightIndex)
        nodeList[hlStringListIndex].highlightIndex = hlIndex

    if stringList[0] != '':
        lines[-1].addToken(nodeList[0])

    for node in nodeList[1:]:
        lines.append(LineNode(lines[-1].indent, lines[-1].parenAlignment))
        lines[-1].addToken(node)


# Walk through the stream of line and token nodes, assigning tokens to lines
def makeLineList(stream, winWidth):
    lines = [LineNode(0, 0)]
    cursorTopLine = None
    cursorBottomLine = None
    cursorAddress = None

    for node in stream:
        currentLineNumber = len(lines)
        currentLine = lines[-1]
        currentLineLength = currentLine.length()

        if isinstance(node, LineNode):
            lines.append(LineNode(node.indent, node.parenAlignment))

        # TokenNode
        else:
            if node.isCursor:
                if cursorTopLine is None:
                    cursorAddress = node.nodeAddress
                    cursorTopLine = currentLineNumber
                cursorBottomLine = currentLineNumber

            tokenLength = len(node.text) + 1  ## technically parens will only be 1 char

            if (currentLineLength + tokenLength) > winWidth:
                if isinstance(node.nodeReference.child, str):
                    appendStringTokenToLineList(lines, node, winWidth)
                else:
                    newLine = LineNode(0)
                    newLine.addToken(node)
                    lines.append(newLine)

            else:
                currentLine.addToken(node)

    return LineList(lines, cursorTopLine, cursorBottomLine, cursorAddress)

def makeIndentedLineList(editor, winWidth, winHeight):

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

        if editor.nodeIsZipped(node.next):
            return parseState
        if node.next and node.next.isSubNode():
            ps = parseState.set('newline')
            if node.isSubNode():
                return ps.update('parenAlignment', 1)
            else:
                return ps.incNesting()

        return parseState

    def recurAllVertical(parseState):
        node = parseState.cursor
        ps = parseState.set('newline')

        if editor.nodeIsZipped(node.next):
            return parseState

        if node.next and node.next.isSubNode() and not node.next.next:
            return ps.incNesting().update('parenAlignment', 0)

        else:
            return ps.update('parenAlignment', 1)

    def recurFolders(parseState):
        ps = parseState.set('newline')

        return ps.update('parenAlignment', 1)


    def recurCode(parseState):
        node = parseState.cursor

        if editor.nodeIsZipped(node.next):
            return parseState

        #if node.child in ('^', 'if'):
        #    return parseState.incNesting()

        if parseState.cursorAdd[-1] == 0:
            if (node.isSubNode() and isComplex(node.child)):
                return parseState.setNewline().update('parenAlignment', 1)

            if isComplex(node.next) or (node.next.isSubNode() and isComplex(node.next.child)):

                ps = parseState.setNewline()
                # if the first node is a list, assume it is part of a let-syntax, so we know not to reindent
                if node.isSubNode():
                    return ps.update('parenAlignment', 1)
                else:
                    return ps.incNesting()

        return parseState


    def makeMixedLineTokenList(parseState):


        if parseState.cursor == editor.buffer.cursor:
            ps = parseState.update('isCursor', True)
        else:
            ps = parseState

        if editor.nodeIsZipped(ps.cursor) and editor.printingMode != 'help':
            ret = [TokenNode(ps, '...')]
            return ret


        if ps.cursor == editor.buffer.cursor and editor.editing:
            editingNode = TokenNode(ps, editor.cellEditor.getContentAsString())
            if editor.cellEditor.isString:
                editingNode.printRule = 'cellEditorString'
                editingNode.highlightIndex = editor.cellEditor.index + 1
            else:
                editingNode.printRule = 'cellEditorNonString'
                editingNode.highlightIndex = editor.cellEditor.index
            ret = [editingNode]


        elif ps.onSubNode():
            if tn.isMethodCallExp(ps.current):
                methodChainps = ps.curChild().reset('newline').set('isMethodChain')
                ret = makeMixedLineTokenList(methodChainps)
            else:
                ret = [TokenNode(ps, ps.cursor.startToken)]
                if editor.printingMode == 'folders':
                    ret.append(LineNode(ps.nesting + 1, ps.parenAlignment))
                    psChild  = ps.curChild().incNesting()
                else:
                    psChild = ps.curChild().reset('newline', 'isMethodChain')
                ret.extend(makeMixedLineTokenList(psChild))
                ret.append(TokenNode(ps, ps.cursor.endToken))

        elif ps.current is None:
            ret = [TokenNode(ps, '('), TokenNode(ps, ')')]

        else:
            ret = [TokenNode(ps)]

        if ps.cursor.quoted and not ps.isMethodChain:
            ret.insert(0, TokenNode(ps, "'"))

        if ps.isMethodChain and ps.cursor.next:
            ret.append(TokenNode(ps, "."))

        # code editor, needs to go with the code editor code
        # try:
        #     if  editor.nodeIsRevealed(ps.cursor) or \
        #             (ps.cursor == editor.buffer.cursor and editor.evalCursorMode == 'active' and ps.onSubNode()):
        #         ret.append(TokenNode(ps, '=>'))
        #         ret.append(TokenNode(ps, reader.to_string(editor.getNodeValue(ps.cursor))))
        # # this exception catch is sort of hacky - covers for the fact that e.g. statusBar won't have revealedNodes
        # # potentially should either move revealedNodes to the parent (but isn't relevant to everything
        # # should call a more generic function on each editor
        # # should move all the code so it is a method of the editor
        # except AttributeError: pass
        # except KeyError: pass

        if parseState.cursor == viewNode:
            return ret

        # pass the original state to maintain the same cursor highlighting
        if parseState.cursor.next:
            modeps = recurMode(parseState)
            if modeps.newline:
                ret.append(LineNode(modeps.nesting, modeps.parenAlignment))

            ret.extend(makeMixedLineTokenList(modeps.curNext()))

        return ret


    recurModes = {
            'code': recurCode,
            'horizontal': recurHorizontal,
            'vertical': recurVertical,
            'allVertical': recurAllVertical,
            'folders': recurFolders
        }
    recurMode = recurModes[editor.printingMode]

    viewNode = editor.buffer.view
    parseState = ParseState(editor.buffer.view, [0])
    lineTokenList = makeMixedLineTokenList(parseState)
    lineList = makeLineList(lineTokenList, winWidth)

    return lineList

# move to lineList
def getTopLine(lineList, currentTopLine, winHeight):
    totalLineCount = len(lineList)

    if lineList.cursorTopLine < currentTopLine:
        newTopLine = lineList.cursorTopLine - 1
    elif lineList.cursorTopLine >= currentTopLine + winHeight - 1:
        newTopLine = lineList.cursorBottomLine - winHeight +1
    #don't allow scrolling past the bottom
    elif totalLineCount < winHeight:
        newTopLine = 0
    elif totalLineCount <= currentTopLine + winHeight:
        newTopLine = totalLineCount - winHeight
    else:
        newTopLine = currentTopLine

    return newTopLine