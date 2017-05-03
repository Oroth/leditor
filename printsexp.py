__author__ = 'chephren'
import buffer
import tn
import funobj as fo
import reader
from screen import createBlank, putNodeOnImage


class ParseState(buffer.ViewBuffer):
    def __init__(self, node, address, nesting=0, isCursor=False, isMethodChain=False):
        self.nesting = nesting
        self.isCursor = isCursor
        self.newline = False        # While True will start a newline at each node
        self.reindent = False       # While true will increase the amount of nesting...
        self.parenAlignment = 0
        self.letSyntax = False
        self.isMethodChain = isMethodChain
        self.codeState = {}
        self.startOfLine = False
        super(ParseState, self).__init__(node, [0], address)

    def incNesting(self):
        return self.update('nesting', self.nesting+1)

    def setNewline(self):
        return self.updateList(
            ('newline', True),
            ('startOfLine', True))


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

# draws the indent space at the beginning of lines
# returns the size of the indent
def drawIndentSpace(line, prevLine, indentWidth, colScheme, hlcol, image, x, y):
    totalLineIndent = line.indent * indentWidth + line.parenAlignment

    # print the indentation space
    if line.indent > 0:
        firstItem = line.tokenList[0]
        # highlight the indented space if it carries over from the previous line
        if firstItem.isCursor and prevLine and prevLine.tokenList[-1].isCursor:
            bgcol = hlcol
        else:
            bgcol = colScheme.bgCol
        indentString = totalLineIndent * ' '
        putNodeOnImage(image, 0, y, indentString, firstItem, bgcol, colScheme.symbolCol)

    return totalLineIndent


def drawItem(item, prevItem, colScheme, hlcol, image, x, y, winWidth, winHeight):
    fgcol = lookupItemFGColour(item, colScheme)
    text = item.nodeToString()

    if item.isCursor:
        bgcol = hlcol

    elif \
            text in ('.', ')') \
            and prevItem and prevItem.printRule in [ 'cellEditorString', 'cellEditorNonString'] \
            and prevItem.highlightIndex == len(prevItem.nodeToString()):
        bgcol = hlcol

    else:
        bgcol = colScheme.bgCol

    # Truncate long strings (e.g. evaluation results)
    if len(text) >= winWidth:
        text = text[0:winWidth - 7] + '...'

    putNodeOnImage(image, x, y, text, item, bgcol, fgcol)

    # highlight the current character if we are using the cell editor
    if item.printRule in [ 'cellEditorString', 'cellEditorNonString']:
        if item.highlightIndex is not None:
            (image[y][x+item.highlightIndex]).bgColour = hlcol
            x += 1



def lookupItemFGColour(item, colScheme):
   if isinstance(item.nodeReference.child, reader.Symbol):
        if item.nodeToString() in ("'", '.', '(', ')', '#'):
            fgcol = colScheme.symbolCol
        elif item.nodeToString() in ('=', '+', '-', '*', '/', '>', '>=', '<', '=<', '!='):
            fgcol = colScheme.operatorCol
        elif item.nodeToString() in ('obj', '^', 'let', 'if'):
            fgcol = colScheme.keyWordCol
        else:
            fgcol = colScheme.identifierCol
   elif isinstance(item.nodeReference.child, str) and item.printRule != 'cellEditorNonString':
       fgcol = colScheme.stringCol
   elif isinstance(item.nodeReference.child, int) or isinstance(item.nodeReference.child, float):
       fgcol = colScheme.numberCol
   else:
       fgcol = colScheme.symbolCol

   return fgcol

def drawSymbolSpace(item, prevItem, colScheme, hlcol, image, x, y):
    if item.isCursor and prevItem.isCursor:
        bgcol = hlcol
    elif prevItem.printRule in [ 'cellEditorString', 'cellEditorNonString'] \
                and prevItem.highlightIndex == len(prevItem.nodeToString()):
        bgcol = hlcol
    else:
        bgcol = colScheme.bgCol

    putNodeOnImage(image, x, y, ' ', item, bgcol, colScheme.symbolCol)


def drawLineList(lineList, winWidth, winHeight, colScheme, isActive, indentWidth):
    image = createBlank(winWidth, winHeight, colScheme.bgCol, colScheme.symbolCol)
    hlcol = colScheme.activeHiCol if isActive else colScheme.idleHiCol
    prevLine = None
    y = 0
    curx, cury = 0, 0


    for line in lineList[:winHeight]:
        x = drawIndentSpace(line, prevLine, indentWidth, colScheme, hlcol, image, 0, y)

        prevLine = line
        prevItem = None

        for item in line.tokenList:
            if prevItem and prevItem.nodeToString() not in ("'", '.', '(', '#') \
                        and item.nodeToString() not in ('.', ')'):

                drawSymbolSpace(item, prevItem, colScheme, hlcol, image, x, y)
                x += 1

            # cursor tracking
            if item.isCursor:
                if not prevItem or not prevItem.isCursor:
                    curx = x
                cury = y

            drawItem(item, prevItem, colScheme, hlcol, image, x, y, winWidth, winHeight)
            x += len(item.nodeToString())

            prevItem = item

        y += 1

    return image, curx, cury


def makeLineIndentList(editor, winWidth, winHeight):

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
            #if node.isSubNode():
            #    return ps.update('parenAlignment', 1)
            #else:
            #return ps.incNesting()

        #return ps


    def recurCode(parseState):
        node = parseState.cursor

        if editor.nodeIsZipped(node.next):
            return parseState

        if node.child == 'let':
            parseState.codeState['letState'] = parseState.nesting +1

        if node.child in ('^', 'if'):
            return parseState.incNesting()

        if (node.isSubNode() and isComplex(node.child)):
            return parseState.setNewline().update('parenAlignment', 1)

        if isComplex(node.next) or (node.next.isSubNode() and isComplex(node.next.child)):

            ps = parseState.setNewline()
            # if the first node is a list, assume it is part of a let-syntax, so we know not to reindent
            if node.isSubNode():
                #return ps
                return ps.update('parenAlignment', 1)
            else:
                return ps.incNesting()



        # if 'letState' in parseState.codeState and parseState.codeState['letState'] != 'off':
        #     if parseState.codeState['letState'] == parseState.nesting and not parseState.startOfLine:
        #        return parseState.setNewline()
        #     elif parseState.codeState['letState'] < parseState.nesting:
        #       parseState.codeState['letState'] = 'off'


        return parseState.reset('startOfLine')


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
            if tn.isMethodCallExp(ps.cursor.child):
                methodChainps = ps.curChild().reset('newline', 'reindent').set('isMethodChain')
                ret = makeLineTokenStream(methodChainps)
            else:
                ret = [TokenNode(ps, '(')]
                ret.extend(makeLineTokenStream(ps.curChild().reset('newline', 'reindent', 'isMethodChain')))
                ret.append(TokenNode(ps, ')'))

        elif ps.cursor.child is None:
            ret = [TokenNode(ps, '('), TokenNode(ps, ')')]

        else:
            ret = [TokenNode(ps)]

        if ps.cursor.quoted and not ps.isMethodChain:
            ret.insert(0, TokenNode(ps, "'"))

        if ps.isMethodChain and ps.cursor.next:
            ret.append(TokenNode(ps, "."))

        # code editor, needs to go with the code editor code
        try:
            if  editor.nodeIsRevealed(ps.cursor) or \
                    (ps.cursor == editor.buffer.cursor and editor.evalCursorMode == 'active' and ps.onSubNode()):
                ret.append(TokenNode(ps, '=>'))
                ret.append(TokenNode(ps, reader.to_string(editor.getNodeValue(ps.cursor))))
        # this exception catch is sort of hacky - covers for the fact that e.g. statusBar won't have revealedNodes
        # potentially should either move revealedNodes to the parent (but isn't relevant to everything
        # should call a more generic function on each editor
        # should move all the code so it is a method of the editor
        except AttributeError: pass
        except KeyError: pass

        if parseState.cursor == viewNode:
            return ret

        # pass the original state to maintain the same cursor highlighting
        if parseState.cursor.next:
            modeps = recurMode(parseState)
            if modeps.newline:
                ret.append(LineNode(modeps.nesting, modeps.parenAlignment))

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

    def appendStringTokenToLineList(lines, node):
        currentLineLength = lines[-1].length()
        lineLengthLeft = winWidth - currentLineLength
        stringList = splitStringAcrossLines(node.text, lineLengthLeft, winWidth)
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
    def makeLineList(stream):
        lines = [LineNode(0, 0)]
        cursorTopLine = None
        cursorBottomLine = None
        newTopLine = editor.topLine

        for node in stream:
            currentLineNumber = len(lines)
            currentLine = lines[-1]
            currentLineLength = currentLine.length()

            if isinstance(node, LineNode):
                # Adjust the top line of the window relative to the cursor:
                #  if it's above the current window set the top line to be above it
                if editor.drawMode == 'cursor':
                    if cursorTopLine is not None and cursorBottomLine is not None:
                        if cursorTopLine <= editor.topLine:
                            newTopLine = cursorTopLine - 1
                        elif cursorTopLine >= editor.topLine + winHeight:
                            newTopLine = cursorBottomLine - winHeight +1

                        if currentLineNumber >= newTopLine + winHeight:
                            break

                lines.append(LineNode(node.indent, node.parenAlignment))

            # TokenNode
            else:
                if node.isCursor:
                    if cursorTopLine is None:
                        cursorTopLine = currentLineNumber
                    cursorBottomLine = currentLineNumber
                    #print cursorTopLine, cursorBottomLine

                tokenLength = len(node.nodeToString()) + 1  ## technically parens will only be 1 char

                if (currentLineLength + tokenLength) > winWidth:
                    if isinstance(node.nodeReference.child, str):
                        appendStringTokenToLineList(lines, node)
                    else:
                        newLine = LineNode(0)
                        newLine.addToken(node)
                        lines.append(newLine)

                else:
                    currentLine.addToken(node)

        totalLineCount = len(lines)

        #check if we found the last line
        if cursorTopLine >= editor.topLine + winHeight and editor.drawMode == 'cursor':
            newTopLine = cursorBottomLine - winHeight +1
        #don't allow scrolling past the bottom
        elif totalLineCount < winHeight:
            newTopLine = 0
        elif totalLineCount <= editor.topLine + winHeight:
            newTopLine = totalLineCount - winHeight


        return lines, newTopLine, cursorTopLine, cursorBottomLine


    recurModes = \
        {
            'code': recurCode,
            'horizontal': recurHorizontal,
            'vertical': recurVertical,
            'allVertical': recurAllVertical
        }
    recurMode = recurModes[editor.printingMode]

    viewNode = editor.buffer.view
    parseState = ParseState(editor.buffer.view, [0])
    lineTokenStream = makeLineTokenStream(parseState)
    lineList, topLine, cursorTopLine, cursorBottomLine = makeLineList(lineTokenStream)

    return lineList, topLine, cursorTopLine, cursorBottomLine


def getTopLine(lineList, cursorTopLine, cursorBottomLine, currentTopLine, winHeight):
    totalLineCount = len(lineList)

    if cursorTopLine <= currentTopLine:
        newTopLine = cursorTopLine - 1
    elif cursorTopLine >= currentTopLine + winHeight:
        newTopLine = cursorBottomLine - winHeight +1
    #don't allow scrolling past the bottom
    elif totalLineCount < winHeight:
        newTopLine = 0
    elif totalLineCount <= currentTopLine + winHeight:
        newTopLine = totalLineCount - winHeight
    else:
        newTopLine = currentTopLine

    return newTopLine