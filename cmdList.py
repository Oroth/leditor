import iop
import funobj as fo

class CmdList(fo.FuncObject):
    def __init__(self, pairs):
        self.dict = dict(pairs)

    def match(self, key):
        return self.dict[key]

    def process(self, key, caller):
        if key.code() == 0:
            return caller

        print 'key received: ', key._key()
        if key in self.dict:
            cmdName = self.dict[key]
            print 'cmd found: ', cmdName

            if hasattr(caller, cmdName):
                cmd = getattr(caller, cmdName)
                return cmd()
        else:
            print 'no match in: ', self.dict

        return False


