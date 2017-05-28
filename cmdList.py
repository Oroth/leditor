import funobj as fo

class CmdList(fo.FuncObject):
    def __init__(self, pairs):
        expandedPairs = []
        for input, command in pairs:
            if isinstance(input, (list, tuple)):
                keyCommandList = [(key, command) for key in input]
                expandedPairs.extend(keyCommandList)
            else:
                expandedPairs.append((input, command))

        self.dict = dict(expandedPairs)

    def match(self, key):
        return self.dict[key]

    def process(self, key, caller):
        if key in self.dict:
            cmd = self.dict[key]
            return cmd(caller)

        return False
