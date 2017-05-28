import funobj as fo
import iop
import reader


class ColourScheme(fo.FuncObject):
    def __init__(self,
                 bgCol=iop.black, symbolCol=iop.grey,
                 identifierCol=iop.white,
                 stringCol=iop.light_green, numberCol=iop.light_purple,
                 activeHiCol=iop.azure, idleHiCol=iop.light_grey,
                 operatorCol=iop.dark_red, keyWordCol=iop.light_sky):
        self.bgCol = bgCol
        self.symbolCol = symbolCol
        self.identifierCol = identifierCol
        self.stringCol = stringCol
        self.numberCol = numberCol
        self.activeHiCol = activeHiCol
        self.idleHiCol = idleHiCol
        self.operatorCol = operatorCol
        self.keyWordCol = keyWordCol

    def lookupTokenFGColour(self, token):
        if isinstance(token.nodeReference.child, reader.Symbol):
            if token.nodeToString() in ("'", '.', '(', ')', '#'):
                fgcol = self.symbolCol
            elif token.nodeToString() in ('=', '+', '-', '*', '/', '>', '>=', '<', '=<', '!='):
                fgcol = self.operatorCol
            elif token.nodeToString() in ('obj', '^', 'let', 'if'):
                fgcol = self.keyWordCol
            else:
                fgcol = self.identifierCol
        elif isinstance(token.nodeReference.child, str) and token.printRule != 'cellEditorNonString':
           fgcol = self.stringCol
        elif isinstance(token.nodeReference.child, int) or isinstance(token.nodeReference.child, float):
           fgcol = self.numberCol
        else:
           fgcol = self.symbolCol

        return fgcol