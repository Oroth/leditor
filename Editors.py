__author__ = 'chephren'
import operator

import buffer
import funobj as fo
import iop
import misc
import printsexp
import reader
import screen
import tn
from reader import Symbol


class View(object):
    def __init__(self, address):
        self.address = address

class EditorAtom(object):
    def __init__(self, atom):
        self.atom = atom

    def toPyExp(self):
        pass

    def toString(self):
        pass

    def __getslice__(self, *args, **kargs):
        return self.atom.__getslice__(*args, **kargs)

class IntAtom(EditorAtom):
    pass

class Editor(fo.FuncObject):
    def __init__(self):
        self.statusBar = StatusBar()

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

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

        if key.code() == iop.KEY_ENTER:
            try:
                if self.isString and ''.join(self.content).decode('string_escape'):
                    return 'END'
            except ValueError: return
            return 'END'  # exit editor

        if key.code() == iop.KEY_ESCAPE:
            return 'CANCEL'  # exit editor

        elif key.code() == iop.KEY_LEFT:
            if self.index > 0:
                self.index -= 1

        elif key.code() == iop.KEY_RIGHT:
            if self.index < len(self.content):
                self.index += 1

        elif key.code() == iop.KEY_BACKSPACE:
            if self.content and self.index != 0:
                del self.content[self.index - 1]
                self.index -= 1
            elif not self.content:
                return 'PREV'

        elif key.code() == iop.KEY_DELETE:
            if self.content and self.index != len(self.content):
                del self.content[self.index]

        elif not self.isString and key.char()  == "'":
            return 'QUOTE'

        elif not self.isString and key.char() == ".":
            return 'DOT'

        elif not self.isString and key.char() == '(':
            return 'NEST'

        elif not self.isString and key.char() == ')':
            return 'UNNEST'

        elif key.char() == '"':
            if not self.isString:
                self.isString = True
            else:
                temp = ''.join(self.content)
                if temp.find(' ') == -1:
                    self.isString = False

        elif not self.isString and key.code() == iop.KEY_SPACE:
            if len(self.content) > 0:
                return 'SPACE'

        elif key.isPrintable() and (self.isString or key.char() not in ':;\\|,#~[]{}%&*'):
            self.content.insert(self.index, key.char())
            self.index += 1

class ColourScheme(fo.FuncObject):
    def __init__(self,
                 bgCol, symbolCol, identifierCol,
                 stringCol, numberCol,
                 activeHiCol, idleHiCol,
                 operatorCol=iop.dark_red, keyWordCol=iop.light_sky):
        self.bgCol = bgCol
        self.symbolCol = symbolCol
        self.identifierCol = identifierCol
        self.stringCol = stringCol
        self.numberCol = numberCol
        self.activeHiCol = activeHiCol
        self.idleHiCol = idleHiCol
        self.operatorCol = operatorCol
        self.keyWordCol = keyWordCol

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
        lineList = printsexp.makeLineIndentList(self, maxx, maxy)
        #if cursorTopLine is None:
        #    cursorTopLine, cursorBottomLine = 0, 0
        #self.topLine = printsexp.getTopLine(lineList, self.topLine, maxy)
        #toppedLineList = lineList.lines[self.topLine:]

        self.image, self.cursorx, self.cursory = \
            printsexp.drawLineList(
                lineList, maxx, maxy, self.colourScheme, isActive, self.indentWidth)

        return self.image



class TreeEditor(DisplayEditor):
    def __init__(self, aBuffer=None, zippedNodes={}):
        super(TreeEditor, self).__init__(aBuffer)

        self.editing = False
        self.changeMode = False
        self.cellEditor = None
        self.yankBuffer = None
        #self.syncWithRoot = True
        self.updateUndo = False
        self.revealedNodes = {}
        self.zippedNodes = dict(zippedNodes)
        initialViewHistoryNode = tn.TNode(tn.TNode(View(self.buffer.viewAdd)))
        self.viewHistory = buffer.SimpleBuffer(initialViewHistoryNode, [0, 0])
        self.drawMode = 'cursor'
        self.statusBar = StatusBar()

        self.maxx = 120
        self.maxy = 68
        self.lineList = printsexp.makeLineIndentList(self, self.maxx, self.maxy)

        #toppedLineList = self.lineList[self.topLine:]
        self.lineList.topLine = self.topLine
        isActive = True
        self.image, self.cursorx, self.cursory = \
            printsexp.drawLineList(
                self.lineList, self.maxx, self.maxy, self.colourScheme, isActive, self.indentWidth)

    def nodeIsRevealed(self, node):
        return node in self.revealedNodes and self.revealedNodes[node]

    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            newBuffer = self.buffer.syncToNewRoot(newImageRoot)
            return self.updateBuffer(newBuffer)
            #return self.update('buffer', self.buffer.syncToNewRoot(newImageRoot))
        else:
            return self

    def updateStatusBar(self):
        self.statusBar.updateStatus([self.statusDescription, self.buffer.viewAdd, self.buffer.cursorAdd,
                             Symbol('nodeID'), self.buffer.cursor.nodeID])

    def updateBuffer(self, newBuffer):
        newEditor = self.update('buffer', newBuffer)
        return newEditor.updateImage()

    def updateSize(self, newMaxx, newMaxy):
        if (self.maxx, self.maxy) != (newMaxx, newMaxy):
            self.maxx = newMaxx
            self.maxy = newMaxy

            return self.updateImage()
        else:
            return self

    def updateLineList(self, newLineList):
        newTopLine = printsexp.getTopLine(newLineList, self.topLine, self.maxy-1)
        toppedLineList = newLineList[newTopLine:]

        isActive = True
        image, self.cursorx, self.cursory = \
            printsexp.drawLineList(
                toppedLineList, self.maxx, self.maxy, self.colourScheme, isActive, self.indentWidth)

        return self.updateList(
            ('image', image),
            ('topLine', newTopLine),
            ('lineList', newLineList))


    #def updateWrappedLineList(self, maxy):

    def updateTopLine(self, newTopLine):
        checkedTopLine = printsexp.getTopLine(self.lineList, newTopLine, self.maxy-1)
        toppedLineList = self.lineList[checkedTopLine:]
        #self.lineList.topLine = checkedTopLine
        isActive = True
        image, self.cursorx, self.cursory = \
            printsexp.drawLineList(
                toppedLineList, self.maxx, self.maxy, self.colourScheme, isActive, self.indentWidth)

        return self.updateList(
            ('image', image),
            ('topLine', checkedTopLine))

    def updateImage(self):
        lineList = printsexp.makeLineIndentList(self, self.maxx, self.maxy)
        topLine = printsexp.getTopLine(lineList, self.topLine, self.maxy-1)

        toppedLineList = lineList[topLine:]
        lineList.topLine = topLine
        isActive = True
        self.image, self.cursorx, self.cursory = \
            printsexp.drawLineList(
                toppedLineList, self.maxx, self.maxy, self.colourScheme, isActive, self.indentWidth)

        return self.updateList(
            ('lineList', lineList),
            ('topLine', topLine))

    def handleKeys(self, key):
        result = self.handleKeysInitial(key)
        return result


    # split out for flexibility when inheriting
    def handleKeysInitial(self, key):
        self.updateUndo = False
        self.drawMode = 'uncursor'
        self.updateStatusBar()

        if key.code() != 0:
            self.statusBar.clearMessage()
        self.statusBar = self.statusBar.refreshBuffer()

        # Reset the screen to include the cursor if we aren't scrolling
        #if key.char() not in ('t', 'T'):
        #    self.drawMode = 'cursor'

        if self.editing:
            return self.handleCellEditor(key)

        elif self.changeMode:
            return self.handleKeysChangeMode(key)

        elif key.char() == 't':
            return self.updateTopLine(self.topLine + 1)

        elif key.char() == 'T':
            if self.topLine > 0:
                return self.updateTopLine(self.topLine - 1)
            else:
                return self

        result =  self.handleKeysMain(key)

        if key.char() in  ('j', 'k', 'l', 'h'):
            # this is reason enough to not subclass list (i.e. don't copy entire list)
            #newLineList = self.lineList.update('cursorAdd', result.buffer.cursorAdd)
            newLineList = self.lineList.newCursorAdd(result.buffer.cursorAdd)
            return result.updateLineList(newLineList)

        return result.updateImage()

    def handleMouse(self, mouse):
        if mouse.lbuttonPressed():

            cell = self.image[mouse.y][mouse.x]

            if self.editing:
                if cell.lineItemNodeReference and cell.lineItemNodeReference.nodeReference == self.buffer.cursor:
                    self.cellEditor.handleClick(cell.characterReference)
                else:
                    print 'Clicked Outside'
                    # still to do: finish editing and move cursor

            elif cell.lineItemNodeReference:
                newBuff = self.buffer.newCursorAdd(cell.lineItemNodeReference.nodeAddress)
                return self.updateBuffer(newBuff)

            else:
                return self

        elif mouse.wheelScrolled():
            if mouse.wheelDown():
                newTopLine = self.topLine + 3

            # scroll up
            elif self.topLine > 2:
                newTopLine = self.topLine - 3
            else:
                newTopLine = 0

            return self.updateTopLine(newTopLine)

        return self

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
                #newBuff2 = self.buffer.replaceAtCursor('').quoteAtCursor()
            return self.updateList(
                ('buffer', newBuff2),
                ('cellEditor', CellEditor(Symbol(''))))

        else:
            self.statusBar.updateMessage("Editing")
            return self

    def handleKeysChangeMode(self, key):

        if self.changeMode in ('from', 'to'):
            if key.isPrintable():
                text = self.buffer.cursor.child
                index = text.find(key.char())
                if self.changeMode == 'from':
                    newCellEditor =  CellEditor(text, index)
                else:
                    newCellEditor = CellEditor(text[index:])

                return self.updateList(
                    ('cellEditor', newCellEditor),
                    ('editing', True),
                    ('changeMode', False))
            else:
                return self.update('changeMode', False)

        # change from start
        if key.char() == 'i':
            return self.updateList(
                ('cellEditor', CellEditor(self.buffer.cursor.child)),
                ('editing', True),
                ('changeMode', False))

        # change from end
        elif key.char() == 'a':
            return self.updateList(
                ('cellEditor', CellEditor(self.buffer.cursor.child, -1)),
                ('editing', True),
                ('changeMode', False))

        # change to end
        elif key.char() in ('e', 'l'):
            return self.updateList(
                ('cellEditor', CellEditor(Symbol(''))),
                ('editing', True),
                ('changeMode', False))

        elif key.char() == 'f':
            return self.update('changeMode', 'from')

        elif key.char() == 't':
            return self.update('changeMode', 'to')

        return self.update('changeMode', False)

    def handleKeysMain(self, key):

        if key.char() == 'd':
            if self.buffer.cursor != self.buffer.root:
                return self.updateList(
                    ('buffer', self.buffer.deleteAtCursor()),
                    ('yankBuffer', self.buffer.cursorToPyExp()),
                    ('updateUndo', True))

        elif key.char() == 'c':
            if not self.buffer.onSubNode():
                print 'changeMode on'
                return self.update('changeMode', True)

        elif key.char() == 'a':
            if self.buffer.cursor != self.buffer.view:
                newBuff = self.buffer.appendAtCursor('').curNext()
                return self.updateList(
                    ('buffer', newBuff),
                    ('cellEditor', CellEditor(Symbol(''))),
                    ('editing', True))

        elif key.char() == 'i':
            if self.buffer.cursor != self.buffer.view:    # maybe the correct behaviour is to sub and ins
                newBuff = self.buffer.insertAtCursor('').curPrev()
                return self.updateList(
                    ('buffer', newBuff),
                    ('cellEditor', CellEditor(Symbol(''))),
                    ('editing', True))


        elif key.char() == 'G':
            lookupAddress = self.buffer.cursor.childToPyExp()
            newBuff = buffer.BufferSexp(self.buffer.root, lookupAddress)
            return self.update('buffer', newBuff)


        elif key.char() == '(':
            return self.updateList(
                ('buffer', self.buffer.nestCursor()),
                ('updateUndo', True))

        elif key.char() == ')':
            if self.buffer.onSubNode() and self.buffer.cursor != self.buffer.root:
                return self.updateList(
                    ('buffer', self.buffer.denestCursor()),
                    ('updateUndo', True))

        elif key.char() == 'o' and not key.ctrl():
            if self.buffer.cursor != self.buffer.view:
                newBuff = self.buffer.appendAtCursor(['']).curNext().curChild()
                return self.updateList(
                    ('buffer', newBuff),
                    ('cellEditor', CellEditor(Symbol(''))),
                    ('editing', True))

        elif key.char() == 'O':
            if self.buffer.cursor != self.buffer.view:
                newBuff = self.buffer.insertAtCursor(['']).curPrev().curChild()
                return self.updateList(
                    ('buffer', newBuff),
                    ('cellEditor', CellEditor(Symbol(''))),
                    ('editing', True))

        elif key.char() == 'm':
            newPrintingMode = misc.cycleThroughList(self.printingMode, self.printingModeOptions)
            self.statusBar.updateMessage("DisplayMode: " + newPrintingMode)

            return self.update('printingMode', newPrintingMode)


        elif key.char() == 'N':
            newBuff = buffer.BufferSexp(self.buffer.root, [0], [0, 0]).curLast()
            newBuff = newBuff.appendAtCursor([reader.Symbol('newNode')]).curNext()
            newBuff = newBuff.viewToCursor().curChild()
            self.topLine = 0
            return self.update('buffer', newBuff)

        elif key.char() == 'p':
            if self.yankBuffer:
                toInsert = tn.createTNodeExpFromPyExp(self.yankBuffer)
                return self.updateList(
                    ('buffer', self.buffer.appendAtCursor(toInsert)),
                    ('updateUndo', True))

        elif key.char() == 'P':
            if self.yankBuffer:
                toInsert = tn.createTNodeExpFromPyExp(self.yankBuffer)
                return self.updateList(
                    ('buffer', self.buffer.insertAtCursor(toInsert)),
                    ('updateUndo', True))

        elif key.char() == 'R':
            return self.update('buffer', self.buffer.viewToRoot())

        elif key.char() == 's':
            return self.updateList(
                ('cellEditor', CellEditor(Symbol(''))),
                ('editing', True))

        elif key.char() == 'u':
            return "UNDO"

        elif key.char() == 'y':
            self.yankBuffer = self.buffer.cursorToPyExp()
            print self.yankBuffer

        elif key.char() == 'z':
            if self.buffer.cursor.nodeID in self.zippedNodes:
                self.zippedNodes[self.buffer.cursor.nodeID] = not(self.zippedNodes[self.buffer.cursor.nodeID])
            else:
                self.zippedNodes[self.buffer.cursor.nodeID] = True

        elif key.char() == "'":
            newBuff = self.buffer.quoteAtCursor()
            return self.update('buffer', newBuff)

        elif key.char() == '.':
            if self.buffer.cursor.next and not self.buffer.cursor.next.isSubNode():
                newBuff = self.buffer.methodChainAtCursor()
                return self.update('buffer', newBuff)

        elif key.char() == '>':
            if self.buffer.onSubNode() or self.buffer.cursor.child is None:
                newBuff = self.buffer.slurpAtCursor()
                return self.update('buffer', newBuff)

        elif key.char() == '<':
            if self.buffer.onSubNode() and self.buffer.cursor.child:
                newBuff = self.buffer.barfAtCursor()
                return self.update('buffer', newBuff)

        elif key.char() == '+':
            numList = self.buffer.cursorToPyExp()
            try:
                result = reduce(operator.add, numList)
            except TypeError:
                newBuff = self.buffer
            else:
                newBuff = self.buffer.replaceAtCursor(result)

            return self.updateList(
                ('buffer', newBuff),
                ('updateUndo', True))

        elif key.char() == '"':
            return self.updateList(
                ('buffer', self.buffer.toggleStringAtCursor()),
                ('updateUndo', True))

        elif key.char() == '/':
            if not self.buffer.onSubNode():
                try:
                    return self.update('buffer', self.buffer.search(self.buffer.getCurrent()))
                except ValueError: pass

        elif key.char() == '=':
            if self.buffer.cursor in self.revealedNodes:
                self.revealedNodes[self.buffer.cursor] = not(self.revealedNodes[self.buffer.cursor])
            else:
                self.revealedNodes[self.buffer.cursor] = True


        else:
            try:
                if key.char() == 'j' and key.ctrl():
                    newBuff = self.buffer.viewToCursor()
                    newHist = self.viewHistory.insertAtCursor(View(newBuff.viewAdd)).curPrev()
                    newHist2 = newHist.rootToCursor()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('viewHistory', newHist2))

                elif key.char() == 'o' and key.ctrl():
                    newHist = self.viewHistory.curNext()
                    newBuff = self.buffer.newViewAdd(newHist.cursor.child.address)
                    return self.updateList(
                        ('viewHistory', newHist),
                        ('buffer', newBuff))

                elif key.char() == 'h' and key.ctrl():
                    newHist = self.viewHistory.curPrev()
                    newBuff = self.buffer.newViewAdd(newHist.cursor.child.address)
                    return self.updateList(
                        ('viewHistory', newHist),
                        ('buffer', newBuff))

                elif key.char() == 'k' and key.ctrl():
                    return self.update('buffer', self.buffer.viewUp())

                elif key.char() == 'H' and key.ctrl():
                    return self.update('buffer', self.buffer.viewPrev())

                elif key.char() == 'L' and key.ctrl():
                    return self.update('buffer', self.buffer.viewNext())


                elif key.char() == 'J':
                    if self.cursorIsZipped(self.buffer):
                        raise ValueError
                    return self.update('buffer', self.buffer.curDownAlong(self.nodeIsZipped))

                elif key.char() == 'H':
                    return self.update('buffer', self.buffer.curPrevUpAlong())

                elif key.char() == 'K':
                    return self.update('buffer', self.buffer.curUp())

                elif key.char() == 'L':
                    if self.cursorIsZipped(self.buffer):
                        newBuff = self.buffer.curUp().curNextUpAlong()
                    else:
                        newBuff = self.buffer.curNextUpAlong()
                    return self.update('buffer', newBuff)


                elif key.char() == 'e': # and key.ctrl():
                    return self.update('buffer', self.buffer.curUnzippedLast(self.nodeIsZipped))
                #
                #elif key.char() == 'H':     # Go back to the first expression in the list
                #     return self.update('buffer', self.buffer.curFirst())



                elif key.code() == iop.KEY_RIGHT or key.char() == 'l':
                    return self.update('buffer', self.buffer.curNextUnzippedSymbol(self.nodeIsZipped))

                elif key.code() == iop.KEY_LEFT or key.char() == 'h':
                    return self.update('buffer', self.buffer.curPrevUnzippedSymbol(self.nodeIsZipped))

                elif key.code() == iop.KEY_DOWN or key.char() == 'j' and self.cursory +1 < len(self.image):
                    return self.cursorToScreenPos(self.cursorx, self.cursory + 1)

                elif key.code() == iop.KEY_UP or key.char() == 'k':
                    if self.topLine > 0 and self.cursory == 0:
                        newEd = self.updateTopLine(self.topLine-1)
                        return newEd.cursorToScreenPos(self.cursorx, 0)
                    elif self.cursory > 0:
                        return self.cursorToScreenPos(self.cursorx, self.cursory - 1)


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
        finalImage = screen.createBlank(maxx, maxy)
        screen.overlayLinesOnImage(finalImage, 0, self.image)

        if self.statusBar:
            statusImage = self.statusBar.draw(maxx, 1, isActive=False)
            screen.overlayLinesOnImage(finalImage, maxy - 1, statusImage)

        return finalImage



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
    def __init__(self, *args, **kwargs):
        self.status = [reader.Symbol('Editor')]
        newBuffer = buffer.BufferSexp(tn.createTNodeExpFromPyExp(self.status))
        super(StatusBar, self).__init__(newBuffer)
        self.message = None
        self.colourScheme = ColourScheme(
            bgCol=iop.white, symbolCol=iop.black,
            identifierCol=iop.black, stringCol=iop.darker_green,
            numberCol=iop.darker_sky, activeHiCol=iop.white, idleHiCol=iop.white)

    def refreshBuffer(self):
        statusList = list(self.status)
        if self.message:
            statusList.append(self.message)
        newBuff = buffer.BufferSexp.fromPyExp(statusList)
        return self.update('buffer', newBuff)

    def updateStatus(self, status):
        self.status = status

    def updateMessage(self, message):
        self.message = message

    def clearMessage(self):
        self.message = None

