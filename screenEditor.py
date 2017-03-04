import funobj as fo
import screen
import Editors
import iop

class ScreenEditor(fo.FuncObject):

    def __init__(self, maxx, maxy):
        self.image = screen.createBlank(maxx, maxy)
        self.text = 'x'
        self.statusBar = Editors.StatusBar()
        self.x = 0; self.y = 0
        self.maxx = maxx; self.maxy = maxy

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def draw(self, maxx, maxy, isActive):
        screen.setCellColour(self.image, self.x, self.y, iop.light_sky, iop.white)

        return self.image



    def handleKeys(self, key, mouse):
        screen.setCellColour(self.image, self.x, self.y, iop.black, iop.white)

        if mouse.lbuttonPressed():
            self.x = mouse.x()
            self.y = mouse.y()
            #cell = self.image[mouse.y()][mouse.x()]

        if key.code() == iop.KEY_RIGHT and self.x < self.maxx:
            self.x += 1

        elif key.code() == iop.KEY_LEFT and self.x > 0:
            self.x -= 1

        elif key.code() == iop.KEY_DOWN and self.y < self.maxy:
            self.y += 1

        elif key.code() == iop.KEY_UP and self.y > 0:
            self.y -= 1

        elif key.code() == iop.KEY_DELETE:
            screen.putNodeOnImage(self.image, self.x, self.y, ' ', None, iop.black, iop.white)

        elif key.code() == iop.KEY_BACKSPACE and self.x != 0:
            self.x -= 1
            screen.putNodeOnImage(self.image, self.x, self.y, ' ', None, iop.black, iop.white)

        elif key.isPrintable():
            screen.putNodeOnImage(self.image, self.x, self.y, key.char(), None, iop.black, iop.white)
            if self.x != self.maxx:
                self.x += 1

        return self