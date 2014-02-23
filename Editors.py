__author__ = 'chephren'
import libtcodpy as libtcod
import utility
import reader
import interp
import TNode
import copy
from TNode import Cursor

class CellEditor(object):
    def __init__(self, content):
        self.content = list(str(content))
        self.index = 0

    def getContent(self):
        text = ''.join(self.content)
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

        elif key.vk == libtcod.KEY_SPACE:
            #print 'space'
            return 'SPACE'

        #elif chr(key.c).isalnum():
        elif key.c != 0:
            self.content.insert(self.index, chr(key.c))
            self.index += 1

    def draw(self, pen):
        pen.writeHL(''.join(self.content), libtcod.azure, self.index)


class TreeEditor(object):
    editors = 0

    def __init__(self, rootCursor, cursor = None):
        self.rootCursor = rootCursor
        self.curRoot = rootCursor.active  # a shortcut i guess.
#        self.root = root
#
#        if curRoot:
#            self.curRoot = curRoot
#        else:
#            self.curRoot = self.root

#        if cursor:
#            self.active = curRoot.gotoNearestAddress(cursor)
#            self.activeAddress = cursor
#        else:
#            self.active = self.curRoot
#            self.activeAddress = [0]

        self.cursor = Cursor(self.curRoot, [0])
        #self.active = self.cursor.active

        self.editing = False
        self.cellEditor = None
        self.yankBuffer = None
        self.printingMode = 'horizontal'
        self.showValues = False
        self.env = None
        self.context = None

        self.id = TreeEditor.editors
        TreeEditor.editors += 1


    def cursorReplace(self, value):
        newRoot = TNode.replaceAdd(self.curRoot, self.cursor.address, value)
        newCur = TNode.Cursor(newRoot, self.cursor.address)
        return newRoot, newCur


    def transform(self, *propValueList):
        newSelf = copy.copy(self)
        #changes = []
        for (prop, val) in propValueList:
            setattr(newSelf, prop, val)
        return newSelf




    def handleKeys(self, key):

        if self.editing:
            finished = self.cellEditor.handle_key(key)
            if finished == 'END':
                #self.active.child = self.cellEditor.getContent()
                self.curRoot = TNode.replaceAdd(self.curRoot, self.cursor.address, self.cellEditor.getContent())
                self.cursor = TNode.Cursor(self.curRoot, self.cursor.address)
                print self.curRoot.toPySexp()
                self.editing = False
            elif finished == 'CANCEL':
                #if self.active.element == '':
                    #delete self

                self.editing = False
            elif finished == 'SPACE':
                self.curRoot = TNode.replaceAdd(self.curRoot, self.cursor.address, self.cellEditor.getContent())
                self.curRoot = TNode.appendAdd(self.curRoot, self.cursor.address, '')
                self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).next()
                self.cellEditor = CellEditor(self.cursor.active.child)

            elif finished == 'NEST':
                if self.cellEditor.content:
                    self.curRoot = TNode.replaceAdd(self.curRoot, self.cursor.address, self.cellEditor.getContent())
                    self.curRoot = TNode.appendAdd(self.curRoot, self.cursor.address, [''])
                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).next().child()
                else:
                    self.curRoot = TNode.replaceAdd(self.curRoot, self.cursor.address, [''])
                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).child()

                self.cellEditor = CellEditor(self.cursor.active.child)

            elif finished == 'UNNEST':
                if self.cellEditor.content:
                    self.active.child = self.cellEditor.getContent()
                    if self.active.parent:
                        self.active = self.active.parent
                    self.active.insertAfter('')
                    self.active = self.active.next

                self.cellEditor = CellEditor(self.active.child)
        else:

            # For the case when our active node gets deleted by another editor
            # Not perfect, but will do for now

            self.cursor = self.cursor.refreshToNearest()

            if key.vk == libtcod.KEY_ESCAPE:
                return 'ESC'  # exit Editor

            # evaluate the current context
            elif key.vk == libtcod.KEY_ENTER:

                sexpToEval = self.active.activeToPySexp()
                evalResult = interp.eval(sexpToEval)

                self.active.nestChild()
                self.active.child.insertAfter(TNode.createTreeFromSexp(evalResult))
                self.active.child.insertBefore("=>")  #needs to go after as will change child

            elif key.vk == 'x' and key.lctrl:
                print "evaluating"

            elif chr(key.c) == 'd':
                if self.cursor.active != self.rootCursor.root:
                    if self.cursor.active == self.curRoot:
                        # set curRoot.Child to the first node in the outer list
                        self.curRoot = self.curRoot.parent

                    self.yankBuffer = self.cursor.childToPySexp()

                    self.curRoot = TNode.deleteAdd(self.curRoot, self.cursor.address)
                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address)


            elif chr(key.c) == 'c':
                if not self.active.isSubNode():
                    self.editing = True
                    self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'a':
                if self.cursor.active != self.curRoot:
                    self.editing = True
                    #self.active.insertAfter('')

                    self.curRoot = TNode.appendAdd(self.curRoot, self.cursor.address, '')

                    # Need to think about how to sync with other editors, e.g.
                    # return the new list and recreate the editor with new root and old cursor address

                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).next()
                    self.cellEditor = CellEditor(self.cursor.active.child)

            elif chr(key.c) == 'i':
                if self.active != self.curRoot:    # maybe the correct behaviour is to sub and ins
                    self.editing = True
#                    self.active.insertBefore('')
#                    self.active = self.active.previous
                    self.curRoot = TNode.appendAdd(self.curRoot, self.cursor.address, '')
                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).next()
                    self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'J':
                if self.active.isSubNode():
                    self.curRoot = self.active

            elif chr(key.c) == 'K':
                if self.curRoot.parent:
                    # set curRoot to the first node in the outer list
                    self.curRoot = self.curRoot.parent

            elif chr(key.c) == 'L':
                if self.curRoot.next:
                    self.curRoot = self.curRoot.next
                    self.active = self.curRoot

            elif chr(key.c) == '(':
                self.active.nestChild()


            elif chr(key.c) == 'o':
                if self.cursor.active != self.curRoot:
                    self.editing = True
#                    self.active.insertAfter('')
#                    self.active = self.active.next
#                    self.active.nestChild()
#                    self.active = self.active.child
                    # return self.transform('curRoot', self.appendAdd(['']),
                    # 'cursor', self.cursor.next().child()
                    # 'cellEditor', CellEditor(self.cursor...
                    # okay try again
                    # newRoot, newCur = cursorAppend([''])
                    # newCur = Cursor(newRoot, self.cursor.address).next().child()
                    # return self.transform('curRoot', newRoot, 'cursor', newCur, 'cellEditor', '')
                    self.curRoot = TNode.appendAdd(self.curRoot, self.cursor.address, [''])
                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).next().child()
                    self.cellEditor = CellEditor(self.cursor.active.child)

            elif chr(key.c) == 'O':
                if self.cursor.active != self.curRoot:
                    self.editing = True
                    self.curRoot = TNode.insertAdd(self.curRoot, self.cursor.address, [''])
                    self.cursor = TNode.Cursor(self.curRoot, self.cursor.address).prev().child()
                    self.cellEditor = CellEditor(self.cursor.active.child)

            elif chr(key.c) == 'm':
                if self.printingMode == 'horizontal':
                    self.printingMode = 'vertical'
                else:
                    self.printingMode = 'horizontal'
                print "print mode is set to:", self.printingMode

            elif chr(key.c) == 'p':
                toInsert = TNode.createTreeFromSexp(self.yankBuffer)
                self.active.insertAfter(toInsert)

            elif chr(key.c) == 'R':
                self.active = self.curRoot

            elif chr(key.c) == 's':
                if self.active.child:
                    self.editing = True
                    self.cellEditor = CellEditor('')
                #otherwise delete and replace


            elif chr(key.c) == 'y':
                self.yankBuffer = self.active.activeToSexpr()
                print self.yankBuffer

            elif chr(key.c) == "'":
                if self.active.evaled:
                    self.active.evaled = False
                else: self.active.evaled = True

            elif chr(key.c) == '=':
                if self.active.displayValue:
                    self.active.displayValue = False
                else: self.active.displayValue = True

            elif key.vk == libtcod.KEY_LEFT or chr(key.c) == 'h':
                try:
                    self.cursor = self.cursor.prev()
                except ValueError: pass

            elif key.vk == libtcod.KEY_RIGHT or chr(key.c) == 'l':
                try:
                    #self.active = self.active.getNextUpAlong('next', self.curRoot)
                    self.cursor = self.cursor.next()
                except ValueError: pass


            elif key.vk == libtcod.KEY_DOWN or chr(key.c) == 'j':
                if self.cursor.onSubNode():
                    self.cursor = self.cursor.child()


            elif key.vk == libtcod.KEY_UP or chr(key.c) == 'k':
                try:
                    self.cursor = self.cursor.up()
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
                    if node == self.cursor.active:
                        bgcolour = hlcol
                    else:
                        bgcolour = parentCol

                    pen.write('(', bgcolour)
                    drawr(node.child, nesting, bgcolour)
                    pen.write(')', bgcolour)

                elif node.child is not None:
                    output = reader.to_string(node.child)
                    if node == self.cursor.active:

                        if self.editing:
                            self.cellEditor.draw(pen)
                        else:
                            pen.write(output, hlcol)

                    else:
                        pen.write(output, parentCol)

                if node.displayValue:
                    pen.write("=>", parentCol)
                    pen.write(reader.to_string(node.getValue(self.id)), parentCol)

            def drawr(node, nesting, parentCol=libtcod.black, reindent=False):
                drawChild(node, nesting + 1, parentCol)
                #reindent = False

                if not node.previous and node.next and node.next.next:
                    for i in node.next:
                        if i.isSubNode():
                            reindent = True


                if node.next:
                    if indent and reindent:
                        pen.writeNL()
                        #pen.skip(2 * nesting, 0)
                        pen.write(' ' * (2 * nesting), parentCol)

                    # try to avoid hiding the cursor in a cell editor
                    elif node == self.cursor.active and self.editing:
                        pen.skip(1, 0)
                    else:
                        pen.write(' ', parentCol)

                    drawr(node.next, nesting, parentCol, reindent)

            if self.curRoot.isSubNode():
                drawChild(self.curRoot, 1)
            else:
                pen.write(str(self.curRoot.child))


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

        if self.showValues:
            if self.context:
                args = []
                if self.context.next:
                    for i in self.context.next:
                        args.append(i.getValue(self.contextParent))
                (newTree, env) = self.context.getValue(self.contextParent)('inspect', *args)
                self.env = env

            self.root.calcValue(self.id, self.env)

        try:
            if self.printingMode == 'horizontal':
                drawHorizontal(posx, posy, hlcol)
            else:
                drawVert(posx, posy, 1)
        except utility.windowBorderException: pass

