import iop
import funobj as fo

class CmdList(fo.FuncObject):
    def __init__(self, pairs):
        self.dict = dict(pairs)

