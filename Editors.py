__author__ = 'chephren'
import libtcodpy as libtcod
import utility
import reader
import interp
import TNode

class CellEditor(object):
    def __init__(self, content):
        self.content = list(str(content))
        self.index = 0

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

        elif chr(key.c) == '(' or chr(key.c) == ')':
            return 'NEST'

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
    def __init__(self):
        self.root = None
        self.curRoot = None
        self.active = None
        self.editing = False
        self.cellEditor = None
        self.yankBuffer = None
        self.printingMode = 'horizontal'

    def writeImage(self):

        f = open("image", 'w')

        def writer(node):
            if node.isSubNode():
                f.write('(')
                writer(node.child)
                f.write(')')
            else:
                output = str(node.child)
                f.write(output)

            if node.next:
                f.write(' ')
                writer(node.next)

        if self.root.isSubNode():
            writer(self.root)

        f.close()

    def loadImage(self):

        f = open("image", 'r')
        buf = f.read()

        output = reader.read(buf)
        print output

    def handleKeys(self, key):

        if self.editing:
            finished = self.cellEditor.handle_key(key)
            if finished == 'END':
                self.active.child = ''.join(self.cellEditor.content)
                self.editing = False
            elif finished == 'CANCEL':
                #if self.active.element == '':
                    #delete self

                self.editing = False
            elif finished == 'SPACE':
                self.active.child = ''.join(self.cellEditor.content)

                self.active.insertAfter('')
                self.active = self.active.next
                self.cellEditor = CellEditor(self.active.child)

            elif finished == 'NEST':
                print len(self.cellEditor.content)
                if self.cellEditor.content:
                    self.active.child = ''.join(self.cellEditor.content)
                    self.active.insertAfter('')
                    self.active = self.active.next

                # from 'o' command
                self.active.nestChild()
                self.active = self.active.child
                self.cellEditor = CellEditor(self.active.child)
        else:

            if key.vk == libtcod.KEY_ESCAPE:
                self.writeImage()
                return True  # exit Editor

            # evaluate the current context
            elif key.vk == libtcod.KEY_ENTER:

                sexpToEval = self.active.activeToPySexp()
                evalResult = interp.eval(sexpToEval)

                self.active.nestChild()
                self.active.child.insertAfter(TNode.createTreeFromSexp(evalResult))
                self.active.child.insertBefore("=>")  #needs to go after as will change child

                # move down a line

                #reset the writer
                #self.root = None

            elif chr(key.c) == 'd':
                self.yankBuffer = self.active.activeToPySexp()
                newActive = self.active.removeSelf()


                # Deleting the last node
                #if self.active == newActive:


                if self.root == self.active:
                    self.root.child = None

                if newActive:
                    if self.root.child == self.active:
                        self.root.child = self.active.next
                    self.active = newActive

            elif chr(key.c) == 'c':
                if not self.active.isSubNode():
                    self.editing = True
                    self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'a':
                self.editing = True
                self.active.insertAfter('')
                self.active = self.active.next
                self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'i':
                if self.active != self.root:    # maybe the correct behaviour is to sub and ins
                    self.editing = True
                    self.active.insertBefore('')
                    self.active = self.active.previous
                    self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'G':
                self.curRoot = self.active

            elif chr(key.c) == '(':
                self.active.nestChild()


            elif chr(key.c) == 'o':
                self.editing = True
                self.active.insertAfter('')
                self.active = self.active.next
                self.active.nestChild()
                self.active = self.active.child
                self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'O':
                self.editing = True
                self.active.insertBefore('')
                self.active = self.active.previous
                self.active.nestChild()
                self.active = self.active.child
                self.cellEditor = CellEditor(self.active.child)

            elif chr(key.c) == 'm':
                if self.printingMode == 'horizontal':
                    self.printingMode = 'vertical'
                else:
                    self.printingMode = 'horizontal'
                print "print mode is set to:", self.printingMode

            elif chr(key.c) == 'p':
                toInsert = TNode.createTreeFromSexp(self.yankBuffer)
                self.active.insertAfter(toInsert)

            elif chr(key.c) == 's':
                if self.active.child:
                    self.editing = True
                    self.cellEditor = CellEditor('')
                #otherwise delete and replace


            elif chr(key.c) == 'y':
                self.yankBuffer = self.active.activeToSexpr()
                print self.yankBuffer

            elif key.vk == libtcod.KEY_LEFT or chr(key.c) == 'h':
                if self.active.previous:
                    self.active = self.active.previous

            elif key.vk == libtcod.KEY_RIGHT or chr(key.c) == 'l':
                if self.active.next:
                    self.active = self.active.next

            elif key.vk == libtcod.KEY_DOWN or chr(key.c) == 'j':
                if self.active.isSubNode():
                    self.active = self.active.child

            elif key.vk == libtcod.KEY_UP or chr(key.c) == 'k':
                if self.active.parent:
                    self.active = self.active.parent

    def draw(self, posx, posy):
        if self.printingMode == 'horizontal':
            self.drawHorizontal(posx, posy)
        else:
            self.drawVert(posx, posy, 1)

    def drawHorizontal(self, posx, posy):
        pen = utility.Pen(posx, posy)

        def drawr(node, parentCol=libtcod.black):
            if node.isSubNode():
                if node.child.child == "=>":
                    pen.writeNL()
                if node == self.active:
                    bgcolour = libtcod.azure
                else:
                    bgcolour = parentCol

                pen.write('(', bgcolour)
                drawr(node.child, bgcolour)
                pen.write(')', bgcolour)
            elif node.child is not None:
                output = str(node.child)
                if node == self.active:

                    if self.editing:
                        self.cellEditor.draw(pen)
                    else:
                        pen.write(output, libtcod.azure)

                else:
                    pen.write(output, parentCol)

            if node.next:
                if node == self.active and self.editing:
                    pen.skip(1, 0)
                else:
                    pen.write(' ', parentCol)

                drawr(node.next, parentCol)

        if self.root.isSubNode():
            drawr(self.root)
        else:
            pen.write(str(self.root.child))


    def drawVert(self, posx, posy, levels):
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

        drawr(self.root, 0)



