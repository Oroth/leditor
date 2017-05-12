import screen
import Editors

class Pager(Editors.Editor):
    def __init__(self, textlist):
        super(Pager, self).__init__()
        self.text = textlist
        self.topLine = 0

    @classmethod
    def fromFile(cls, fileName):
        f = open(fileName, 'r')
        flist = f.readlines()
        f.close()
        return cls(flist)


    def draw(self, maxx, maxy, isActive):
        return screen.createImageFromStringList(self.text[self.topLine:], maxx, maxy)

    def handleKeys(self, key):
        if key.char == 'j' and self.topLine < len(self.text) - 10:
            return self.update('topLine', self.topLine + 1)

        elif key.char == 'k' and self.topLine > 0:
            return self.update('topLine', self.topLine - 1)

        return self
