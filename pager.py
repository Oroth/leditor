import funobj as fo
import screen
import Editors
import iop

class Pager(fo.FuncObject):
    def __init__(self, textlist):
        #self.image = screen.createBlank(maxx, maxy)
        self.statusBar = Editors.StatusBar()
        #self.maxx = maxx; self.maxy = maxy
        self.text = textlist

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def draw(self, maxx, maxy, isActive):
        #return screen.stringToImage(self.text, maxx, maxy)
        return screen.createImageFromStringList(self.text, maxx, maxy)



    def handleKeys(self, key, mouse):
        return self

