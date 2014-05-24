__author__ = 'chephren'
import libtcodpy as libtcod
import utility
import reader
import interp
import TNode
#import evalNode


class CellEditor(object):
    def __init__(self, content):
        self.content = list(str(content))
        self.index = 0
        # should check to make sure not a symbol
        if isinstance(content, str) and len(content) > 0 and content[0] == '"':
            self.isString = True
        else: self.isString = False

    def getContent(self):
        text = ''.join(self.content)
        if self.isString:
            text = '"' + text + '"'
        return reader.atom(text)

    def handle_key(self, key):

        if key.vk == libtcod.KEY_ENTER:
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
            self.isString = not(self.isString)

        elif key.vk == libtcod.KEY_SPACE:
            if self.isString:
                self.content.insert(self.index, chr(key.c))
                self.index += 1
            else: return 'SPACE'

        #elif chr(key.c).isalnum():
        elif key.c != 0:
            self.content.insert(self.index, chr(key.c))
            self.index += 1

    def draw(self, pen):
        if self.isString:
            pen.writeHL('"' + ''.join(self.content) + '" ', libtcod.azure, self.index+1)
        else:
            pen.writeHL(''.join(self.content) + ' ', libtcod.azure, self.index)


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
        self.statusBar = None
#        self.env = None
#        self.context = None
        self.revealedNodes = {}
        self.zippedNodes = {}

        self.id = TreeEditor.editors
        TreeEditor.editors += 1


    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            return self.update('buffer', self.buffer.syncToNewRoot(newImageRoot))
        else:
            return self

    def handleKeys(self, key):
        self.updateUndo = False

        if self.editing:
            finished = self.cellEditor.handle_key(key)
            if finished == 'END':
                return self.updateList(
                    ('buffer', self.buffer.replaceAtCursor(self.cellEditor.getContent())),
                    ('editing', False),
                    ('updateUndo', True))

            elif finished == 'CANCEL':
                #if self.active.element == '':
                    #delete self
                return self.updateList(
                    ('buffer', self.buffer.deleteAtCursor()),
                    ('editing', False)
                )

            elif finished == 'SPACE':
                ## ideal: self.buffer.spliceAtCursor([self.cellEditor.getContent(), ''], [1])
                newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
                newBuff2 = newBuff.appendAtCursor('').curNext()
                return self.updateList(
                    ('buffer', newBuff2),
                    ('cellEditor', CellEditor('')))

            elif finished == 'NEST':
                if self.cellEditor.content:
                    newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
                    newBuff2 = newBuff.appendAtCursor(['']).curNext().curChild()
                else:
                    newBuff2 = self.buffer.replaceAtCursor(['']).curChild()

                return self.updateList(
                    ('buffer', newBuff2),
                    ('cellEditor', CellEditor('')))

            elif finished == 'UNNEST':
                if self.cellEditor.content:
                    newBuff = self.buffer.replaceAtCursor(self.cellEditor.getContent())
                else:
                    newBuff = self.buffer.deleteAtCursor()

                newBuff2 = newBuff.curUp()
                newBuff3 = newBuff2.appendAtCursor('').curNext()

                return self.updateList(
                    ('buffer', newBuff3),
                    ('cellEditor', CellEditor('')))

        else:

            # For the case when our active node gets deleted by another editor
            # Not perfect, but will do for now

            #self.cursor = self.cursor.refreshToNearest()

            if key.vk == libtcod.KEY_ESCAPE:
                return 'ESC'  # exit Editor

            # evaluate the current context
            #elif key.vk == libtcod.KEY_ENTER:

                #sexpToEval = self.active.activeToPySexp()
                #evalResult = interp.eval(sexpToEval)

                #self.active.nestChild()
                #self.active.child.insertAfter(TNode.createTreeFromSexp(evalResult))
                #self.active.child.insertBefore("=>")  #needs to go after as will change child

            elif key.vk == 'x' and key.lctrl:
                print "evaluating"

            elif chr(key.c) == 'b':
                return self.update('buffer', self.buffer.cursorToFirst())

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
                        ('cellEditor', CellEditor('')),
                        ('editing', True))

            elif chr(key.c) == 'i':
                if self.buffer.cursor != self.buffer.view:    # maybe the correct behaviour is to sub and ins
                    newBuff = self.buffer.insertAtCursor('').curPrev()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('cellEditor', CellEditor('')),
                        ('editing', True))

            elif chr(key.c) == 'e':
                return self.update('buffer', self.buffer.curLast())

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
                        ('cellEditor', CellEditor('')),
                        ('editing', True))

            elif chr(key.c) == 'O':
                if self.buffer.cursor != self.buffer.view:
                    newBuff = self.buffer.insertAtCursor(['']).curPrev().curChild()
                    return self.updateList(
                        ('buffer', newBuff),
                        ('cellEditor', CellEditor('')),
                        ('editing', True))

            elif chr(key.c) == 'm':
                if self.printingMode == 'horizontal':
                    self.printingMode = 'vertical'
                else:
                    self.printingMode = 'horizontal'
                print "print mode is set to:", self.printingMode

            elif chr(key.c) == 'p':
                toInsert = TNode.createTreeFromSexp(self.yankBuffer)
                return self.updateList(
                    ('buffer', self.buffer.appendAtCursor(toInsert)),
                    ('updateUndo', True))

            elif chr(key.c) == 'R':
                return self.update('buffer', self.buffer.viewToRoot())

            elif chr(key.c) == 's':
                return self.updateList(
                    ('cellEditor', CellEditor('')),
                    ('editing', True))

            elif chr(key.c) == 'u':
                return "UNDO"

            elif chr(key.c) == 'y':
                self.yankBuffer = self.buffer.cursorToPySexp()
                print self.yankBuffer

            elif chr(key.c) == 'z':
                if self.buffer.cursor in self.zippedNodes:
                    self.zippedNodes[self.buffer.cursor] = not(self.zippedNodes[self.buffer.cursor])
                else:
                    self.zippedNodes[self.buffer.cursor] = True

            elif chr(key.c) == "'":
                return self.update('buffer', self.buffer.quoteAtCursor())
#                if self.buffer.cursor.evaled:
#                    self.buffer.cursor.evaled = False
#                else: self.buffer.cursor.evaled = True

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

            elif key.vk == libtcod.KEY_LEFT or chr(key.c) == 'h':
                try:
                    newBuff = self.buffer.curPrevUpAlong()
                    return self.update('buffer', newBuff)
                except ValueError: pass

            elif key.vk == libtcod.KEY_RIGHT or chr(key.c) == 'l':
                try:
                    if self.buffer.cursor in self.zippedNodes and self.zippedNodes[self.buffer.cursor]:
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

        def drawHorizontal(posx, posy, hlcol, indent=True):
            pen = utility.Pen(posx, posy, maxx, maxy)

            def drawChild(node, nesting, parentCol=libtcod.black):



                if not node.evaled:
                    pen.write("'", parentCol)

                if node.isSubNode():
                    if node.child == "=>":
                        pen.writeNL()
                        # check view
                    if node == self.buffer.cursor:
                        bgcolour = hlcol
                    else:
                        bgcolour = parentCol

                    pen.write('(', bgcolour)
                    drawr(node.child, nesting, bgcolour)
                    pen.write(')', bgcolour)

                elif node.child is not None:
                    output = reader.to_string(node.child)
                    if node == self.buffer.cursor:

                        if self.editing:
                            self.cellEditor.draw(pen)
                        else:
                            pen.write(output, hlcol)

                    else:
                        pen.write(output, parentCol)



#                #if node.displayValue:
#                if node in self.revealedNodes:
#                    pen.write("=>", parentCol)
#                    pen.write(reader.to_string(node.getValue(self.id)), parentCol)

            def drawr(node, nesting, parentCol=libtcod.black, reindent=False):

                try:
                    if self.zippedNodes[node]:
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

#
#class statusBar(TreeEditor):
#    def __init__(self, *args, **kwargs):
#        #super(statusBar, self).__init__(*args, **kwargs)
#        self.buffer =