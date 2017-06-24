import os
import iop, colourScheme
import tn, buffer, Editors
import cmdList
from iop import Key

class FileObj(object):
    def __init__(self, file, path):
        self.fullpath = os.path.join(path, file)

    @property
    def basename(self):
        return os.path.basename(self.fullpath)

    @property
    def dirname(self):
        return os.path.dirname(self.fullpath)

    @property
    def isdir(self):
        return os.path.isdir(self.fullpath)

    @property
    def ismusic(self):
        return self.basename.endswith(('mp3', 'flac'))

    def __repr__(self):
        return '<FileObj ' + str(self.basename) + '>'

    def __str__(self):
        return str(self.basename)

def dirToFileList(path):
    return [FileObj(file, path) for file in os.listdir(path)]

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
    def __init__(self, aBuffer=None, directory='./', store=None, trackref=None):
        super(SimpleFileEditor, self).__init__(aBuffer)
        self.printingMode = 'allVertical'
        self.indentWidth = 2
        self.colourScheme = FileEditorColourScheme()
        self.directory = directory
        self.track = None
        self.trackref = trackref
        self.store = store

        self.moveCommands = cmdList.CmdList([
            ((Key.c('l'), Key.c('j'), Key.vk(iop.KEY_RIGHT), Key.vk(iop.KEY_DOWN)),
                Editors.cmdCursorNext),
            ((Key.c('h'), Key.c('k'), Key.vk(iop.KEY_LEFT), Key.vk(iop.KEY_UP)),
                Editors.cmdCursorPrevious),
        ])

    @classmethod
    def fromPath(cls, path='./', store=None, trackref=None):
        fileList = dirToFileList(path )
        fileRoot = tn.createTNodeExpFromPyExp([fileList])
        fileBuffer = buffer.BufferSexp(fileRoot, cursorAdd=[0, 0])
        return cls(fileBuffer, path, store, trackref)

    def newPath(self, path):
        fileList = dirToFileList(path )
        fileRoot = tn.createTNodeExpFromPyExp([fileList])
        fileBuffer = buffer.BufferSexp(fileRoot, cursorAdd=[0, 0])
        newSFE = self.updateBuffer(fileBuffer)

        return newSFE.update('directory', path)

    def handleKeysMain(self, key):
        if key.code == iop.KEY_ENTER:
            return self.handleDefaultAction()

        elif key.code == iop.KEY_BACKSPACE:
            parentDir = os.path.dirname(self.directory)
            return SimpleFileEditor.fromPath(parentDir)

        else:
            return self.handleKeysMovement(key)


    def handleDefaultAction(self):
        if self.buffer.onSubNode():
            return self

        file = self.buffer.current
        if file.isdir:
            return self.newPath(file.fullpath)
        elif file.ismusic:
            return self.playMusic(file)

        else:
            return self


    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False

    def playMusic(self, file):
        newStore = self.store.set(self.trackref, file.fullpath)
        return self.update('store', newStore)
