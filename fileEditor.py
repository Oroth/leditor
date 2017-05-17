import os
import reader, iop
import tn, buffer, Editors, colourScheme

def dirToList(path):
    f = []

    for item in os.listdir(path):
        fullname = os.path.join(path, item)
        if os.path.isdir(fullname) and not any(x in item for x in ['git', 'swp']):
            newDir = [reader.Symbol(item)]
            newDir.append(dirToList(fullname))
            f.append(newDir)
        else:
            f.append(reader.Symbol(item))

    return f

def dirToFileList(path):
    f = []

    for item in os.listdir(path):
        fullname = os.path.join(path, item)
        if os.path.isdir(fullname) and not any(x in item for x in ['git', 'swp']):
            newDir = [FileObj(path, item, 'dir')]
            newDir.append(dirToFileList(fullname))
            f.append(newDir)
        else:
            f.append(FileObj(path, item, 'file'))

    return f

class FNode(tn.TNode):
    def __init__(self, val=None, id=None, next=None, name=''):
        #super(FNode, self).__init__(val, id, next)
        self.name=name
        self.child = createFNodeExpFromPyExp(val)
        self.next = next
        self.nodeID = 0
        self.quoted = False

        if not id:
            self.nodeID = tn.TNode.__nodes__
            tn.TNode.__nodes__ += 1
        else:
            self.nodeID = id

    def __repr__(self):
        return '<FNode ' + str(self.child) + '>'

    def __str__(self):
        return '<FNode ' + str(self.child) + '>'

class FileObj(object):
    def __init__(self, path, name, type):
        self.path = path
        self.name = name
        self.type = type
        self.size = 0
        self.dateModified = None

    def __repr__(self):
        return '<FileObj ' + str(self.name) + '>'

    def __str__(self):
        return str(self.name)

def isFolder(val):
    if isinstance(val, tn.TNode) and val.child \
            and isinstance(val.child, FileObj) and val.child.type == 'dir':
        return True
    else:
        return False

def parseFileNode(car, cdr):
    if isFolder(car):
        val = car.next.child
        newNode = FNode(val)
        return tn.join(newNode, cdr)
    else:
        return FNode(car, next=cdr)

def createFNodeExpFromPyExp(pyexp):
    return tn.foldrtpy(parseFileNode, pyexp) if tn.isPyList(pyexp) else pyexp



def isFile(token):
    tokenRef = token.nodeReference
    if tokenRef.next and tokenRef.next.isSubNode() and not tokenRef.next.next:
        return True
    else:
        return False

class FileEditorColourScheme(colourScheme.ColourScheme):
    def __init__(self, *args, **kwargs):
        super(FileEditorColourScheme, self).__init__(*args, **kwargs)
        self.fileCol = iop.light_green

    def lookupTokenFGColour(self, token):
        if isFile(token):
            return self.fileCol
        else:
            return super(FileEditorColourScheme, self).lookupTokenFGColour(token)


class FileEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(FileEditor, self).__init__(*args, **kwargs)
        self.printingMode = 'allVertical'
        self.indentWidth = 4
        self.directory = None
        self.colourScheme = FileEditorColourScheme(bgCol=iop.black, symbolCol=iop.grey,
            identifierCol=iop.white, stringCol=iop.light_green,
            numberCol=iop.light_purple, activeHiCol=iop.azure, idleHiCol=iop.light_grey)

    @classmethod
    def fromPath(cls, path='./'):
        #fileList = dirToList(path)
        #fileRoot = tn.createTNodeExpFromPyExp([fileList])

        fileList = dirToFileList(path)
        fileRoot = createFNodeExpFromPyExp([fileList])

        fileBuffer = buffer.BufferSexp(fileRoot)
        return cls(fileBuffer)

    def syncWithImage(self, newImage):
        return self

    def isRootImageEditor(self):
        return False