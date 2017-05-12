import screen
import Editors
import iop

class ScreenEditor(Editors.Editor):
    def __init__(self, maxx, maxy):
        self.image = screen.createBlank(maxx, maxy)
        self.x = 0; self.y = 0
        self.maxx = maxx; self.maxy = maxy
        super(ScreenEditor, self).__init__()

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def draw(self, maxx, maxy, isActive):
        screen.setCellColour(self.image, self.x, self.y, iop.light_sky, iop.white)

        return self.image

    def handleKeys(self, key):
        screen.setCellColour(self.image, self.x, self.y, iop.black, iop.white)

        return self.handleKeysMain(key)

    def handleMouse(self, mouse):
        screen.setCellColour(self.image, self.x, self.y, iop.black, iop.white)
        if mouse.lbuttonPressed():
            return self.updateList(
                ('x', mouse.x),
                ('y', mouse.y))
        else:
            return self

    def handleKeysMain(self, key):

        if key.code() == iop.KEY_RIGHT and self.x < self.maxx:
            return self.update('x', self.x + 1)

        elif key.code() == iop.KEY_LEFT and self.x > 0:
            return self.update('x', self.x - 1)

        elif key.code() == iop.KEY_DOWN and self.y < self.maxy:
            return self.update('y', self.y + 1)

        elif key.code() == iop.KEY_UP and self.y > 0:
            return self.update('y', self.y - 1)

        elif key.code() == iop.KEY_DELETE:
            screen.putNodeOnImage(self.image, self.x, self.y, ' ', None, iop.black, iop.white)

        elif key.code() == iop.KEY_BACKSPACE and self.x != 0:
            self.x -= 1
            screen.putNodeOnImage(self.image, self.x, self.y, ' ', None, iop.black, iop.white)

        elif key.isPrintable():
            newImage = screen.fnPutNodeOnImage(self.image, self.x, self.y, key.char)
            if self.x != self.maxx:
                newx = self.x + 1
            else:
                newx = self.x


            return self.updateList(
                ('image', newImage),
                ('x', newx))


            #screen.putNodeOnImage(self.image, self.x, self.y, key.char, None, iop.black, iop.white)
            #if self.x != self.maxx:
            #    self.x += 1

        return self