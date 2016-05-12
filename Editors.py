__author__ = 'chephren'
import iop
import printsexp
import reader
import tn
import buffer
import funobj as fo
import operator
import screen
import misc
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

class CellEditor(object):
    def __init__(self, content, index=0):
        self.original = str(content)
        self.content = list(str(content).encode('string_escape'))
        if index < 0:
            self.index = len(content) + index + 1
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

        elif key.isPrintable():
            self.content.insert(self.index, key.char())
            self.index += 1


class ColourScheme(fo.FuncObject):
    def __init__(self, bgCol, symbolCol, stringCol, numberCol, activeHiCol, idleHiCol):
        self.bgCol = bgCol
        self.symbolCol = symbolCol
        self.stringCol = stringCol
        self.numberCol = numberCol
        self.activeHiCol = activeHiCol
        self.idleHiCol = idleHiCol

class DisplayEditor(fo.FuncObject):
    editors = 0

    def __init__(self, root, rootCursorAdd=[0], cursorAdd=[0]):
        self.buffer = buffer.BufferSexp(root, rootCursorAdd, cursorAdd)
        self.printingMode = 'horizontal'
        self.printingModeOptions = ['horizontal', 'vertical']
        self.topLine = 0
        self.image = None
        self.colourScheme = ColourScheme(iop.black, iop.white, iop.light_green, iop.light_sky, iop.azure, iop.light_grey)
        self.statusDescription = reader.Symbol(self.__class__.__name__)
        self.id = DisplayEditor.editors
        DisplayEditor.editors += 1

        #need to be refactored out, back into TreeEditor (e.g. by creating a much simpler
        # display routined)
        self.zippedNodes = {}
        self.editing = False
        self.drawMode = 'notCursor'

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
        lineList, self.topLine = printsexp.makeLineIndentList(self, maxx, maxy)
        toppedLineList = lineList[self.topLine:]
        self.image = printsexp.drawLineList(toppedLineList, maxx, maxy, self.colourScheme, isActive)
        return self.image



class TreeEditor(DisplayEditor):
    def __init__(self, root, rootCursorAdd=[0], cursorAdd=[0], zippedNodes={}):
        super(TreeEditor, self).__init__(root, rootCursorAdd, cursorAdd)

        self.editing = False
        self.changeMode = False
        self.cellEditor = None
        self.yankBuffer = None
        self.syncWithRoot = True
        self.updateUndo = False
        self.revealedNodes = {}
        self.zippedNodes = dict(zippedNodes)
        initialViewHistoryNode = tn.TNode(tn.TNode(View(rootCursorAdd)))
        self.viewHistory = buffer.SimpleBuffer(initialViewHistoryNode, [0, 0])
        self.cmdBar = None

        self.drawMode = 'cursor'
        self.statusBar = StatusBar()

    def nodeIsRevealed(self, node):
        return node in self.revealedNodes and self.revealedNodes[node]


    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            return self.update('buffer', self.buffer.syncToNewRoot(newImageRoot))
        else:
            return self

    def updateStatusBar(self):
        self.statusBar.updateStatus([self.statusDescription, self.buffer.viewAdd, self.buffer.cursorAdd,
                             Symbol('nodeID'), self.buffer.cursor.nodeID])

    def handleKeys(self, key, mouse):
        return self.handleKeysInitial(key, mouse)

    def handleKeysInitial(self, key, mouse):
        if self.cmdBar:
            cmdResult = self.cmdBar.handleKeys(key, mouse)
            if cmdResult == 'ESCAPE':
                return self.update('cmdBar', None)
            else:
                return self.update('cmdBar', cmdResult)

        else:
            return self.handleKeysMain(key, mouse)

    def handleMouse(self, mouse):
        if mouse.lbuttonPressed():
            cell = self.image[mouse.y()][mouse.x()]

            if self.editing:
                if cell.lineItemNodeReference and cell.lineItemNodeReference.nodeReference == self.buffer.cursor:
                    self.cellEditor.handleClick(cell.characterReference)
                else:
                    print 'Clicked Outside'
                    # still to do: finish editing and move cursor

            elif cell.lineItemNodeReference:
                newBuff = self.buffer.newCursorAdd(cell.lineItemNodeReference.nodeAddress)
                return self.update('buffer', newBuff)
        elif mouse.wheelDown():
            self.topLine += 3
        elif mouse.wheelUp():
            if self.topLine > 2:
                self.topLine -= 3
            else:
                self.topLine = 0

        else:
            return None

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
        elif key.char() == 'e':
            return self.updateList(
                ('cellEditor', CellEditor(Symbol(''))),
                ('editing', True),
                ('changeMode', False))

        elif key.char() == 'f':
            return self.update('changeMode', 'from')

        elif key.char() == 't':
            return self.update('changeMode', 'to')

        return self.update('changeMode', False)


    def handleKeysMain(self, key, mouse):
        self.updateUndo = False
        self.drawMode = 'uncursor'
        self.updateStatusBar()

        if key.code() != 0:
            self.statusBar.clearMessage()
        self.statusBar = self.statusBar.refreshBuffer()

        mouseResult = self.handleMouse(mouse)
        if mouseResult:
            return mouseResult

        if key.code() == 0:
            return self

        # Reset the screen to include the cursor if we aren't scrolling
        if key.char() not in ('t', 'T'):
            self.drawMode = 'cursor'

        if self.editing:
            return self.handleCellEditor(key)

        elif self.changeMode:
            return self.handleKeysChangeMode(key)


        else:

            if key.code() == iop.KEY_ESCAPE:                                        # exit Editor
                return 'ESC'

            # Trial: blit an image to screen
            # elif key.char() == 'x':
            #     image = io.image_load('fonts\\arial10x10.png')
            #     io.image_blit(image, 0, 10, 10, io.BKGND_DEFAULT, 2, 2, 0)
            #     io.console_flush()
            #     time.sleep(2)


            elif key.char() == 'i' and key.lctrl():     # Go back to the first expression in the list
                return self.update('buffer', self.buffer.curFirst())

            elif key.char() == 'd':
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

            elif key.char() == 'e':
                return self.update('buffer', self.buffer.curLast())

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

            elif key.char() == 'o' and not key.lctrl():
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

            elif key.char() == 't':
                self.topLine += 1

            elif key.char() == 'T':
                if self.topLine > 0:
                    self.topLine -= 1

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
                #newBuff = self.buffer.nestCursor().curChild().insertAtCursor(Symbol('quote'))
                return self.update('buffer', newBuff)

            elif key.char() == '.':
                if self.buffer.cursor.next and not self.buffer.cursor.next.isSubNode():
                    #newBuff = self.buffer.updateAtCursor('methodCall', not self.buffer.cursor.methodCall)
                    newBuff = self.buffer.methodChainAtCursor()
                    return self.update('buffer', newBuff)

            elif key.char() == '+':
                numList = self.buffer.cursorToPyExp()
                result = reduce(operator.add, numList)
                newBuff = self.buffer.replaceAtCursor(result)
                return self.updateList(
                    ('buffer', newBuff),
                    ('updateUndo', True))

            elif key.char() == '"':
                return self.updateList(
                    ('buffer', self.buffer.toggleStringAtCursor()),
                    ('updateUndo', True))

            elif key.char() == ':':
                self.cmdBar = CmdBar(tn.createTNodeExpFromPyExp([[Symbol('')]]), [0], [0, 0])
                self.cmdBar.editing = True
                self.cmdBar.cellEditor = CellEditor(Symbol(''))

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
                    if key.char() == 'J':
                        newBuff = self.buffer.viewToCursor()
                        newHist = self.viewHistory.insertAtCursor(View(newBuff.viewAdd)).curPrev()
                        newHist2 = newHist.rootToCursor()
                        return self.updateList(
                            ('buffer', newBuff),
                            ('viewHistory', newHist2))

                    elif key.char() == 'o' and key.lctrl():
                        newHist = self.viewHistory.curNext()
                        newBuff = self.buffer.newViewAdd(newHist.cursor.child.address)
                        return self.updateList(
                            ('viewHistory', newHist),
                            ('buffer', newBuff))

                    elif key.char() == 'h' and key.lctrl():
                        newHist = self.viewHistory.curPrev()
                        newBuff = self.buffer.newViewAdd(newHist.cursor.child.address)
                        return self.updateList(
                            ('viewHistory', newHist),
                            ('buffer', newBuff))

                    elif key.char() == 'K':
                        return self.update('buffer', self.buffer.viewUp())

                    elif key.char() == 'H':
                        return self.update('buffer', self.buffer.viewPrev())

                    elif key.char() == 'L' and key.lctrl():
                        return self.update('buffer', self.buffer.viewNext())

                    elif key.char() == 'L':
                        return self.update('buffer', self.buffer.curNextChild())

                    elif key.char() == 'w':
                        return self.update('buffer', self.buffer.curNextUnzippedSymbol(self.nodeIsZipped))

                    elif key.char() == 'b':
                        return self.update('buffer', self.buffer.curPrevUnzippedSymbol(self.nodeIsZipped))

                    elif key.code() == iop.KEY_LEFT or key.char() == 'h':
                        return self.update('buffer', self.buffer.curPrevUpAlong())

                    elif key.code() == iop.KEY_RIGHT or key.char() == 'l':
                        if self.cursorIsZipped(self.buffer):
                            newBuff = self.buffer.curUp().curNextUpAlong()
                        else:
                            newBuff = self.buffer.curNextUpAlong()
                        return self.update('buffer', newBuff)

                    elif key.code() == iop.KEY_DOWN or key.char() == 'j':
                        if self.cursorIsZipped(self.buffer):
                            raise ValueError
                        return self.update('buffer', self.buffer.curChild())

                    elif key.code() == iop.KEY_UP or key.char() == 'k':
                        return self.update('buffer', self.buffer.curUp())

                except ValueError:pass

        return self


    def draw(self, maxx, maxy, isActive):
        finalImage = screen.createBlank(maxx, maxy+1)
        mainImage = super(TreeEditor, self).draw(maxx, maxy-1, isActive)[:]

        screen.overlayLinesOnImage(finalImage, 0, mainImage)

        if self.cmdBar:
            cmdImage = self.cmdBar.draw(maxx, 2, isActive=True)
            screen.overlayLinesOnImage(finalImage, maxy - 2, cmdImage)

        if self.statusBar:
            statusImage = self.statusBar.draw(maxx, 2, isActive=False)
            screen.overlayLinesOnImage(finalImage, maxy - 1, statusImage)

        return finalImage


class CmdBar(TreeEditor):
    def __init__(self, *args, **kwargs):
        super(CmdBar, self).__init__(*args, **kwargs)

    def draw(self, maxx, maxy, isActive):
        return super(TreeEditor, self).draw(maxx, maxy, isActive)

    def handleKeys(self, key, mouse):

        if key.code() == iop.KEY_ESCAPE:
            return 'ESCAPE'

        return super(CmdBar, self).handleKeys(key, mouse)


class StatusBar(DisplayEditor):
    def __init__(self, *args, **kwargs):
        self.status = [reader.Symbol('Editor')]
        super(StatusBar, self).__init__(tn.createTNodeExpFromPyExp(self.status))
        self.message = None
        self.colourScheme = ColourScheme(iop.white, iop.black, iop.darker_green, iop.darker_sky, iop.white, iop.white)


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