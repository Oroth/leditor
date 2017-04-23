import pyglet
from pyglet import gl
import pyglet.sprite

from pyglet.window import key
import pyglet.window.mouse
from string import printable

KEY_ENTER = key.ENTER
KEY_ESCAPE = key.ESCAPE
KEY_BACKSPACE = key.BACKSPACE
KEY_DELETE = key.DELETE
KEY_SPACE = key.SPACE
KEY_TAB = key.TAB
KEY_ALT = key.LALT
KEY_F1 = key.F1
KEY_F2 = key.F2
KEY_F5 = key.F5
KEY_F8 = key.F8
KEY_F9 = key.F9
KEY_F10 = key.F10
KEY_F11 = key.F11
KEY_F12 = key.F12
KEY_LEFT = key.LEFT
KEY_RIGHT = key.RIGHT
KEY_UP = key.UP
KEY_DOWN = key.DOWN
KEY_CHAR = 65

ShiftMap = {
    key.GRAVE : key.QUOTELEFT,
    key._1 : key.EXCLAMATION,
    key._2 : key.DOUBLEQUOTE,
    key._3 : key.POUND,
    key._4 : key.DOLLAR,
    key._5 : key.PERCENT,
    key._6 : key.ASCIICIRCUM,
    key._7 : key.AMPERSAND,
    key._8 : key.ASTERISK,
    key._9 : key.PARENLEFT,
    key._0 : key.PARENRIGHT,
    key.UNDERSCORE : key.UNDERSCORE,
    key.EQUAL : key.PLUS,
    key.BRACKETLEFT : key.BRACELEFT,
    key.BRACKETRIGHT : key.BRACERIGHT,
    key.SEMICOLON : key.COLON,
    key.APOSTROPHE : key.AT,
    key.HASH : key.ASCIITILDE,
    key.BACKSLASH : key.BAR,
    key.COMMA : key.LESS,
    key.PERIOD : key.GREATER,
    key.SLASH : key.QUESTION
}

light_grey = (159,159,159)
light_green= (114,255,114)
white = (255, 255, 255)
black = (0, 0, 0)

light_sky = (114,219,255)
light_purple = (219,114,255)
azure = (0,127,255)
grey = (127,127,127)
dark_green = (0,191,0)
dark_red = (191,0,0)
darker_green = (0,127,0)
darker_sky = (0,95,127)


def defaultBG():
    return black

def defaultFG():
    return white


class Key():
    def __init__(self, symbol, modifier=0):
        if modifier & key.MOD_SHIFT and symbol in ShiftMap:
            self.symbol = (ShiftMap[symbol])
        else:
            self.symbol = symbol

        if self.symbol < 256 and chr(self.symbol) in printable:
            c = chr(self.symbol)
            if (modifier & key.MOD_SHIFT) and c.islower():
                self.c = chr(self.symbol - 32)
            else:
                self.c = chr(self.symbol)
        else:
            self.c = chr(0)

        self.modifier = modifier

    vkCharMap = {
            KEY_ENTER: 13,
            KEY_ESCAPE: 27,
            KEY_BACKSPACE: 8,
            KEY_SPACE: 32,
            KEY_TAB: 9
        }

    shiftedKeys = '!"$%^&*()_+{}:@~|<>?'

    @classmethod
    def vk(cls, vk, ctrl=False, alt=False, shift=False):
        # newKey = libtcod.Key()
        # newKey.vk = vk
        # if vk in Key.vkCharMap:
        #     c = Key.vkCharMap[vk]
        # else:
        #     newKey.c = 0
        mctrl = key.MOD_CTRL if ctrl else 0
        malt =  key.MOD_ALT if alt else 0
        mshift = key.MOD_SHIFT if shift else 0
        modifiers = mctrl | malt | mshift

        return cls(vk, modifiers)

    @classmethod
    def c(cls, c, ctrl=False, alt=False, shift=None):
        sym = ord(c)
        if c.isupper():
            sym += 32

        if shift is not None:
            newShift = shift
        elif c.isupper() or c in Key.shiftedKeys:
            newShift = True
        else:
            newShift = False

        mctrl = key.MOD_CTRL if ctrl else 0
        malt =  key.MOD_ALT if alt else 0
        mshift = key.MOD_SHIFT if newShift else 0
        modifiers = mctrl | malt | mshift

        return cls(sym, modifiers)


    def __eq__(x, y):
        return x._key() == y._key()

    def __hash__(self):
        return hash(self._key())

    def _key(self):
        return (self.symbol, self.ctrl(), self.alt(), self.shift())

    def code(self):
        if self.symbol < 256 and chr(self.symbol) in printable:
            return KEY_CHAR
        return self.symbol

    def char(self):
        return self.c

    def off(self):
        return self.symbol == 0

    def on(self):
        return self.symbol != 0

    def ctrl(self):
        return self.modifier & key.MOD_CTRL != 0

    def alt(self):
        return self.modifier & key.MOD_ALT != 0

    def shift(self):
        return self.modifier & key.MOD_SHIFT != 0

    def isPrintable(self):
        return self.symbol < 256 and chr(self.symbol) in printable


class Mouse():
    def __init__(self, x, y, cx, cy, button=0, mouseScroll=0):
        self.x = x
        self.y = y
        self.cx = cx
        self.cy = cy
        self.button = button
        self.mouseScroll = mouseScroll

    def lbuttonPressed(self):
        return self.button == pyglet.window.mouse.LEFT

    def wheelUp(self):
        return self.mouseScroll > 0

    def wheelDown(self):
        return self.mouseScroll < 0

    def on(self):
        return self.button or self.mouseScroll

    def getPos(self):
        return self.cx, self.cy

    def getMouseWithRelativePosition(self, newX1, newY1):
        relx = self.x - newX1
        rely = self.y - newY1
        return Mouse(relx, rely, self.button, self.mouseScroll)

    # positions on console
    def x(self):
        return self.cx

    def y(self):
        return self.cy



class Application(pyglet.window.Window):
    def __init__(self, screenCols, screenRows, resizable=True):

        self.texturefile = 'fonts/terminal-transparent.png'
        self.fontRows = 16
        self.fontCols = 16
        self.font_image = pyglet.image.load(self.texturefile)
        self.font_texture = self.font_image.get_texture()

        self.cellWidth = self.font_texture.width / self.fontRows
        self.cellHeight = self.font_texture.height / self.fontCols


        screenWidth = self.cellWidth * screenCols
        screenHeight = self.cellHeight * screenRows
        super(Application, self).__init__(screenWidth, screenHeight, resizable=resizable)

    @property
    def screenCols(self):
        return self.width // self.cellWidth

    @property
    def screenRows(self):
        return self.height // self.cellHeight

    def toggleFullScreen(self):
        self.set_fullscreen(not self.fullscreen)

    def getVertexCoords(self, x, y):
        cw = self.cellWidth
        ch = self.cellHeight
        sx = x * self.cellWidth
        sy = (self.screenRows - y - 1) * ch
        return [sx,sy, sx+cw,sy, sx,sy+ch, sx+cw, sy+ch]

    def getCharCoords(self, c):
        cindex = ord(c)
        cy = 15 - (cindex // self.fontRows)
        cx = cindex % self.fontCols

        # convert to [0, 1] bounded float notation
        cw = 1.0 / self.fontCols
        ch = 0.875 / self.fontRows   # don't understand why this is 0.875, rather than 1.0
        tcy = cy * ch
        tcx = cx * cw
        return [tcx,tcy, tcx+cw,tcy, tcx,tcy+ch, tcx+cw,tcy+ch]

    def setBackgroundCol(self, cellXPos, cellYPos, bgcol=black):
        vertex_list = pyglet.graphics.vertex_list(4,
            ('v2i', self.getVertexCoords(cellXPos, cellYPos)),
            ('c3B', bgcol * 4))

        vertex_list.draw(gl.GL_TRIANGLE_STRIP)


    def screenPrint(self, cellXPos, cellYPos, fmt, bgcol=defaultBG(), fgcol=white):
        if bgcol != defaultBG():
            self.setBackgroundCol(cellXPos, cellYPos, bgcol)

        vertexCoords = self.getVertexCoords(cellXPos, cellYPos)
        texCoords = self.getCharCoords(fmt)

        vlist = pyglet.graphics.vertex_list(
            4,
            ('v2f', vertexCoords),
            ('t2f', texCoords),
            ('c3B', fgcol * 4))

        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.font_texture.id)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        vlist.draw(gl.GL_TRIANGLE_STRIP)

        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_TEXTURE_2D)

    def handleKeyWrapper(self, handler):
        def wrapper(symbol, modifiers):
            print pyglet.window.key.symbol_string(symbol)
            key = Key(symbol, modifiers)
            return handler(key)

        return wrapper

    def handleMouseWrapper(self, handler):
        def wrapper(x, y, button, modifiers):
            cx = x // self.cellWidth
            cy = (self.height - y) // self.cellHeight
            mouse = Mouse(x, y, cx, cy, button, modifiers)
            return handler(mouse)

        return wrapper

    #def on_text(self, text):
    #    print text

    #def on_resize(self, width, height):
    #    print 'The window was resized to %dx%d' % (width, height)

    def eventLoopSetup(self, handleKey, handleMouse, draw):
        self.on_key_press = self.handleKeyWrapper(handleKey)
        self.on_mouse_press = self.handleMouseWrapper(handleMouse)
        self.on_draw = draw
        pyglet.app.run()

    def closeWindow(self):
        pyglet.app.exit()

    def screenFlush(self):
        gl.glFlush()
