import Editors
import os
import reader
from os.path import isdir, join
import tn, buffer

def dirToList(path):
    f = []

    for item in os.listdir(path):
        fullname = join(path, item)
        if isdir(fullname) and not any(x in item for x in ['git', 'swp']):
            newDir = [reader.Symbol(item)]
            newDir.append(dirToList(fullname))
            f.append(newDir)
        else:
            f.append(reader.Symbol(item))

    return f

class fileTNode(tn.TNode):
    def __init__(self, *args, **kwargs):
        super(fileTNode, self).__init__(*args, **kwargs)
        #path

class file(object):
    def __init__(self):
        self.path = ''
        self.name = ''
        self.type = ''
        self.size = 0
        self.dateModified = None

class FileEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(FileEditor, self).__init__(*args, **kwargs)
        self.printingMode = 'allVertical'
        self.indentWidth = 4
        self.directory = None

    @classmethod
    def fromPath(cls, path='./'):
        fileList = dirToList(path)
        fileRoot = tn.createTNodeExpFromPyExp([fileList])
        fileBuffer = buffer.BufferSexp(fileRoot)
        return cls(fileBuffer)

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False