import funobj as fo
import screen
import Editors

class Pager(fo.FuncObject):
    def __init__(self, textlist):
        self.statusBar = Editors.StatusBar()
        self.text = textlist
        self.topLine = 0

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def draw(self, maxx, maxy, isActive):
        return screen.createImageFromStringList(self.text[self.topLine:], maxx, maxy)

    def handleKeys(self, key):
        if key.char() == 'j' and self.topLine < len(self.text) - 10:
            return self.update('topLine', self.topLine + 1)

        elif key.char() == 'k' and self.topLine > 0:
            return self.update('topLine', self.topLine - 1)

        return self

    def handleMouse(self, mouse):
        return self
