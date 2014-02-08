__author__ = 'chephren'
import TNode
import utility
import libtcodpy

# interface

class Window(object):
    def __init(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = libtcodpy.console_new(width, height)

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
        curY = 0
        yStep = utility.screenHeight() / self.wins

        for i in self.root:
            i.child.draw(0, curY)
            curY += yStep
            #libtcodpy.console_print_frame(0,0, 0, utility.screenWidth(), yStep - 1)
            libtcodpy.console_hline(0, 0, yStep - 1, utility.screenWidth())

        #curx = iter.element.width
        #while iter.next:
            #iter.element.draw()
        #self.active.element.draw(0, 0)

    def handleKeys(self, key):
        #return self.active.child.function.handleKeys(key)
        #if key.vk = 'w'
        return self.active.child.handleKeys(key)


    #def mainLoop(self):

