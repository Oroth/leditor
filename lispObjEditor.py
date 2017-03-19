import funobj as fo
import Editors
import screen
import iop

class LispObjEditor(fo.FuncObject):
    def __init__(self, obj):
        self.lispObj = obj
        #self.image = screen.createBlank(maxx, maxy)
        self.statusBar = Editors.StatusBar()


    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def draw(self, maxx, maxy, isActive):
        drawFunc = self.lispObj.call('draw')
        txt = drawFunc.call(maxx, maxy)
        image = screen.stringToImage(txt, 20, 10)
        return image

    def handleKeys(self, key, mouse):
        handleKeysFunc = self.lispObj.call('handleKeys')
        newLispObj = handleKeysFunc.call(key)

        return self.update('lispObj', newLispObj)
