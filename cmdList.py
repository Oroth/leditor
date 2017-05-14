import funobj as fo

class CmdList(fo.FuncObject):
    def __init__(self, pairs):
        self.dict = dict(pairs)

    def match(self, key):
        return self.dict[key]

    def process(self, key, caller):
        if key in self.dict:
            cmd = self.dict[key]
            return cmd(caller)

        return False


