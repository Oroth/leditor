__author__ = 'chephren'
import TNode
import utility
import Editors
import libtcodpy as libtcod
import evalNode

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


class WindowManager(object):
    def __init__(self, initialFunc):
        #self.root = TNode.TNode(Column(utility.screenWidth(), initialFunc))
        self.root = TNode.TNode(initialFunc)
        self.active = self.root
        self.winCmd = False
        self.cols = 1
        self.wins = 1

    def addCol(self):
        self.cols += 1
        newWidth = utility.screenWidth() / self.cols
        #need to readjust all columns..
        self.active.insertAfter(newWidth)
        self.active = self.active.next

        iter = self.root
        iter.child.width = newWidth
        while iter.next:
            iter.next.child.width = newWidth
            iter = iter.next

    def addWindow(self, newFunc):
        self.wins += 1
        self.active.insertAfter(newFunc)

    def draw(self):
        maxX = utility.screenWidth()
        curY = 0
        yStep = utility.screenHeight() / self.wins

        for i in self.root:
            if i == self.active:
                i.child.draw(0, curY, maxX, curY + yStep, libtcod.azure)
            else: i.child.draw(0, curY, maxX, curY + yStep, libtcod.grey)
            curY += yStep
            if i.next:
                libtcod.console_hline(0, 0, curY - 1, utility.screenWidth())


    def handleKeys(self, key):
        #return self.active.child.function.handleKeys(key)

        if self.winCmd:

            if chr(key.c) == 'j':
                if self.active.next:
                    self.active = self.active.next
                    self.winCmd = False

            elif chr(key.c) == 'k':
                if self.active.previous:
                    self.active = self.active.previous
                    self.winCmd = False

            elif chr(key.c) == 'o':
                newEd = Editors.TreeEditor(self.active.child.root, self.active.child.active)
                self.addWindow(newEd)
                self.active = self.active.next
                self.winCmd = False

            elif chr(key.c) == 'd':
                if self.wins > 1:
                    self.wins -= 1
                    oldAdd = self.active.getAddress()
                    self.active.removeSelf()
                    self.active = self.root.gotoNearestAddress(oldAdd)
                    self.winCmd = False

            elif chr(key.c) == 'w':
                if self.active.next:
                    self.active = self.active.next
                else:
                    self.active = self.root
                self.winCmd = False

            elif key.vk == libtcod.KEY_ENTER:
                newTree = TNode.copyTNodeAsNewTreeClass(self.active.child.active, evalNode.EvalNode)
                newEd = Editors.TreeEditor(newTree)
                newEd.showValues = True
                newEd.env = evalNode.global_env
                newEd.root.calcValue(newEd.id)
                self.addWindow(newEd)
                self.active = self.active.next
                self.winCmd = False

            elif chr(key.c) == '>':
                #newTree = TNode.copyTNodeAsNewTreeClass(self.active.child.active, evalNode.EvalNode)
                activeEd = self.active.child
                activeNode = self.active.child.active

                if activeNode.isSubNode():
                    args = []
                    if activeNode.child.next:
                        for i in activeNode.child.next:
                            args.append(i.getValue(self.active.child.id))


                    (newTree, env) = activeNode.child.getValue(activeEd.id)('inspect', *args)
                    newEd = Editors.TreeEditor(newTree)
                    newEd.showValues = True
                    newEd.env = env
                    #newEd.root.calcValue()
                    newEd.root.eval(newEd.id, env)
                    self.addWindow(newEd)
                    self.active = self.active.next
                self.winCmd = False

        elif chr(key.c) == 'w': #and key.lctrl:
            self.winCmd = True
            print "windowing"

        else:
            return self.active.child.handleKeys(key)


    #def mainLoop(self):

