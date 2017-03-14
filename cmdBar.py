import iop
from Editors import TreeEditor, CellEditor
from reader import Symbol
import tn

class CmdBar(TreeEditor):
    def __init__(self, *args, **kwargs):
        super(CmdBar, self).__init__(*args, **kwargs)
        self.returnState = 'EDIT'
        self.editing = True
        self.cellEditor = CellEditor(Symbol(''))


    def draw(self, maxx, maxy, isActive):
        return super(TreeEditor, self).draw(maxx, maxy, isActive)

    def parseCommand(self):
        return self.update('returnState', 'PRINT')

    def handleKeys(self, key, mouse):
        if key.code() == iop.KEY_ESCAPE:
            return self.update('returnState', 'ESCAPE')

        if key.code() == iop.KEY_ENTER:
            return super(CmdBar, self).handleKeys(key, mouse).parseCommand()

        return super(CmdBar, self).handleKeys(key, mouse)