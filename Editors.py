__author__ = 'chephren'
import libtcodpy as libtcod
import futility
import reader
from reader import Symbol
import Eval
import TNode
import operator
import time


class CellEditor(object):
    def __init__(self, content):
        self.original = str(content)
        self.content = list(str(content).encode('string_escape'))
        self.index = 0
        # should check to make sure not a symbol
        if not isinstance(content, Symbol): # and len(content) > 0 and content[0] == '"':
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

        if key.vk == libtcod.KEY_ENTER:
            try:
                if self.isString and ''.join(self.content).decode('string_escape'):
                    return 'END'
            except ValueError: return
            return 'END'  # exit editor

        if key.vk == libtcod.KEY_ESCAPE:
            return 'CANCEL'  # exit editor

        elif key.vk == libtcod.KEY_LEFT:
            if self.index > 0:
                self.index -= 1

        elif key.vk == libtcod.KEY_RIGHT:
            if self.index < len(self.content):
                self.index += 1

        elif key.vk == libtcod.KEY_BACKSPACE:
            if self.content and self.index != 0:
                del self.content[self.index - 1]
                self.index -= 1

        elif key.vk == libtcod.KEY_DELETE:
            if self.content and self.index != len(self.content):
                del self.content[self.index]

        elif not self.isString and chr(key.c) == '(':
            return 'NEST'

        elif not self.isString and chr(key.c) == ')':
            return 'UNNEST'

        elif chr(key.c) == '"':
            if not self.isString:
                self.isString = True
            else:
                temp = ''.join(self.content)
                if temp.find(' ') == -1:
                    self.isString = False

        elif not self.isString and key.vk == libtcod.KEY_SPACE:
            if len(self.content) > 0:
                return 'SPACE'

        elif key.c != 0:
            self.content.insert(self.index, chr(key.c))
            self.index += 1

    # def draw(self, pen):
    #     if self.isString:
    #         pen.writeHL('"' + ''.join(self.content) + '" ', libtcod.azure, self.index+1)
    #     else:
    #         pen.writeHL(''.join(self.content) + ' ', libtcod.azure, self.index)
    #
    # def getImage(self):
    #     if self.isString:
    #         text = '"' + ''.join(self.content) + '" '
    #     else:
    #         text = ''.join(self.content) + ' '
    #     image = futility.createBlank(len(text), 1)
    #     futility.putNodeOnImage2(image, 0, 0, text, None)
    #     image[0][self.index].bgColour = libtcod.azure
    #
    #     return image

class ColourScheme(TNode.FuncObject):

    def __init__(self, bgCol, symbolCol, stringCol, numberCol, activeHiCol, idleHiCol):
        self.bgCol = bgCol
        self.symbolCol = symbolCol
        self.stringCol = stringCol
        self.numberCol = numberCol
        self.activeHiCol = activeHiCol
        self.idleHiCol = idleHiCol


class TreeEditor(TNode.FuncObject):
    editors = 0

    def __init__(self, root, rootCursorAdd=[0], cursorAdd=[0], zippedNodes=None):
        #self.root = root
        self.buffer = TNode.Buffer(root, rootCursorAdd, cursorAdd)
        self.posx = 0
        self.posy = 0
        self.maxx = 80
        self.maxy = 50

        self.statusDescription = reader.Symbol('TreeEditor')
        self.editing = False
        self.cellEditor = None
        self.yankBuffer = None
        self.printingMode = 'code'
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

        self.colourScheme = ColourScheme(libtcod.black, libtcod.white,
                                         libtcod.light_green, libtcod.light_sky,
                                         libtcod.azure, libtcod.light_grey)

        # self.fgCol = libtcod.white
        # self.bgCol = libtcod.black

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


    def handleKeys(self, key, mouse):
        self.updateUndo = False
        self.statusBar.item1 = self.statusDescription
        self.statusBar.item2 = self.buffer.viewAdd
        self.statusBar.item3 = self.buffer.cursorAdd
        if key.c != 0:
            self.statusBar.message = None
        self.statusBar = self.statusBar.refreshStatus()

#        self.statusBar = self.statusBar.updateStatus(
#            [reader.Symbol('Editor')
#            ,self.buffer.viewAdd
#            ,self.buffer.cursorAdd])
        if mouse.lbutton_pressed:
            cell = self.image[mouse.cy - self.posy][mouse.cx - self.posx]

            if self.editing:
                if cell.lineItemNodeReference and cell.lineItemNodeReference.nodeReference == self.buffer.cursor:
                    self.cellEditor.handleClick(cell.characterReference)
                else:
                    print 'Clicked Outside'
                    # TODO: finish editing and move cursor

            elif cell.lineItemNodeReference:
                newBuff = self.buffer.cursorToAddress(cell.lineItemNodeReference.nodeAddress)
                return self.update('buffer', newBuff)
        elif mouse.wheel_down:
            self.topLine += 3
        elif mouse.wheel_up:
            if self.topLine > 2:
                self.topLine -= 3
            else:
                self.topLine = 0

#            try:
#                if self.buffer.cursor.nodeID in self.zippedNodes and self.zippedNodes[self.buffer.cursor.nodeID]:
#                    newBuff = self.buffer.curUp().curNextUpAlong()
#                else:
#                    newBuff = self.buffer.curNextUpAlong()
#                return self.update('buffer', newBuff)
#            except ValueError: pass

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
                if self.cellEditor.original == '':
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

            if key.vk == libtcod.KEY_ESCAPE:                                        # exit Editor
                return 'ESC'

            elif chr(key.c) == 'x':
                image = libtcod.image_load('fonts\\arial10x10.png')
                libtcod.image_blit(image, 0, 10, 10, libtcod.BKGND_DEFAULT, 2, 2, 0)
                libtcod.console_flush()
                time.sleep(2)


            elif chr(key.c) == 'b':     # Go back to the first expression in the list
                return self.update('buffer', self.buffer.curFirst())

            elif chr(key.c) == 'd':
                if self.buffer.cursor != self.buffer.root:
                    return self.updateList(
                        ('buffer', self.buffer.deleteAtCursor()),
                        ('yankBuffer', self.buffer.cursorToPySexp()),
                        ('updateUndo', True))

            elif chr(key.c) == 'c':
                if not self.buffer.onSubNode():
                    return self.updateList(
                        ('cellEditor', CellEditor(self.buffer.cursor.child)),
                        ('editing', True))

            elif chr(key.c) == 'a':
                if self.buffer.cursor != self.buffer.view:
                    newBuff = self.buffer.appendAtCursor('').curNext()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('cellEditor', CellEditor(Symbol(''))),
                        ('editing', True))

            # elif chr(key.c) == 'f':
            #     self.firstNode = self.buffer.cursor


            elif chr(key.c) == 'i':
                if self.buffer.cursor != self.buffer.view:    # maybe the correct behaviour is to sub and ins
                    newBuff = self.buffer.insertAtCursor('').curPrev()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('cellEditor', CellEditor(Symbol(''))),
                        ('editing', True))

            elif chr(key.c) == 'e':
                return self.update('buffer', self.buffer.curLast())

            elif chr(key.c) == 'G':
                lookupAddress = self.buffer.cursor.activeToPySexp()
                #newViewAddress = self.buffer.root.getNodeAtNVS(lookupAddress)
                newBuff = TNode.Buffer(self.buffer.root, lookupAddress)
                return self.update('buffer', newBuff)

            elif chr(key.c) == 'J':
                if self.buffer.onSubNode():
                    return self.update('buffer', self.buffer.viewToCursor())

            elif chr(key.c) == 'K':
                try:
                    return self.update('buffer', self.buffer.viewUp())
                except ValueError: pass

            elif chr(key.c) == 'H':
                try:
                    return self.update('buffer', self.buffer.viewPrev())
                except ValueError: pass

            elif chr(key.c) == 'L':
                try:
                    return self.update('buffer', self.buffer.viewNext())
                except ValueError: pass

            elif chr(key.c) == '(':
                return self.updateList(
                    ('buffer', self.buffer.nestCursor()),
                    ('updateUndo', True))

            elif chr(key.c) == ')':
                if self.buffer.onSubNode() and self.buffer.cursor != self.buffer.root:
                    return self.updateList(
                        ('buffer', self.buffer.denestCursor()),
                        ('updateUndo', True))

            elif chr(key.c) == 'o':
                if self.buffer.cursor != self.buffer.view:
                    newBuff = self.buffer.appendAtCursor(['']).curNext().curChild()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('cellEditor', CellEditor(Symbol(''))),
                        ('editing', True))

            elif chr(key.c) == 'O':
                if self.buffer.cursor != self.buffer.view:
                    newBuff = self.buffer.insertAtCursor(['']).curPrev().curChild()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('cellEditor', CellEditor(Symbol(''))),
                        ('editing', True))

            elif chr(key.c) == 'm':
                modes = ['code', 'horizontal', 'vertical']
                if self.printingMode == 'help':
                    currentModePos = 2
                else:
                    currentModePos = modes.index(self.printingMode)
                self.printingMode = modes[(currentModePos + 1) % len(modes)]
                self.statusBar.displayMessage("DisplayMode: " + self.printingMode)


            elif chr(key.c) == 'N':
                newBuff = TNode.Buffer(self.buffer.root, [0], [0, 0]).curLast()
                newBuff = newBuff.appendAtCursor([reader.Symbol('newNode')]).curNext()
                newBuff = newBuff.viewToCursor().curChild()
                self.topLine = 0
                return self.update('buffer', newBuff)

            elif chr(key.c) == 'p':
                toInsert = TNode.createTreeFromSexp(self.yankBuffer)
                return self.updateList(
                    ('buffer', self.buffer.appendAtCursor(toInsert)),
                    ('updateUndo', True))

            elif chr(key.c) == 'P':
                toInsert = TNode.createTreeFromSexp(self.yankBuffer)
                return self.updateList(
                    ('buffer', self.buffer.insertAtCursor(toInsert)),
                    ('updateUndo', True))

            #elif chr(key.c) == 'q':
            #    var = self.buffer.cursor.child
            #    value = self.buffer.findLexicalValue(var)
            #    return self.update('yankBuffer', value)

            elif chr(key.c) == 'R':
                return self.update('buffer', self.buffer.viewToRoot())

            elif chr(key.c) == 's':
                return self.updateList(
                    ('cellEditor', CellEditor(Symbol(''))),
                    ('editing', True))

            elif chr(key.c) == 't':
                self.topLine += 1

            elif chr(key.c) == 'T':
                if self.topLine > 0:
                    self.topLine -= 1

            elif chr(key.c) == 'u':
                return "UNDO"

            elif chr(key.c) == 'y':
                self.yankBuffer = self.buffer.cursorToPySexp()
                print self.yankBuffer

            elif chr(key.c) == 'z':
                if self.buffer.cursor.nodeID in self.zippedNodes:
                    self.zippedNodes[self.buffer.cursor.nodeID] = not(self.zippedNodes[self.buffer.cursor.nodeID])
                else:
                    self.zippedNodes[self.buffer.cursor.nodeID] = True

            elif chr(key.c) == "'":
                #return self.update('buffer', self.buffer.quoteAtCursor())
                newBuff = self.buffer.nestCursor().curChild().insertAtCursor(Symbol('quote'))
                return self.update('buffer', newBuff)
#                if self.buffer.cursor.evaled:
#                    self.buffer.cursor.evaled = False
#                else: self.buffer.cursor.evaled = True

            elif chr(key.c) == '+':
                numList = self.buffer.cursorToPySexp()
                result = reduce(operator.add, numList)
                newBuff = self.buffer.replaceAtCursor(result)
                #result = Eval.eval(self.buffer)
                #return self.update('yankBuffer', result)
                return self.updateList(
                    ('buffer', newBuff),
                    ('updateUndo', True))


            elif chr(key.c) == '"':
                return self.updateList(
                    ('buffer', self.buffer.toggleStringAtCursor()),
                    ('updateUndo', True))

            elif chr(key.c) == '=':
                #return self.update()
                if self.buffer.cursor in self.revealedNodes:
                    self.revealedNodes[self.buffer.cursor] = not(self.revealedNodes[self.buffer.cursor])
                else:
                    self.revealedNodes[self.buffer.cursor] = True
#                if self.buffer.cursor.displayValue:
#                    self.buffer.cursor.displayValue = False
#                else: self.buffer.cursor.displayValue = True

            # Go to help pages, will need to be updated
            elif chr(key.c) == '?':
                helpIter, helpAddress = self.buffer.root.gotoNodeAtNVS(['origin', 'help'])
                newBuff = TNode.Buffer(self.buffer.root, helpAddress)
                self.printingMode = 'help'
                return self.update('buffer', newBuff)


            # Save the current state of the image
            elif key.vk == libtcod.KEY_F2:
                zipped, zipAdd = self.buffer.root.gotoNodeAtNVS(['origin', 'editor', 'zipped'])
                zipAdd += [1]
                #newBuff = TNode.Buffer(self.buffer.root, [0], zipAdd)
                zipList = []
                for k, v in self.zippedNodes.iteritems():
                    if v is True:
                        zipList.append(k)
                newImage = TNode.replaceAdd(self.buffer.root, zipAdd, zipList)

                view, viewAdd = self.buffer.root.gotoNodeAtNVS(['origin', 'editor', 'address'])
                viewAdd += [1]
                viewList = self.buffer.viewAdd
                newImage = TNode.replaceAdd(newImage, viewAdd, viewList)

                cursor, cursorSaveAdd = self.buffer.root.gotoNodeAtNVS(['origin', 'editor', 'cursor'])
                cursorSaveAdd += [1]
                currentCursorAdd = self.buffer.cursorAdd
                newImage = TNode.replaceAdd(newImage, cursorSaveAdd, currentCursorAdd)

                newBuff = TNode.Buffer(newImage, self.buffer.viewAdd, self.buffer.cursorAdd)
                return self.update('buffer', newBuff)

            elif key.vk == libtcod.KEY_LEFT or chr(key.c) == 'h':
                try:
                    newBuff = self.buffer.curPrevUpAlong()
                    return self.update('buffer', newBuff)
                except ValueError: pass

            elif key.vk == libtcod.KEY_RIGHT or chr(key.c) == 'l':
                try:
                    if self.buffer.cursor.nodeID in self.zippedNodes and self.zippedNodes[self.buffer.cursor.nodeID]:
                        newBuff = self.buffer.curUp().curNextUpAlong()
                    else:
                        newBuff = self.buffer.curNextUpAlong()
                    return self.update('buffer', newBuff)
                except ValueError: pass


            elif key.vk == libtcod.KEY_DOWN or chr(key.c) == 'j':
                if self.buffer.onSubNode():
                    newBuff = self.buffer.curChild()
                    return self.update('buffer', newBuff)


            elif key.vk == libtcod.KEY_UP or chr(key.c) == 'k':
                try:
                    newBuff = self.buffer.curUp()
                    return self.update('buffer', newBuff)
                except ValueError: pass

        return self

    def draw(self, posx, posy, maxx, maxy, isActive):

        lineList = futility.createStucturalLineIndentList(self, maxx, maxy)
        self.topLine = lineList[0].lineNumber

        #fakeWin = futility.drawLineList(lineList, maxx, maxy, self.bgCol, self.fgCol, hlcol)
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
        #super(statusBar, self).__init__(*args, **kwargs)

        self.editing = False
        #self.cellEditor = None
        self.printingMode = 'horizontal'
        self.zippedNodes = {}
        self.statusBar = None
        self.item1 = None
        self.item2 = None
        self.item3 = None
        self.message = None
        self.topLine = 0
        self.bgCol = libtcod.white
        self.fgCol = libtcod.black

        self.colourScheme = ColourScheme(libtcod.white, libtcod.black,
                                         libtcod.darker_green, libtcod.darker_sky,
                                         libtcod.white, libtcod.white)

        status = TNode.TNode(TNode.createTreeFromSexp(
            [reader.Symbol('Editor')
            ,reader.Symbol('View')
            ,reader.Symbol('Address')]
        ))

        self.buffer = TNode.Buffer(status)

    def draw(self, posx, posy, maxx, maxy, isActive):
        return super(StatusBar, self).draw(posx, posy, maxx, maxy, isActive)

    def refreshStatus(self):
        statusList = [x for x in [self.item1, self.item2, self.item3, self.message] if x is not None]
        return self.updateStatus(statusList)

    def updateStatus(self, status):
        newStatus = TNode.Buffer(TNode.TNode(TNode.createTreeFromSexp(status)))
        return self.update('buffer', newStatus)

    def displayMessage(self, message):
        self.message = message
        self.buffer = self.buffer.curChild().curLast().appendAtCursor(message)