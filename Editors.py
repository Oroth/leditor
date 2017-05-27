import operator

import funobj as fo
import tn, buffer
import iop, screen, printsexp
import cmdList, misc, reader
from colourScheme import ColourScheme
from reader import Symbol
from iop import Key

class View(object):
    def __init__(self, address):
        self.address = address


class Editor(fo.FuncObject):
    def __init__(self):
        self.maxx = 125
        self.maxy = 75
        self.image = screen.createBlank(self.maxx, self.maxy)
        self.message = ''

    def status(self):
        return [Symbol(self.__class__.__name__)]

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def updateSize(self, newMaxx, newMaxy):
        if (self.maxx, self.maxy) != (newMaxx, newMaxy):
            return self.updateList(
                ('maxx', newMaxx),
                ('maxy', newMaxy),
                ('image', screen.createBlank(newMaxx, newMaxy)))

        else:
            return self

    def draw(self, maxx, maxy, isActive):
        return screen.createBlank(maxx, maxy)

    def handleKeys(self, key):
        return self

    def handleMouse(self, mouse):
        return self

class CellEditor(object):
    def __init__(self, content, index=0):
        self.original = str(content)
        self.content = list(str(content).encode('string_escape'))
        if index < 0:
            self.index = len(self.content) + index + 1
        else:
            self.index = index

        if type(content) is str:
            self.isString = True
        else: self.isString = False

    def getContentAsString(self):
        text = ''.join(self.content)
        if self.isString:
            text = '"' + text + '"'
        return text

    def getContent(self):
        return reader.atom(self.getContentAsString())

    def handleClick(self, characterRef):
        if self.isString:
            self.index = characterRef - 1
        else:
            self.index = characterRef

    def handleKey(self, key):
        if key.code == iop.KEY_ENTER:
            try:
                if self.isString and ''.join(self.content).decode('string_escape'):
                    return 'END'
            except ValueError: return
            return 'END'  # exit editor

        if key.code == iop.KEY_ESCAPE:
            return 'CANCEL'  # exit editor

        elif key.code == iop.KEY_LEFT:
            if self.index > 0:
                self.index -= 1

        elif key.code == iop.KEY_RIGHT:
            if self.index < len(self.content):
                self.index += 1

        elif key.code == iop.KEY_BACKSPACE:
            if self.content and self.index != 0:
                del self.content[self.index - 1]
                self.index -= 1
            elif not self.content:
                return 'PREV'

        elif key.code == iop.KEY_DELETE:
            if self.content and self.index != len(self.content):
                del self.content[self.index]

        elif not self.isString and key.char  == "'":
            return 'QUOTE'

        elif not self.isString and key.char == ".":
            return 'DOT'

        elif not self.isString and key.char == '(':
            return 'NEST'

        elif not self.isString and key.char == ')':
            return 'UNNEST'

        elif key.char == '"':
            if not self.isString:
                self.isString = True
            else:
                temp = ''.join(self.content)
                if temp.find(' ') == -1:
                    self.isString = False

        elif not self.isString and key.code == iop.KEY_SPACE:
            if len(self.content) > 0:
                return 'SPACE'

        elif key.isPrintable() and (self.isString or key.char not in ':;\\|,#~[]{}%&*'):
            self.content.insert(self.index, key.char)
            self.index += 1


class DisplayEditor(fo.FuncObject):
    editors = 0

    def __init__(self, aBuffer=None):
        if aBuffer is None:
            # push to buffer constructor
            self.buffer = buffer.BufferSexp(tn.TNode([[Symbol('')]]), [0], [0, 0])
        else:
            self.buffer = aBuffer
        self._isRootImageEditor = True
        self.printingMode = 'horizontal'
        self.printingModeOptions = ['horizontal', 'vertical']
        self.topLine = 0
        self.image = None
        self.indentWidth = 2
        self.cursorx = 0
        self.cursory = 0
        self.maxx = 120
        self.maxy = 68
        self._message = ''

        self.statusDescription = reader.Symbol(self.__class__.__name__)
        self.id = DisplayEditor.editors
        DisplayEditor.editors += 1

        self.colourScheme = ColourScheme(
            bgCol=iop.black, symbolCol=iop.grey,
            identifierCol=iop.white, stringCol=iop.light_green,
            numberCol=iop.light_purple, activeHiCol=iop.azure, idleHiCol=iop.light_grey)

        #need to be refactored out, back into TreeEditor (e.g. by creating a much simpler
        # display routined)
        self.zippedNodes = {}
        self.editing = False
        self.drawMode = 'notCursor'

        self.persist = ['printingMode', 'topLine', 'buffer', 'zippedNodes']

    @property
    def message(self):
        return self._message

    def isRootImageEditor(self):
        return self._isRootImageEditor

    def getEditorSettings(self):
        viewAdd = self.buffer.viewAdd
        cursorAdd = self.buffer.cursorAdd
        s = reader.Symbol
        zipList = []
        for k, v in self.zippedNodes.iteritems():
            if v is True:
                zipList.append(k)

        return [s('editor'),
                [s('cursor'), 0],
                [s('window'), [s('id'), self.id],
                [s('address'), viewAdd], [s('cursor'), cursorAdd],
                [s('printingMode'), self.printingMode],
                [s('zippedNodes'), zipList]]]


    def nodeIsZipped(self, node):
        return node.nodeID in self.zippedNodes and self.zippedNodes[node.nodeID]

    def cursorIsZipped(self, buffer):
        return self.nodeIsZipped(buffer.cursor)

    def draw(self, maxx, maxy, isActive):
        self.lineList = printsexp.makeIndentedLineList(self, maxx, maxy)
        self.maxx = maxx
        self.maxy = maxy

        self.image, self.cursorx, self.cursory = \
            printsexp.drawLineList(self.lineList, self, isActive)
                #lineList, maxx, maxy, self.colourScheme, isActive, self.indentWidth)

        return self.image

def lineLastSymbolPos(line, maxx=None):
    if not maxx: maxx = len(line)
    lastSymbolPos = 0
    for x, cell in enumerate(line):
        if cell.lineItemNodeReference and x != maxx:
            if cell.character != ')':
                lastSymbolPos = x
        else:
            return lastSymbolPos


class StatusBar(DisplayEditor):
    def __init__(self, aBuffer=None):
        if aBuffer:
            statusBuffer = aBuffer
        else:
            self.status = [reader.Symbol('Editor')]
            statusBuffer = buffer.BufferSexp(tn.createTNodeExpFromPyExp(self.status))

        super(StatusBar, self).__init__(statusBuffer)

        self.colourScheme = ColourScheme(
            bgCol=iop.white, symbolCol=iop.black,
            identifierCol=iop.black, stringCol=iop.darker_green,
            numberCol=iop.darker_sky, activeHiCol=iop.white, idleHiCol=iop.white)

    @classmethod
    def fromStatusList(cls, statusList):
        statusBuffer = buffer.BufferSexp.fromPyExp(statusList)
        return cls(statusBuffer)




class TreeEditor(DisplayEditor):
    def __init__(self, aBuffer=None, zippedNodes={}):
        super(TreeEditor, self).__init__(aBuffer)
        self.editing = False
        self.changeMode = False
        self.cellEditor = None
        self.yankBuffer = None
        self.updateUndo = False
        self.revealedNodes = {}
        self.zippedNodes = dict(zippedNodes)
        initialViewHistoryNode = tn.TNode(tn.TNode(View(self.buffer.viewAdd)))
        self.viewHistory = buffer.SimpleBuffer(initialViewHistoryNode, [0, 0])

        self.maxx = 120
        self.maxy = 68
        self.lineList = printsexp.makeIndentedLineList(self, self.maxx, self.maxy)

        self.lineList.topLine = self.topLine
        isActive = True
        self.image, self.cursorx, self.cursory = \
            printsexp.drawLineList(self.lineList, self, isActive)

        self._message = ''

        self.mainCommands = cmdList.CmdList([
            (Key.c('d'), cmdDeleteAtCursor),
            (Key.c('c'), cmdStartChangeMode),
            (Key.c('a'), cmdAppendAtCursor),
            (Key.c('i'), cmdInsertAtCursor),
            (Key.c('G'), cmdGotoAddressAtCursor),
            (Key.c('('), cmdNestCursor),
            (Key.c(')'), cmdDenestCursor),
            (Key.c('o'), cmdAppendListAtCursor),
            (Key.c('O'), cmdInsertListAtCursor),
            (Key.c('m'), cmdCyclePrintMode),
            (Key.c('N'), cmdViewNewListAtEndOfBuffer),
            (Key.c('p'), cmdPasteAfterCursor),
            (Key.c('P'), cmdPasteBeforeCursor),
            (Key.c('R'), cmdViewToRoot),
            (Key.c('u'), cmdUndo),
            (Key.c('y'), cmdYankAtCursor),
            (Key.c('z'), cmdFoldAtCursor),
            (Key.c("'"), cmdQuoteAtCursor),
            (Key.c('.'), cmdMethodChainAtCursor),
            (Key.c('>'), cmdSlurpAtCursor),
            (Key.c('<'), cmdBarfAtCursor),
            (Key.c('+'), cmdReplaceCursorWithSum),
            (Key.c('"'), cmdToggleStringAtCursor),
            (Key.c('/'), cmdSearchForMatchToCursor),
            (Key.c('='), cmdToggleRevealedNode),
        ])

        self.moveCommands = cmdList.CmdList([
            (Key.c('j', ctrl=True), cmdViewToCursor),
            (Key.c('o', ctrl=True), cmdViewFuturePostion),
            (Key.c('h', ctrl=True), cmdViewPastPosition),
            (Key.c('k', ctrl=True), cmdViewUp),
            (Key.c('H', ctrl=True), cmdViewPrevious),
            (Key.c('L', ctrl=True), cmdViewNext),
            (Key.c('J'), cmdCursorDownAlong),
            (Key.c('H'), cmdCursorPreviousUpAlong),
            (Key.c('K'), cmdCursorUp),
            (Key.c('L'), cmdCursorNextUpAlong),
            (Key.c('e'), cmdCursorToUnzippedLast),
            (Key.vk(iop.KEY_RIGHT), cmdCursorToNextUnzippedSymbol),
            (Key.vk(iop.KEY_LEFT), cmdCursorToPreviousUnzippedSymbol),
            (Key.vk(iop.KEY_DOWN), cmdCursorToAboveSymbol),
            (Key.vk(iop.KEY_UP), cmdCursorToBelowSymbol),
            (Key.c('l'), cmdCursorToNextUnzippedSymbol),
            (Key.c('h'), cmdCursorToPreviousUnzippedSymbol),
            (Key.c('j'), cmdCursorToAboveSymbol),
            (Key.c('k'), cmdCursorToBelowSymbol),
        ])

    def nodeIsRevealed(self, node):
        return node in self.revealedNodes and self.revealedNodes[node]

    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            newBuffer = self.buffer.syncToNewRoot(newImageRoot)
            return self.updateBuffer(newBuffer)
        else:
            return self

    @property
    def message(self):
        if self.editing:
            return '--editing--'

        if self.changeMode:
            return '--Change Mode--'

        return self._message

    def status(self):
        return [self.statusDescription,
                self.buffer.viewAdd,
                self.buffer.cursorAdd,
                Symbol('nodeID'),
                self.buffer.cursor.nodeID]

    def updateSize(self, newMaxx, newMaxy):
        if (self.maxx, self.maxy) != (newMaxx, newMaxy):
            newEditor = self.updateList(
                ('maxx', newMaxx),
                ('maxy', newMaxy))

            return newEditor.refreshImage()
        else:
            return self

    def updateBuffer(self, newBuffer):
        newEditor = self.update('buffer', newBuffer)
        return newEditor.refreshImage()

    def refreshImage(self):
        lineList = printsexp.makeIndentedLineList(self, self.maxx, self.maxy)
        return self.updateLineList(lineList)

    def updateLineList(self, newLineList):
        newEditor = self.update('lineList', newLineList)
        return newEditor.updateToppedLineList(self.topLine)

    def updateToppedLineList(self, newTopLine):
        checkedTopLine = printsexp.getTopLine(self.lineList, newTopLine, self.maxy-1)
        toppedLineList = self.lineList[checkedTopLine:]
        isActive = True
        image, cursorx, cursory = printsexp.drawLineList(
                toppedLineList, self, isActive)

        return self.updateList(
            ('topLine', checkedTopLine),
            ('image', image),
            ('cursorx', cursorx),
            ('cursory', cursory))


    def handleKeys(self, key):
        result = self.handleKeysInitial(key)
        return result

    # split out for flexibility when inheriting
    def handleKeysInitial(self, key):
        self.updateUndo = False
        self._message = ''

        if self.editing:
            return self.handleCellEditor(key).refreshImage()

        elif self.changeMode:
            return self.handleKeysChangeMode(key).refreshImage()

        elif key.char == 't':
            return cmdScrollDown(self)

        elif key.char == 'T':
            return cmdScrollUp(self)

        result =  self.handleKeysMain(key)

        if key.char in  ('j', 'k', 'l', 'h'):
            # this is reason enough to not subclass list (i.e. don't copy entire list)
            #newLineList = self.lineList.update('cursorAdd', result.buffer.cursorAdd)
            newLineList = self.lineList.newCursorAdd(result.buffer.cursorAdd)
            return result.updateLineList(newLineList)


        return result.refreshImage()

    def handleMouse(self, mouse):
        if mouse.lbuttonPressed():
            return self.handleMouseButtonPressed(mouse)

        elif mouse.wheelScrolled():
            return self.handleMouseScroll(mouse)

        return self

    def handleMouseButtonPressed(self, mouse):
        cell = self.image[mouse.y][mouse.x]

        if self.editing:
            if self.cellInCursor(cell):
                self.cellEditor.handleClick(cell.characterReference)
            else:
                print 'Clicked Outside'
                # still to do: finish editing and move cursor

        elif cell.lineItemNodeReference:
            return self.cursorToCellAtom(cell)

        else:
            return self

    def cellInCursor(self, cell):
        if cell.lineItemNodeReference and \
            cell.lineItemNodeReference.nodeReference == self.buffer.cursor:
                return True

        return False

    def cursorToCellAtom(self, cell):
        newBuff = self.buffer.newCursorAdd(cell.lineItemNodeReference.nodeAddress)
        return self.updateBuffer(newBuff)


    def handleMouseScroll(self, mouse):
        if mouse.wheelDown():
            newTopLine = self.topLine + 3

        # scroll up
        elif self.topLine > 2:
            newTopLine = self.topLine - 3
        else:
            newTopLine = 0

        return self.updateToppedLineList(newTopLine)

    def handleCellEditor(self, key):
        finished = self.cellEditor.handleKey(key)
        if finished == 'END':
            if self.cellEditor.getContent() == '':
                isChanged = False if self.cellEditor.original == '' else True
                return self.updateList(
                    ('buffer', self.buffer.deleteAtCursor()),
                    ('editing', False),
                    ('updateUndo', isChanged))
            else:
                content = self.cellEditor.getContent()

                return self.updateList(
                    ('buffer', self.buffer.replaceAtCursor(content)),
                    ('editing', False),
                    ('updateUndo', True))

        elif finished == 'CANCEL':
            if self.buffer.cursor.child == '':
                return self.updateList(
                    ('buffer', self.buffer.deleteAtCursor()),
                    ('editing', False))
            else:
                return self.update('editing', False)

        elif finished == 'PREV':
            if self.buffer.cursorAdd[-1] != 0 and self.buffer.cursor.next:
                newBuff = self.buffer.deleteAtCursor().curPrev()
            else:
                newBuff = self.buffer.deleteAtCursor()

            # check we didn't delete the last node:
            if newBuff.onSubNode() or newBuff.cursor.child is None:
                return self.updateList(
                    ('buffer', newBuff),
                    ('editing', False))

            return self.updateList(
                ('buffer', newBuff),
                ('cellEditor', CellEditor(newBuff.cursor.child, -1)))

        elif finished == 'SPACE':
            ## ideal: self.buffer.spliceAtCursor([self.cellEditor.getContent(), ''], [1])
            newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
            newBuff2 = newBuff.appendAtCursor('').curNext()
            return self.updateList(
                ('buffer', newBuff2),
                ('cellEditor', CellEditor(Symbol(''))))

        elif finished == 'NEST':
            if self.cellEditor.content:
                newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
                newBuff2 = newBuff.appendAtCursor(['']).curNext().curChild()
            else:
                newBuff2 = self.buffer.replaceAtCursor(['']).curChild()

            return self.updateList(
                ('buffer', newBuff2),
                ('cellEditor', CellEditor(Symbol(''))))

        elif finished == 'UNNEST':
            if self.cellEditor.content:
                newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
            else:
                newBuff = self.buffer.deleteAtCursor()

            newBuff2 = newBuff.curUp()
            newBuff3 = newBuff2.appendAtCursor('').curNext()

            return self.updateList(
                ('buffer', newBuff3),
                ('cellEditor', CellEditor(Symbol(''))))

        elif finished == 'QUOTE':
            if self.cellEditor.content:
                newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
                newBuff2 = newBuff.appendAtCursor('').curNext().quoteAtCursor()
            else:
                newBuff2 = self.buffer.replaceAtCursor('').quoteAtCursor()
            return self.updateList(
                ('buffer', newBuff2),
                ('cellEditor', CellEditor(Symbol(''))))

        elif finished == 'DOT':
            if self.cellEditor.content:
                if self.buffer.cursor.quoted:
                    newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent()).curUp().nestCursor()
                    newBuff2 = newBuff.curChild().appendAtCursor('').curNext().quoteAtCursor()
                else:
                    newBuff = self.buffer.replaceAtCursor([self.cellEditor.getContent()]).curChild()
                    newBuff2 = newBuff.appendAtCursor('').curNext().quoteAtCursor()
            else:
                return self
            return self.updateList(
                ('buffer', newBuff2),
                ('cellEditor', CellEditor(Symbol(''))))

        else:
            return self

    def handleKeysChangeMode(self, key):
        if self.changeMode in ('from', 'to'):
            if key.isPrintable():
                return cmdStartEditFromChangeMode(self, key)
            else:
                return self.update('changeMode', False)

        if key.char == 'i':
            return cmdChangeFromStart(self)

        elif key.char == 'a':
            return cmdChangeFromEnd(self)

        elif key.char in ('e', 'l'):
            return cmdChangeToEnd(self)

        elif key.char == 'f':
            return cmdChangeFromMode(self)

        elif key.char == 't':
            return cmdChangeToMode(self)

        return self.update('changeMode', False)

    def handleKeysMain(self, key):

        mainCommandResult = self.mainCommands.process(key, self)

        if mainCommandResult:
            return mainCommandResult
        else:
            try:
                result = self.moveCommands.process(key, self)
                if result:
                    return result
                # # #elif key.char == 'H':     # Go back to the first expression in the list
                # # #     return self.update('buffer', self.buffer.curFirst())

            except ValueError:pass

        return self

    def cursorToScreenPos(self, newx, newy):
        cell = self.image[newy][newx]

        if cell.lineItemNodeReference is None or cell.character == ')':
            lastSymbolPos = lineLastSymbolPos(self.image[newy], newx)
            finalCell = self.image[newy][lastSymbolPos]
        else:
            finalCell = cell

        if finalCell.lineItemNodeReference and finalCell.character != ')':
            newBuff = self.buffer.newCursorAdd(finalCell.lineItemNodeReference.nodeAddress)
            if self.cursorIsZipped(newBuff):
                return self.update('buffer', newBuff)
            else:
                return self.update('buffer', newBuff.curBottom())

        return self

    def draw(self, maxx, maxy, isActive):
        return self.image


##################################### Change Mode Commands ###############################################

def cmdChangeFromStart(editor):
    return editor.updateList(
        ('cellEditor', CellEditor(editor.buffer.cursor.child)),
        ('editing', True),
        ('changeMode', False))

def cmdChangeFromEnd(editor):
    return editor.updateList(
        ('cellEditor', CellEditor(editor.buffer.cursor.child, -1)),
        ('editing', True),
        ('changeMode', False))

def cmdChangeToEnd(editor):
    return editor.updateList(
        ('cellEditor', CellEditor(Symbol(''))),
        ('editing', True),
        ('changeMode', False))

def cmdChangeFromMode(editor):
    return editor.update('changeMode', 'from')

def cmdChangeToMode(editor):
    return editor.update('changeMode', 'to')

def cmdStartEditFromChangeMode(editor, key):
    text = editor.buffer.cursor.child
    index = text.find(key.char)
    if editor.changeMode == 'from':
        newCellEditor =  CellEditor(text, index)
    else:
        newCellEditor = CellEditor(text[index:])

    return editor.updateList(
        ('cellEditor', newCellEditor),
        ('editing', True),
        ('changeMode', False))

############################ Scrolling Commands ##########################################################

def cmdScrollDown(editor):
    return editor.updateToppedLineList(editor.topLine + 1)

def cmdScrollUp(editor):
    if editor.topLine > 0:
        return editor.updateToppedLineList(editor.topLine - 1)
    else:
        return editor

############################ Tree Editor Main Commands ####################################################


def cmdDeleteAtCursor(editor):
    if editor.buffer.cursor != editor.buffer.root:
        return editor.updateList(
            ('buffer', editor.buffer.deleteAtCursor()),
            ('yankBuffer', editor.buffer.cursorToPyExp()),
            ('updateUndo', True))

def cmdStartChangeMode(editor):
    if not editor.buffer.onSubNode():
        print 'changeMode on'
        return editor.update('changeMode', True)

def cmdAppendAtCursor(editor):
    if editor.buffer.cursor != editor.buffer.view:
        newBuff = editor.buffer.appendAtCursor('').curNext()
        return editor.updateList(
            ('buffer', newBuff),
            ('cellEditor', CellEditor(Symbol(''))),
            ('editing', True))

def cmdInsertAtCursor(editor):
    if editor.buffer.cursor != editor.buffer.view:    # maybe the correct behaviour is to sub and ins
        newBuff = editor.buffer.insertAtCursor('').curPrev()
        return editor.updateList(
            ('buffer', newBuff),
            ('cellEditor', CellEditor(Symbol(''))),
            ('editing', True))

def cmdGotoAddressAtCursor(editor):
    lookupAddress = editor.buffer.cursor.childToPyExp()
    newBuff = buffer.BufferSexp(editor.buffer.root, lookupAddress)
    return editor.update('buffer', newBuff)

def cmdNestCursor(editor):
    return editor.updateList(
        ('buffer', editor.buffer.nestCursor()),
        ('updateUndo', True))

def cmdDenestCursor(editor):
    if editor.buffer.onSubNode() and editor.buffer.cursor != editor.buffer.root:
        return editor.updateList(
            ('buffer', editor.buffer.denestCursor()),
            ('updateUndo', True))

def cmdAppendListAtCursor(editor):
    if editor.buffer.cursor != editor.buffer.view:
        newBuff = editor.buffer.appendAtCursor(['']).curNext().curChild()
        return editor.updateList(
            ('buffer', newBuff),
            ('cellEditor', CellEditor(Symbol(''))),
            ('editing', True))

def cmdInsertListAtCursor(editor):
    if editor.buffer.cursor != editor.buffer.view:
        newBuff = editor.buffer.insertAtCursor(['']).curPrev().curChild()
        return editor.updateList(
            ('buffer', newBuff),
            ('cellEditor', CellEditor(Symbol(''))),
            ('editing', True))

def cmdCyclePrintMode(editor):
    newPrintingMode = misc.cycleThroughList(editor.printingMode, editor.printingModeOptions)
    msg = "DisplayMode: " + newPrintingMode
    return editor.updateList(
        ('printingMode', newPrintingMode),
        ('_message', msg))


def cmdViewNewListAtEndOfBuffer(editor):
    newBuff = buffer.BufferSexp(editor.buffer.root, [0], [0, 0]).curLast()
    newBuff = newBuff.appendAtCursor([reader.Symbol('newNode')]).curNext()
    newBuff = newBuff.viewToCursor().curChild()
    editor.topLine = 0
    return editor.update('buffer', newBuff)

def cmdPasteAfterCursor(editor):
    if editor.yankBuffer:
        toInsert = tn.createTNodeExpFromPyExp(editor.yankBuffer)
        return editor.updateList(
            ('buffer', editor.buffer.appendAtCursor(toInsert)),
            ('updateUndo', True))

def cmdPasteBeforeCursor(editor):
    if editor.yankBuffer:
        toInsert = tn.createTNodeExpFromPyExp(editor.yankBuffer)
        return editor.updateList(
            ('buffer', editor.buffer.insertAtCursor(toInsert)),
            ('updateUndo', True))

def cmdViewToRoot(editor):
    return editor.update('buffer', editor.buffer.viewToRoot())

def cmdReplaceAtCursor(editor):
    return editor.updateList(
        ('cellEditor', CellEditor(Symbol(''))),
        ('editing', True))

def cmdUndo(editor):
    return "UNDO"

def cmdYankAtCursor(editor):
    editor.yankBuffer = editor.buffer.cursorToPyExp()
    print editor.yankBuffer

def cmdFoldAtCursor(editor):
    if editor.buffer.cursor.nodeID in editor.zippedNodes:
        editor.zippedNodes[editor.buffer.cursor.nodeID] = not(editor.zippedNodes[editor.buffer.cursor.nodeID])
    else:
        editor.zippedNodes[editor.buffer.cursor.nodeID] = True

def cmdQuoteAtCursor(editor):
    newBuff = editor.buffer.quoteAtCursor()
    return editor.update('buffer', newBuff)

def cmdMethodChainAtCursor(editor):
    if editor.buffer.cursor.next and not editor.buffer.cursor.next.isSubNode():
        newBuff = editor.buffer.methodChainAtCursor()
        return editor.update('buffer', newBuff)

def cmdSlurpAtCursor(editor):
    if editor.buffer.onSubNode() or editor.buffer.cursor.child is None:
        newBuff = editor.buffer.slurpAtCursor()
        return editor.update('buffer', newBuff)

def cmdBarfAtCursor(editor):
    if editor.buffer.onSubNode() and editor.buffer.cursor.child:
        newBuff = editor.buffer.barfAtCursor()
        return editor.update('buffer', newBuff)

def cmdReplaceCursorWithSum(editor):
    numList = editor.buffer.cursorToPyExp()
    try:
        result = reduce(operator.add, numList)
    except TypeError:
        newBuff = editor.buffer
    else:
        newBuff = editor.buffer.replaceAtCursor(result)

    return editor.updateList(
        ('buffer', newBuff),
        ('updateUndo', True))

def cmdToggleStringAtCursor(editor):
    return editor.updateList(
        ('buffer', editor.buffer.toggleStringAtCursor()),
        ('updateUndo', True))

def cmdSearchForMatchToCursor(editor):
    if not editor.buffer.onSubNode():
        try:
            return editor.update('buffer', editor.buffer.search(editor.buffer.getCurrent()))
        except ValueError: pass

def cmdToggleRevealedNode(editor):
    if editor.buffer.cursor in editor.revealedNodes:
        editor.revealedNodes[editor.buffer.cursor] = not(editor.revealedNodes[editor.buffer.cursor])
    else:
        editor.revealedNodes[editor.buffer.cursor] = True



def cmdViewToCursor(editor):
    newBuff = editor.buffer.viewToCursor()
    newHist = editor.viewHistory.insertAtCursor(View(newBuff.viewAdd)).curPrev()
    newHist2 = newHist.rootToCursor()
    return editor.updateList(
        ('buffer', newBuff),
        ('viewHistory', newHist2))

def cmdViewFuturePostion(editor):
    newHist = editor.viewHistory.curNext()
    newBuff = editor.buffer.newViewAdd(newHist.cursor.child.address)
    return editor.updateList(
        ('viewHistory', newHist),
        ('buffer', newBuff))

def cmdViewPastPosition(editor):
    newHist = editor.viewHistory.curPrev()
    newBuff = editor.buffer.newViewAdd(newHist.cursor.child.address)
    return editor.updateList(
        ('viewHistory', newHist),
        ('buffer', newBuff))

def cmdViewUp(editor):
    return editor.update('buffer', editor.buffer.viewUp())

def cmdViewPrevious(editor):
    return editor.update('buffer', editor.buffer.viewPrev())

def cmdViewNext(editor):
    return editor.update('buffer', editor.buffer.viewNext())


def cmdCursorDownAlong(editor):
    if editor.cursorIsZipped(editor.buffer):
        raise ValueError
    return editor.update('buffer', editor.buffer.curDownAlong(editor.nodeIsZipped))

def cmdCursorPreviousUpAlong(editor):
    return editor.update('buffer', editor.buffer.curPrevUpAlong())

def cmdCursorUp(editor):
    return editor.update('buffer', editor.buffer.curUp())

def cmdCursorNextUpAlong(editor):
    if editor.cursorIsZipped(editor.buffer):
        newBuff = editor.buffer.curUp().curNextUpAlong()
    else:
        newBuff = editor.buffer.curNextUpAlong()
    return editor.update('buffer', newBuff)


def cmdCursorToUnzippedLast(editor):
    return editor.update('buffer', editor.buffer.curUnzippedLast(editor.nodeIsZipped))

def cmdCursorToNextUnzippedSymbol(editor):
    return editor.update('buffer', editor.buffer.curNextUnzippedSymbol(editor.nodeIsZipped))

def cmdCursorToPreviousUnzippedSymbol(editor):
    return editor.update('buffer', editor.buffer.curPrevUnzippedSymbol(editor.nodeIsZipped))

def cmdCursorToAboveSymbol(editor):
    if editor.cursory +1 < len(editor.image):
        return editor.cursorToScreenPos(editor.cursorx, editor.cursory + 1)

def cmdCursorToBelowSymbol(editor):
    if editor.topLine > 0 and editor.cursory == 0:
        newEd = editor.updateToppedLineList(editor.topLine-1)
        return newEd.cursorToScreenPos(editor.cursorx, 0)
    elif editor.cursory > 0:
        return editor.cursorToScreenPos(editor.cursorx, editor.cursory - 1)