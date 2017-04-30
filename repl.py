import screen
import Editors
import cmdBar
import eval
import buffer
import reader

class Repl(Editors.Editor):
    def __init__(self):
        super(Repl, self).__init__()
        self.text = []
        self.topLine = 0
        self.cmdBar = cmdBar.CmdBar()
        self.cmdBarEnv = eval.global_env


    def draw(self, maxx, maxy, isActive):
        baseImage = screen.createImageFromStringList(self.text[self.topLine:], maxx, maxy)
        cmdImage = self.cmdBar.draw(maxx, 2, isActive=True)
        screen.overlayTextOnImage(baseImage, 0, len(self.text), '> ')
        screen.overlayImage(baseImage, 2, len(self.text), cmdImage)
        #screen.overlayLinesOnImage(baseImage, len(self.text), cmdImage)
        return baseImage

    def handleKeys(self, key):
        return self.handleCmdBarInput(key)


    def evalCmdBarResult(self, cmdBuffer):
        # Maybe should get done in the actual cmdbar
        cmd = cmdBuffer.toPyExp()
        print cmd

        #if cmd and cmd[0] in ('q', 'quit'):
        #    return 'QUIT-WM'

        result = eval.eval(buffer.BufferSexp(cmdBuffer.root), self.cmdBarEnv)
        print result

        #if isinstance(result, WindowManager):
        #    return result.update('cmdBar', None)
        self.text.append('> ' + reader.to_string(cmd))
        self.text.append(reader.to_string(result))

        return self.updateList(
            ('cmdBar', cmdBar.CmdBar()))

    def handleCmdBarInput(self, key):
        cmdResult = self.cmdBar.handleKeys(key)
        if cmdResult.returnState == 'ESCAPE':
            return self

        elif cmdResult.returnState == 'PRINT':
            return self.evalCmdBarResult(cmdResult.buffer)

        else:
            return self.update('cmdBar', cmdResult)
