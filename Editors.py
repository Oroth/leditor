__author__ = 'chephren'
import iop
import futility
import reader
from reader import Symbol
import tn
import buffer
import funobj as fo
import operator
import re


class CellEditor(object):
    def __init__(self, content):
        self.original = str(content)
        self.content = list(str(content).encode('string_escape'))
        self.index = 0
        # should check to make sure not a symbol
        if not isinstance(content, Symbol):
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

        elif re.match('\\w', key.char()):
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


class TreeEditor(fo.FuncObject):
    editors = 0

    def __init__(self, root, rootCursorAdd=[0], cursorAdd=[0], zippedNodes=None):
        self.buffer = buffer.BufferSexp(root, rootCursorAdd, cursorAdd)
        self.posx = 0
        self.posy = 0
        self.maxx = 80
        self.maxy = 50

        self.statusDescription = reader.Symbol('TreeEditor')
        self.editing = False
        self.cellEditor = None
        self.yankBuffer = None
        self.printingMode = 'horizontal'
        self.syncWithRoot = True
        self.updateUndo = False
        self.showValues = False
        self.revealedNodes = {}

        #self.zippedNodes = {}
        if zippedNodes == None:
            self.zippedNodes = {}
        else:
            self.zippedNodes = zippedNodes.copy()

        self.drawMode = 'cursor'
        self.topLine = 0
        self.firstNode = self.buffer.view
        self.topNode = self.buffer.cursorToFirst().curBottom().cursor
        self.image = None

        self.colourScheme = ColourScheme(iop.black, iop.white, iop.light_green, iop.light_sky, iop.azure, iop.light_grey)
        self.statusBar = StatusBar()
        self.id = TreeEditor.editors
        TreeEditor.editors += 1


    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            return self.update('buffer', self.buffer.syncToNewRoot(newImageRoot))
        else:
            return self

    def setPosition(self, newPosx, newPosy, newMaxx, newMaxy):
        self.posx = newPosx
        self.posy = newPosy
        self.maxx = newMaxx
        self.maxy = newMaxy


    def nodeIsZipped(self, node):
        return node.nodeID in self.zippedNodes and self.zippedNodes[node.nodeID]

    def cursorIsZipped(self, buffer):
        return self.nodeIsZipped(buffer.cursor)
        #return self.buffer.cursor.nodeID in self.zippedNodes and self.zippedNodes[self.buffer.cursor.nodeID]

    def handleKeys(self, key, mouse):
        self.updateUndo = False
        self.statusBar.item1 = self.statusDescription
        self.statusBar.item2 = self.buffer.viewAdd
        self.statusBar.item3 = self.buffer.cursorAdd
        if key.code() != 0:
            self.statusBar.message = None
        self.statusBar = self.statusBar.refreshStatus()

        if mouse.lbuttonPressed():
            cell = self.image[mouse.y() - self.posy][mouse.x() - self.posx]

            if self.editing:
                if cell.lineItemNodeReference and cell.lineItemNodeReference.nodeReference == self.buffer.cursor:
                    self.cellEditor.handleClick(cell.characterReference)
                else:
                    print 'Clicked Outside'
                    # still to do: finish editing and move cursor

            elif cell.lineItemNodeReference:
                newBuff = self.buffer.cursorToAddress(cell.lineItemNodeReference.nodeAddress)
                return self.update('buffer', newBuff)
        elif mouse.wheelDown():
            self.topLine += 3
        elif mouse.wheelUp():
            if self.topLine > 2:
                self.topLine -= 3
            else:
                self.topLine = 0


        if self.editing:

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
                self.statusBar.message = "Editing"

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
                    return self.updateList(
                        ('cellEditor', CellEditor(self.buffer.cursor.child)),
                        ('editing', True))

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

            elif key.char() == 'o':
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
                modes = ['code', 'horizontal', 'vertical']
                if self.printingMode == 'help':
                    currentModePos = 2
                else:
                    currentModePos = modes.index(self.printingMode)
                self.printingMode = modes[(currentModePos + 1) % len(modes)]
                self.statusBar.displayMessage("DisplayMode: " + self.printingMode)


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
                newBuff = self.buffer.nestCursor().curChild().insertAtCursor(Symbol('quote'))
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

            elif key.char() == '=':
                if self.buffer.cursor in self.revealedNodes:
                    self.revealedNodes[self.buffer.cursor] = not(self.revealedNodes[self.buffer.cursor])
                else:
                    self.revealedNodes[self.buffer.cursor] = True

            # Go to help pages, will need to be updated
            elif key.char() == '?':
                helpIter, helpAddress = self.buffer.root.gotoNodeAtNVS(['origin', 'help'])
                newBuff = buffer.BufferSexp(self.buffer.root, helpAddress)
                self.printingMode = 'help'
                return self.update('buffer', newBuff)

            else:
                try:
                    if key.char() == 'J':
                        return self.update('buffer', self.buffer.viewToCursor())

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


    def draw(self, posx, posy, maxx, maxy, isActive):
        lineList = futility.createStucturalLineIndentList(self, maxx, maxy)
        self.topLine = lineList[0].lineNumber

        fakeWin = futility.drawLineList(lineList, maxx, maxy, self.colourScheme, isActive)
        #self.topNode = lineList[0].nodeList[0].nodeReference
        #self.topNode = self.buffer.cursorToFirst().curBottom().cursor
        #self.bottomNode = lineList[-1].nodeList[-1].nodeReference

        finalWin = futility.sliceFakeWindow(fakeWin, 0, maxy)
        self.image = finalWin

        futility.printToScreen(finalWin, posx, posy)

        if self.statusBar:
            self.statusBar.draw(0, posy + maxy - 1, maxx, 2, isActive=False)



class StatusBar(TreeEditor):
    def __init__(self, *args, **kwargs):
        self.editing = False
        self.printingMode = 'horizontal'
        self.zippedNodes = {}
        self.statusBar = None
        self.item1 = None
        self.item2 = None
        self.item3 = None
        self.message = None
        self.topLine = 0
        self.bgCol = iop.white
        self.fgCol = iop.black

        self.colourScheme = ColourScheme(iop.white, iop.black, iop.darker_green, iop.darker_sky, iop.white, iop.white)

        status = tn.createTNodeExpFromPyExp(
            [reader.Symbol('Editor')
            ,reader.Symbol('View')
            ,reader.Symbol('Address')]
        )

        self.buffer = buffer.BufferSexp.fromPyExp(status)

    def draw(self, posx, posy, maxx, maxy, isActive):
        return super(StatusBar, self).draw(posx, posy, maxx, maxy, isActive)

    def refreshStatus(self):
        statusList = [x for x in [self.item1, self.item2, self.item3, self.message] if x is not None]
        return self.updateStatus(statusList)

    def updateStatus(self, status):
        newStatus = buffer.BufferSexp.fromPyExp(status)
        return self.update('buffer', newStatus)

    def displayMessage(self, message):
        self.message = message
        self.buffer = self.buffer.curChild().curLast().appendAtCursor(message)