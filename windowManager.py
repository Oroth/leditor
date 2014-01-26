__author__ = 'chephren'
import Dlist
import utility

# interface

class Window(object):
    def __init(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = []

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
        self.root = Dlist.TNode(Column(utility.screenWidth(), initialFunc))
        self.active = self.root
        self.cols = 1

    def addCol(self):
        self.cols += 1
        newWidth = utility.screenWidth() / self.cols
        #need to readjust all columns..
        self.active.insertAfter(newWidth)
        self.active = self.active.next

        iter = self.root
        iter.element.width = newWidth
        while iter.next:
            iter.next.element.width = newWidth
            iter = iter.next

    def draw(self):
        iter = self.root
        iter.element.draw(0, 2)
        #curx = iter.element.width
        #while iter.next:
            #iter.element.draw()
        #self.active.element.draw(0, 0)

    def handleKeys(self, key):
        return self.active.element.function.handleKeys(key)


    #def mainLoop(self):

