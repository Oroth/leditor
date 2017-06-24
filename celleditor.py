import funobj as fo
import iop
import reader


class CellEditor(fo.FuncObject):
    def __init__(self, content, index=0):
        self.original = str(content)
        self.content = list(str(content).encode('string_escape'))
        self.returnCode = None
        if index < 0:
            self.index = len(self.content) + index + 1
        else:
            self.index = index

        if type(content) is str:
            self.isString = True
        else: self.isString = False

    def getContentAsString(self):
        text = ''.join(self.content)
        if self.isString:
            text = '"' + text + '"'
        return text

    def getContent(self):
        return reader.atom(self.getContentAsString())

    def handleClick(self, characterRef):
        if self.isString:
            self.index = characterRef - 1
        else:
            self.index = characterRef

    def handleKey(self, key):
        self.returnCode = 'CONTINUE'
        if key.code == iop.KEY_ENTER:
            return acceptInput(self)

        if key.code == iop.KEY_ESCAPE:
            return self.update('returnCode', 'CANCEL' )

        elif key.code == iop.KEY_LEFT:
            return cursorLeft(self)

        elif key.code == iop.KEY_RIGHT:
            return cursorRight(self)

        elif key.code == iop.KEY_BACKSPACE:
            return deleteBack(self)

        elif key.code == iop.KEY_DELETE:
            return deleteForward(self)

        elif key.char == '"':
            return toggleString(self)

        elif not self.isString and key.char  == "'":
            return self.update('returnCode', 'QUOTE')

        elif not self.isString and key.char == ".":
            return self.update('returnCode', 'DOT')

        elif not self.isString and key.char == '(':
            return self.update('returnCode', 'NEST')

        elif not self.isString and key.char == ')':
            return self.update('returnCode', 'UNNEST')

        elif not self.isString and key.code == iop.KEY_SPACE:
            return returnSpace(self)

        elif key.isPrintable() and (self.isString or key.char not in ':;\\|,#~[]{}%&*'):
            return inputCharacter(self, key)

        else:
            return self


def acceptInput(cellEditor):
    try:
        if cellEditor.isString and ''.join(cellEditor.content).decode('string_escape'):
            return cellEditor.update('returnCode', 'END')
    except ValueError: return
    return cellEditor.update('returnCode', 'END')

def exitCellEditor(cellEditor):
    return cellEditor.update('returnCode', 'CANCEL' )

def cursorLeft(cellEditor):
    if cellEditor.index > 0:
        return cellEditor.update('index', cellEditor.index - 1)

def cursorRight(cellEditor):
    if cellEditor.index < len(cellEditor.content):
        return cellEditor.update('index', cellEditor.index + 1)

def deleteBack(cellEditor):
    if cellEditor.content and cellEditor.index != 0:
        newContent = list(cellEditor.content)
        del newContent[cellEditor.index - 1]
        return cellEditor.updateList(
            ('content', newContent),
            ('index', cellEditor.index - 1))
    elif not cellEditor.content:
        return cellEditor.update('returnCode', 'PREV')

def deleteForward(cellEditor):
    if cellEditor.content and cellEditor.index != len(cellEditor.content):
        newContent = list(cellEditor.content)
        del newContent[cellEditor.index]
        return cellEditor.update('content', newContent)

def returnCode(cellEditor, code):
    return cellEditor.update('returnCode', code)

def toggleString(cellEditor):
    if not cellEditor.isString:
        return cellEditor.update('isString', True)
    else:
        temp = ''.join(cellEditor.content)
        if temp.find(' ') == -1:
            return cellEditor.update('isString', False)
        else:
            return cellEditor

def returnSpace(cellEditor):
    if len(cellEditor.content) > 0:
        return cellEditor.update('returnCode', 'SPACE')

def inputCharacter(cellEditor, key):
    newContent = list(cellEditor.content)
    newContent.insert(cellEditor.index, key.char)
    return cellEditor.updateList(
        ('content', newContent),
        ('index', cellEditor.index + 1),
        ('returnCode', 'CONTINUE'))


