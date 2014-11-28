__author__ = 'chephren'
import TNode
from TNode import cons, Buffer
import utility
import Editors
import libtcodpy as libtcod
import reader
import CodeEditor



# interface

class Window(object):
    def __init(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = libtcod.console_new(width, height)


class Column(object):
    def __init__(self, width, function):
        self.width = width
        self.function = function
        self.rows = None

    #def widthIncrease(self, x):

    #def widthDecrease(self, x)

    def draw(self, x, y):
        self.function.draw(x, y)

    def handleKeys(self, key):
        result = self.function.handleKeys(key)
        if result:
            return True



class WindowManager(TNode.FuncObject):
    def __init__(self, ImageRoot):
        self.ImageRoot = ImageRoot

        # root of windows
        winRoot = TNode.TNode(self.parse_memory(ImageRoot))
        self.winTree = Buffer(winRoot, [0], [0, 0])
        self.winCmd = False
        self.cols = 1
        self.wins = 1
        self.hist = ImageRoot

    def parse_memory(self, root):
        edAddPy = root.getValueAtNVS(['origin', 'editor', 'address']).child.toPySexp()
        edCurPy = root.getValueAtNVS(['origin', 'editor', 'cursor']).child.toPySexp()
        edZipped = root.getValueAtNVS(['origin', 'editor', 'zipped']).child.toPySexp()

        listEd = Editors.TreeEditor(root, edAddPy, edCurPy)

        for i in edZipped:
            listEd.zippedNodes[i] = True

        return TNode.TNode(listEd)

    def writeImage(self):

        pyObj = self.ImageRoot.child.toPySexp()
        text = reader.to_string(pyObj)
        f = open("image", 'w')
        f.write(text)
        f.close()

    def testNewWrite(self):

        pyObj = self.ImageRoot.child.toNodeIDValuePySexp()
        text = reader.to_string(pyObj)
        f = open("testIDImage", 'w')
        f.write(text)
        f.close()

#    def addCol(self):
#        self.cols += 1
#        newWidth = utility.screenWidth() / self.cols
#        #need to readjust all columns..
#        self.active.insertAfter(newWidth)
#        self.active = self.active.next
#
#        iter = self.winRoot
#        iter.child.width = newWidth
#        while iter.next:
#            iter.next.child.width = newWidth
#            iter = iter.next

    def addWindow(self, newFunc):
        self.wins += 1
        newWinTree = self.winTree.appendAtCursor(newFunc).curNext()
        return newWinTree

    def draw(self):
        maxX = utility.screenWidth()
        curY = 0
        yStep = utility.screenHeight() / self.wins

        for i in self.winTree.root.child:
            if i == self.winTree.cursor:
                i.child.draw(0, curY, maxX, curY + yStep, libtcod.azure)
            else: i.child.draw(0, curY, maxX, curY + yStep, libtcod.grey)
            curY += yStep
            if i.next:
                libtcod.console_hline(0, 0, curY - 1, utility.screenWidth())


    def handleKeys(self, key, mouse):
        #return self.active.child.function.handleKeys(key)

        if self.winCmd:

            if chr(key.c) == 'j':
                try:
                    return self.updateList(
                        ('winTree', self.winTree.curNext()),
                        ('winCmd', False))
                except ValueError: pass

            elif chr(key.c) == 'k':
                try:
                    return self.updateList(
                        ('winTree', self.winTree.curPrev()),
                        ('winCmd', False))
                except ValueError: pass

            #elif chr(key.c) == 'n':

            elif chr(key.c) == 'o':
                #abomination
                #cursorToView
                curEd = self.winTree.cursor.child
                newEd = Editors.TreeEditor(self.ImageRoot, curEd.buffer.rootToCursorAdd())
                newWinTree = self.addWindow(newEd)
                return self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False)
                )

            elif chr(key.c) == 'd':
                if self.wins > 1:
                    return self.updateList(
                        ('winTree', self.winTree.deleteAtCursor()),
                        ('wins', self.wins - 1),
                        ('winCmd', False))


            elif chr(key.c) == 'u':
                if self.hist.next:
                    return self.updateList(
                        ('ImageRoot', self.hist.next),
                        ('hist', self.hist.next)
                    )
                    #self.ImageRoot = self.hist.next
                    #self.hist = self.hist.next

            elif chr(key.c) == 'w':
                try:
                    next = self.winTree.curNext()
                except ValueError:
                    next = self.winTree.cursorToFirst()

                return self.updateList(
                    ('winTree', next),
                    ('winCmd', False))

            # run a function like a program
            elif key.vk == libtcod.KEY_SPACE:
                curEd = self.winTree.cursor.child
                evalBuffer = TNode.Buffer(self.ImageRoot, curEd.buffer.rootToCursorAdd())
                #func = CodeEditor.eval(evalBuffer)
                prog = CodeEditor.evalIOHandler(evalBuffer)
                newWinTree = self.addWindow(prog)

                newWM = self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

                return newWM

            elif key.vk == libtcod.KEY_ENTER:
                curEd = self.winTree.cursor.child
                newEd = CodeEditor.CodeEditor(self.ImageRoot, curEd.buffer.rootToCursorAdd())

                newEd.evalBuffer()
                newWinTree = self.addWindow(newEd)

                return self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

            elif chr(key.c) == 'e':
                pass

            elif chr(key.c) == '>':
                curEd = self.winTree.cursor.child
                curNode = curEd.buffer.cursor

                if curNode.isSubNode():
                    args = []
                    if curNode.child.next:
                        for i in curNode.child.next:
                            #args.append(i.getValue(curEd.id))
                            args.append(curEd.nodeValues[i])


                    #(newTree, env) = curNode.child.getValue(curEd.id)('inspect', *args)
                    (newTree, env) = curEd.nodeValues[curNode.child]('inspect', *args)
                    newEd = CodeEditor.CodeEditor(newTree.root, newTree.rootToCursorAdd())
                    newEd.context = curEd.buffer
                    newEd.contextParent = curEd.id    # not really needed?
                    newEd.showValues = True
                    newEd.env = env
                    newEd.evalBuffer()

                    newWinTree = self.addWindow(newEd)
                    return self.updateList(
                        ('winTree', newWinTree),
                        ('winCmd', False))

            elif key.vk == libtcod.KEY_ESCAPE:
                return self.update('winCmd', False)

        elif chr(key.c) == 'w' and key.lctrl:
            self.winCmd = True
            print "windowing"

        elif chr(key.c) == 's' and key.lctrl:
            #self.writeImage()
            self.testNewWrite()
            print "saving"


        else:
            result = self.winTree.cursor.child.handleKeys(key, mouse)
            #print "result ", result
            if result == 'ESC':
                #self.writeImage()
                self.testNewWrite()
                return False

            if result == 'UNDO':
                if self.hist.next:
                    self.ImageRoot = self.hist.next
                    self.hist = self.hist.next

            else:
                self.winTree = self.winTree.replaceAtCursor(result)

                if isinstance(result, Editors.TreeEditor) and result.syncWithRoot and \
                                                        self.ImageRoot != result.buffer.root:
                    self.ImageRoot = result.buffer.root
                    if result.updateUndo:
                        self.hist = cons(self.ImageRoot.child, self.hist)
                    #print "hist", self.hist.child.toPySexp()

            # need to sync all Editors to the newTree
            for i in self.winTree.root.child:
                if isinstance(i.child, Editors.TreeEditor) and i.child.syncWithRoot:
                    i.child = i.child.syncWithImage(self.ImageRoot)
            #functional: map(self.winTree.root.child .syncWithImage)

            return self
            #return self.update('winTree', self.winTree.replaceAtCursor(result))

        return self
        #return self.update('winCmd', False)


