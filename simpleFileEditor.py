import os
import iop, colourScheme
import tn,buffer, Editors

class FileObj(object):
    def __init__(self, path):
        self.fullpath = os.path.abspath(path)

    @property
    def basename(self):
        return os.path.basename(self.fullpath)

    @property
    def dirname(self):
        return os.path.dirname(self.fullpath)

    @property
    def isdir(self):
        return os.path.isdir(self.fullpath)

    def __repr__(self):
        return '<FileObj ' + str(self.basename) + '>'

    def __str__(self):
        return str(self.basename)

def dirToFileList(path):
    return [FileObj(f) for f in os.listdir(path)]

def isDirectory(node):
    fileRef = node.child
    return hasattr(fileRef, 'isdir') and fileRef.isdir


class FileEditorColourScheme(colourScheme.ColourScheme):
    def __init__(self, *args, **kwargs):
        super(FileEditorColourScheme, self).__init__(*args, **kwargs)
        self.dirCol = iop.light_green

    def lookupTokenFGColour(self, token):
        if isDirectory(token.nodeReference):
            return self.dirCol
        else:
            return self.identifierCol

class SimpleFileEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(SimpleFileEditor, self).__init__(*args, **kwargs)
        self.printingMode = 'allVertical'
        self.indentWidth = 2
        self.directory = None
        self.colourScheme = FileEditorColourScheme(bgCol=iop.black, symbolCol=iop.grey,
            identifierCol=iop.white, stringCol=iop.light_green,
            numberCol=iop.light_purple, activeHiCol=iop.azure, idleHiCol=iop.light_grey)

    @classmethod
    def fromPath(cls, path='./'):
        fileList = dirToFileList(path)
        fileRoot = tn.createTNodeExpFromPyExp([fileList])
        fileBuffer = buffer.BufferSexp(fileRoot)
        return cls(fileBuffer)

    def handleKeysMain(self, key):
        if key.code == iop.KEY_ENTER:
            cursor =  self.buffer.cursor
            if isDirectory(cursor):
                return SimpleFileEditor.fromPath(cursor.child.fullpath)
            else:
                return self

        elif key.code == iop.KEY_BACKSPACE:
            firstChild = self.buffer.first().child
            return SimpleFileEditor.fromPath(firstChild.dirname)

        else:
            return super(SimpleFileEditor, self).handleKeysMain(key)


    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False