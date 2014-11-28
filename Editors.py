__author__ = 'chephren'
import libtcodpy as libtcod
import utility
import futility
import reader
from reader import Symbol
import Eval
import TNode
import operator



class CellEditor(object):
    def __init__(self, content):
        self.original = str(content)
        self.content = list(str(content).encode('string_escape'))
        self.index = 0
        # should check to make sure not a symbol
        if not isinstance(content, Symbol): # and len(content) > 0 and content[0] == '"':
            self.isString = True
        else: self.isString = False

    def getContent(self):
        text = ''.join(self.content)
        if self.isString:
            text = '"' + text + '"'
        return reader.atom(text)

    def handle_key(self, key):

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

        elif chr(key.c) == '(':
            return 'NEST'

        elif chr(key.c) == ')':
            return 'UNNEST'

        elif chr(key.c) == '"':
            if not self.isString:
                self.isString = True
            else:
                temp = ''.join(self.content)
                if temp.find(' ') == -1:
                    self.isString = False

        elif key.vk == libtcod.KEY_SPACE:
            if self.isString:
                self.content.insert(self.index, chr(key.c))
                self.index += 1
            elif len(self.content) > 0:
                return 'SPACE'

        #elif chr(key.c).isalnum():
        elif key.c != 0:
            self.content.insert(self.index, chr(key.c))
            self.index += 1

    def draw(self, pen):
        if self.isString:
            pen.writeHL('"' + ''.join(self.content) + '" ', libtcod.azure, self.index+1)
        else:
            pen.writeHL(''.join(self.content) + ' ', libtcod.azure, self.index)

    def getImage(self):
        if self.isString:
            text = '"' + ''.join(self.content) + '" '
        else:
            text = ''.join(self.content) + ' '
        image = futility.createBlank(len(text), 1)
        futility.putNodeOnImage2(image, 0, 0, text, None)
        image[0][self.index].bgColour = libtcod.azure

        return image


class TreeEditor(TNode.FuncObject):
    editors = 0

    def __init__(self, root, rootCursorAdd=[0], cursorAdd=[0]):
        #self.root = root
        self.buffer = TNode.Buffer(root, rootCursorAdd, cursorAdd)

        self.editing = False
        self.cellEditor = None
        self.yankBuffer = None
        self.printingMode = 'horizontal'
        self.syncWithRoot = True
        self.updateUndo = False
        self.showValues = False
       # self.statusBar = None
#        self.env = None
#        self.context = None
        self.revealedNodes = {}
        self.zippedNodes = {}
        self.drawMode = 'cursor'
        self.topLine = 0
        self.firstNode = self.buffer.view
        self.topNode = self.buffer.cursorToFirst().curBottom().cursor
        self.image = None

#        status = TNode.TNode(TNode.createTreeFromSexp(
#                [reader.Symbol('Editor')
#                ,reader.Symbol('View')
#                ,reader.Symbol('Address')]
#        ))
        self.statusBar = StatusBar()

        self.id = TreeEditor.editors
        TreeEditor.editors += 1


    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            return self.update('buffer', self.buffer.syncToNewRoot(newImageRoot))
        else:
            return self

    def handleKeys(self, key, mouse):
        self.updateUndo = False
        self.statusBar.item1 = reader.Symbol('Editor')
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
            cell = self.image[mouse.cy][mouse.cx]
            if cell.lineItemNodeReference:
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
            finished = self.cellEditor.handle_key(key)
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

            if key.vk == libtcod.KEY_ESCAPE:
                return 'ESC'  # exit Editor

            # evaluate the current context
            elif key.vk == libtcod.KEY_ENTER:

                result = Eval.eval(self.buffer)
                self.statusBar.message = 'Result to buffer'
                return self.update('yankBuffer', result)

                #self.active.nestChild()
                #self.active.child.insertAfter(TNode.createTreeFromSexp(evalResult))
                #self.active.child.insertBefore("=>")  #needs to go after as will change child

            elif key.vk == 'x' and key.lctrl:
                print "evaluating"

            elif chr(key.c) == 'b':
                return self.update('buffer', self.buffer.curFirst())

            elif chr(key.c) == 'd':
                if self.buffer.cursor != self.buffer.root:
                    #self.yankBuffer = self.buffer.childToPySexp()
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

            elif chr(key.c) == 'f':
                self.firstNode = self.buffer.cursor


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
                return self.update('buffer', self.buffer.nestCursor())


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

#            elif chr(key.c) == 'm':
#                if self.printingMode == 'horizontal':
#                    self.printingMode = 'vertical'
#                else:
#                    self.printingMode = 'horizontal'
#                print "print mode is set to:", self.printingMode

            elif chr(key.c) == 'N':
                newBuff = TNode.Buffer(self.buffer.root, [0], [0, 0]).curLast()
                newBuff = newBuff.appendAtCursor([reader.Symbol('newNode')]).curNext()
                newBuff = newBuff.viewToCursor().curChild()
                return self.update('buffer', newBuff)

            elif chr(key.c) == 'p':
                toInsert = TNode.createTreeFromSexp(self.yankBuffer)
                return self.updateList(
                    ('buffer', self.buffer.appendAtCursor(toInsert)),
                    ('updateUndo', True))

            elif chr(key.c) == 'q':
                var = self.buffer.cursor.child
                value = self.buffer.findLexicalValue(var)
                return self.update('yankBuffer', value)

            elif chr(key.c) == 'R':
                return self.update('buffer', self.buffer.viewToRoot())

            elif chr(key.c) == 's':
                return self.updateList(
                    ('cellEditor', CellEditor(Symbol(''))),
                    ('editing', True))

            elif chr(key.c) == 't':
                self.topLine += 1
                #print self.buffer.root.getNodeAtNVS(['origin', 'editor', 'address']).toPySexp()
#                op = lambda addNode: TNode.cons('test', addNode)
#                newImage = TNode.opAtNVSAdd(self.buffer.root, ['origin', 'editor', 'cursor'], op)
#                newBuff = TNode.Buffer(newImage)
#                return self.update('buffer', newBuff)

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
                    ('updateUndo', True)
                )


            elif chr(key.c) == '"':
                return self.updateList(
                    ('buffer', self.buffer.toggleStringAtCursor()),
                    ('updateUndo', True)
                )

            elif chr(key.c) == '=':
                #return self.update()
                if self.buffer.cursor in self.revealedNodes:
                    self.revealedNodes[self.buffer.cursor] = not(self.revealedNodes[self.buffer.cursor])
                else:
                    self.revealedNodes[self.buffer.cursor] = True
#                if self.buffer.cursor.displayValue:
#                    self.buffer.cursor.displayValue = False
#                else: self.buffer.cursor.displayValue = True

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

    def draw(self, posx, posy, maxx, maxy, hlcol):

        lineList = futility.createStucturalLineIndentList(self, 80, 50)
        self.topLine = lineList[0].lineNumber

        fakeWin = futility.drawLineList(lineList, 80, 50)
        #self.topNode = lineList[0].nodeList[0].nodeReference
        #self.topNode = self.buffer.cursorToFirst().curBottom().cursor
        #self.bottomNode = lineList[-1].nodeList[-1].nodeReference

        finalWin = futility.sliceFakeWindow(fakeWin, 0, maxy)
        self.image = finalWin

        futility.printToScreen(finalWin)


    def draw2(self, posx, posy, maxx, maxy, hlcol):

        def drawHorizontal(posx, posy, hlcol, indent=True):
            pen = utility.Pen(posx, posy, maxx, maxy-1, self.topLine)
            firstNodeSeen = False

            def drawChild(node, nesting, parentCol=libtcod.black):

                if not node.evaled:
                    pen.write("'", parentCol)

                if node == self.buffer.cursor:
#                    if self.topLine > pen.y1:
#                        self.topLine = pen.y1
#                    if self.topLine + maxy < pen.y1:
#                        self.topLine = pen.y1 - maxy
                    bgcolour = hlcol
                    firstNodeSeen = True
                else:
                    bgcolour = parentCol


                if node.isSubNode():


#                    if node.child.child == "quote" and node.child.next and not node.child.next.next:
#                        pen.write("'", bgcolour)
#                        drawr(node.child.next, nesting, bgcolour)
#                    else:
                    if node.child.child == "=>":
                        pen.writeNL()
                    pen.write('(', bgcolour)
                    drawr(node.child, nesting, bgcolour)
                    pen.write(')', bgcolour)

                elif node.child is None:
                    pen.write('()', bgcolour)

                else:
                    output = reader.to_string(node.child)

                    if node == self.buffer.cursor and self.editing:
                        self.cellEditor.draw(pen)
                    else:
                        pen.write(output, bgcolour)


            def drawr(node, nesting, parentCol=libtcod.black, reindent=False):

                try:
                    if self.zippedNodes[node.nodeID]:
                        pen.write("...", hlcol if node == self.buffer.cursor else parentCol)
                        return
                except KeyError: pass

                drawChild(node, nesting + 1, parentCol)
                #reindent = False

                if node.next and node.next.next:
                    for i in node.next:
                        if i.isSubNode():
                            for subi in i.child:
                                if subi.isSubNode(): reindent = True


                if node.next:
                    if indent and reindent:
                        pen.writeNL()
                        #pen.skip(2 * nesting, 0)
                        pen.write(' ' * (2 * nesting), parentCol)

                    # try to avoid hiding the cursor in a cell editor
                    #elif node == self.buffer.cursor and self.editing:
                    #    pen.skip(1, 0)
                    else:
                        pen.write(' ', parentCol)

                    drawr(node.next, nesting, parentCol, reindent)

            if self.buffer.view.isSubNode():
                drawChild(self.buffer.view, 1)
            else:
                pen.write(str(self.buffer.view.child))

            if self.statusBar:
                self.statusBar.draw(0, maxy - 1, maxx, maxy, libtcod.darker_gray)


        def drawVert(posx, posy, levels):
            pen = utility.Pen(posx, posy)

            def drawr(node, nesting, parentCol=libtcod.black,):

                if node.isSubNode():
                    if node == self.active:
                        bgcolour = libtcod.azure
                    else:
                        bgcolour = parentCol

                    pen.write('(', bgcolour)
                    drawr(node.child, nesting + 1, bgcolour)
                    pen.write(')', bgcolour)
                else:
                    output = str(node.child)
                    if node == self.active:

                        if self.editing:
                            self.cellEditor.draw(pen)
                        else:
                            pen.write(output, libtcod.azure)

                    else:
                        pen.write(output, parentCol)

                if node.next:
                    if nesting == levels:
                        pen.writeNL()
                    elif node == self.active and self.editing:
                        pen.write(' ', libtcod.azure)
                    else:
                        pen.write(' ', parentCol)
                    drawr(node.next, nesting, parentCol)

            drawr(self.curRoot, 0)

#        if self.showValues:
#            if self.context:
#                args = []
#                if self.context.next:
#                    for i in self.context.next:
#                        args.append(i.getValue(self.contextParent))
#                (newTree, env) = self.context.getValue(self.contextParent)('inspect', *args)
#                self.env = env
#
#            self.root.calcValue(self.id, self.env)

        try:
            if self.printingMode == 'horizontal':
                drawHorizontal(posx, posy, hlcol)
            else:
                drawVert(posx, posy, 1)
        except utility.windowBorderException: pass




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

        status = TNode.TNode(TNode.createTreeFromSexp(
            [reader.Symbol('Editor')
            ,reader.Symbol('View')
            ,reader.Symbol('Address')]
        ))

        self.buffer = TNode.Buffer(status)

    def refreshStatus(self):
        statusList = [x for x in [self.item1, self.item2, self.item3, self.message] if x is not None]
        return self.updateStatus(statusList)

    def updateStatus(self, status):
        newStatus = TNode.Buffer(TNode.TNode(TNode.createTreeFromSexp(status)))
        return self.update('buffer', newStatus)

    def displayMessage(self, message):
        self.message = message
        self.buffer = self.buffer.curChild().curLast().appendAtCursor(message)