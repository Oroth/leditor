import Editors
import os
import reader
from os.path import isdir, join

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


class FileEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(FileEditor, self).__init__(*args, **kwargs)
        self.printingMode = 'allVertical'
        self.indentWidth = 4
        self.directory = None

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False