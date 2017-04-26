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
    def __init__(self, cx, cy, button=0, mouseScroll=0):
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
        relx = self.cx - newX1
        rely = self.cy - newY1
        return Mouse(relx, rely, self.button, self.mouseScroll)

    # positions on console
    @property
    def x(self):
        return self.cx

    @property
    def y(self):
        return self.cy

class BackgroundGroup(pyglet.graphics.OrderedGroup):
    def __int__(self):
        super(BackgroundGroup, self).__init__(0)

class ForegroundGroup(pyglet.graphics.OrderedGroup):
    def __init__(self, fontTex):
        self.fontTexture = fontTex
        super(ForegroundGroup, self).__init__(1)

    def set_state(self):
        gl.glEnable(self.fontTexture.target)
        gl.glBindTexture(self.fontTexture.target, self.fontTexture.id)

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(self.fontTexture.target)


class Application(pyglet.window.Window):
    def __init__(self, screenCols, screenRows, resizable=True):
        self.fontImageFileName = 'fonts/terminal-transparent.png'
        self.fontImage = pyglet.image.load(self.fontImageFileName)
        self.fontImageRows = 16
        self.fontImageCols = 16

        self.fontTexture = self.fontImage.get_texture()
        self.foregroundGroup = ForegroundGroup(self.fontTexture)
        self.backgroundGroup = pyglet.graphics.OrderedGroup(0)

        self.cellWidth = self.fontTexture.width / self.fontImageRows
        self.cellHeight = self.fontTexture.height / self.fontImageCols

        screenWidth = self.cellWidth * screenCols
        screenHeight = self.cellHeight * screenRows
        super(Application, self).__init__(screenWidth, screenHeight, resizable=resizable)

        self.fontImageGrid = pyglet.image.ImageGrid(self.fontImage, self.fontImageRows, self.fontImageCols)
        self.fontTextureGrid = pyglet.image.TextureGrid(self.fontImageGrid)

        self.batch = pyglet.graphics.Batch()
        self.initBackground(screenCols, screenRows, black)
        self.initForeground(screenCols, screenRows)

        self.pygletKeys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.pygletKeys)


    @property
    def screenCols(self):
        return self.width // self.cellWidth

    @property
    def screenRows(self):
        return self.height // self.cellHeight

    def initBackground(self, maxx, maxy, bgcol):
        vertCoords = []
        for y in xrange(maxy):
            for x in xrange(maxx):
                vertCoords .extend(self.getVertexCoords(x, y))

        self.background = self.batch.add(4 * maxx * maxy, gl.GL_QUADS, self.backgroundGroup,
            ('v2f', vertCoords),
            ('c3B', bgcol * 4 * maxx * maxy))

    def initForeground(self, maxx, maxy):
        vertCoords = []
        for y in xrange(maxy):
            for x in xrange(maxx):
                vertCoords.extend(self.getVertexCoords(x, y))

        self.foreground = self.batch.add(4 * maxx * maxy, gl.GL_QUADS, self.foregroundGroup,
            ('v2f', vertCoords),
            ('t3f', self.getTexCoords(' ')  * maxx * maxy),
            ('c3B', white * 4 * maxx * maxy))

    def toggleFullScreen(self):
        self.set_fullscreen(not self.fullscreen)

    def getVertexCoords(self, x, y):
        cw = self.cellWidth
        ch = self.cellHeight
        sx = x * self.cellWidth
        sy = (self.screenRows - y - 1) * ch

        return [sx, sy, sx+cw, sy, sx+cw, sy+ch, sx, sy+ch]  # GL_QUAD

    def getTexCoords(self, char):
        charIdx = ord(char)
        cy = 15 - (charIdx // self.fontImageRows)
        cx = charIdx % self.fontImageCols

        return self.fontTextureGrid[cy, cx].tex_coords

    def screenPrint(self, x, y, fmt, bgcol=defaultBG(), fgcol=defaultFG()):
        texIdx = 12 * ((y * self.screenCols) + x)
        self.foreground.tex_coords[texIdx:texIdx+12] = self.getTexCoords(fmt)

        colIdx = 12 * ((y * self.screenCols) + x)
        self.foreground.colors[colIdx:colIdx+12] = fgcol * 4
        self.background.colors[colIdx:colIdx+12] = bgcol * 4

    def handleKeyWrapper(self, handler):
        def wrapper(symbol, modifiers):
            if modifiers & key.MOD_CTRL and symbol < 256:
                k = Key(symbol, modifiers)
                return handler(k)

        return wrapper

    def handleTextWrapper(self, handler):
        def wrapper(text):
            if not (self.pygletKeys[key.LCTRL] or self.pygletKeys[key.RCTRL]):
                k = Key.c(text)
                return handler(k)

        return wrapper

    def handleMotionWrapper(self, handler):
        def wrapper(motion):
            if motion > 6: # above 6 they have ascii defns
                key = Key(motion)
                return handler(key)

        return wrapper

    def handleMouseWrapper(self, handler):
        def wrapper(x, y, button, modifiers):
            cx = x // self.cellWidth
            cy = (self.height - y) // self.cellHeight
            mouse = Mouse(cx, cy, button, modifiers)
            print 'clicked', cx, cy
            return handler(mouse)

        return wrapper

    #def on_resize(self, width, height):
    #    print 'The window was resized to %dx%d' % (width, height)

    def eventLoopSetup(self, handleKey, handleMouse, draw):
        self.on_text = self.handleTextWrapper(handleKey)
        self.on_key_press = self.handleKeyWrapper(handleKey)
        self.on_text_motion = self.handleMotionWrapper(handleKey)
        self.on_mouse_press = self.handleMouseWrapper(handleMouse)
        self.on_draw = draw
        self.clear()
        pyglet.app.run()

    def closeWindow(self):
        pyglet.app.exit()

    def screenFlush(self):
        self.batch.draw()
