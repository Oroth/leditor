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


class Colour(tuple):
    def __new__(cls, r, g, b):
        return (r, g, b)

class Key():
    def __init__(self, symbol, modifier=0):
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

    def __repr__(self):
        return 'key(%s)' % self.symbol

    def _key(self):
        return (self.symbol, self.ctrl(), self.alt(), self.shift())

    def code(self):
        if self.symbol in (KEY_SPACE, KEY_ENTER):
            return self.symbol

        if self.symbol < 256 and chr(self.symbol) in printable:
            return KEY_CHAR
        return self.symbol

    @property
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

    def wheelScrolled(self):
        return self.mouseScroll != 0

    def wheelUp(self):
        return self.mouseScroll > 0

    def wheelDown(self):
        return self.mouseScroll < 0

    def on(self):
        return self.button or self.mouseScroll

    def position(self):
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


class IOApplication(pyglet.window.Window):
    def __init__(self, screenCols, screenRows, bgcol, fgcol, resizable=True):
        self.fontImageFileName = 'fonts/terminal-transparent.png'
        self.fontImage = pyglet.image.load(self.fontImageFileName)
        self.fontImageRows = 16
        self.fontImageCols = 16

        self._fontTexture = self.fontImage.get_texture()
        self._foregroundGroup = ForegroundGroup(self._fontTexture)
        self._backgroundGroup = pyglet.graphics.OrderedGroup(0)

        self.cellWidth = self._fontTexture.width / self.fontImageRows
        self.cellHeight = self._fontTexture.height / self.fontImageCols

        screenWidth = self.cellWidth * screenCols
        screenHeight = self.cellHeight * screenRows
        super(IOApplication, self).__init__(screenWidth, screenHeight, resizable=resizable)

        self._fontImageGrid = pyglet.image.ImageGrid(self.fontImage, self.fontImageRows, self.fontImageCols)
        self._fontTextureGrid = pyglet.image.TextureGrid(self._fontImageGrid)

        self._batch = pyglet.graphics.Batch()
        self._initBackground(screenCols, screenRows, bgcol)
        self._initForeground(screenCols, screenRows, fgcol)

        self._pygletKeys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self._pygletKeys)

    def _initBackground(self, maxx, maxy, bgcol):
        vertCoords = []
        for y in xrange(maxy):
            for x in xrange(maxx):
                vertCoords.extend(self._getVertexCoords(x, y))

        self.background = self._batch.add(4 * maxx * maxy, gl.GL_QUADS, self._backgroundGroup,
                                          ('v2f', vertCoords),
                                          ('c3B', bgcol * 4 * maxx * maxy))

    def _initForeground(self, maxx, maxy, fgcol):
        vertCoords = []
        for y in xrange(maxy):
            for x in xrange(maxx):
                vertCoords.extend(self._getVertexCoords(x, y))

        self.foreground = self._batch.add(4 * maxx * maxy, gl.GL_QUADS, self._foregroundGroup,
                                          ('v2f', vertCoords),
                                          ('t3f', self._getTexCoords(' ') * maxx * maxy),
                                          ('c3B', fgcol * 4 * maxx * maxy))

    def _getVertexCoords(self, x, y):
        cw = self.cellWidth
        ch = self.cellHeight
        sx = x * self.cellWidth
        sy = (self.screenRows - y - 1) * ch

        return [sx, sy, sx+cw, sy, sx+cw, sy+ch, sx, sy+ch]  # GL_QUAD

    def _getTexCoords(self, char):
        charIdx = ord(char)
        cy = 15 - (charIdx // self.fontImageRows)
        cx = charIdx % self.fontImageCols

        return self._fontTextureGrid[cy, cx].tex_coords


    @property
    def screenCols(self):
        return self.width // self.cellWidth

    @property
    def screenRows(self):
        return self.height // self.cellHeight

    def toggleFullScreen(self):
        self.set_fullscreen(not self.fullscreen)

    def screenPrint(self, x, y, cell):
        texIdx = 12 * ((y * self.screenCols) + x)
        self.foreground.tex_coords[texIdx:texIdx+12] = self._getTexCoords(cell.character)

        colIdx = texIdx
        self.foreground.colors[colIdx:colIdx+12] = cell.fgColour * 4
        self.background.colors[colIdx:colIdx+12] = cell.bgColour * 4


    def handleKeyWrapper(self, handler):
        def wrapper(symbol, modifiers):
            if modifiers & key.MOD_CTRL and symbol < 256:
                k = Key(symbol, modifiers)
                return handler(k)
            elif symbol > 255:
                return handler(Key(symbol, modifiers))

        return wrapper

    def handleTextWrapper(self, handler):
        def wrapper(text):
            if not any([self._pygletKeys[c] for c in (key.LCTRL, key.RCTRL, key.ENTER, key.BACKSPACE)]):
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

    def handleMouseScrollWrapper(self, handler):
        def wrapper(x, y, scroll_x, scroll_y):
            mouse = Mouse(0, 0, mouseScroll=scroll_y)
            return handler(mouse)

        return wrapper

    #def on_resize(self, width, height):
    #    print 'The window was resized to %dx%d' % (width, height)

    def eventLoopSetup(self, handleKey, handleMouse, draw):
        self.on_text = self.handleTextWrapper(handleKey)
        self.on_key_press = self.handleKeyWrapper(handleKey)
        self.on_text_motion = self.handleMotionWrapper(handleKey)
        self.on_mouse_press = self.handleMouseWrapper(handleMouse)
        self.on_mouse_scroll = self.handleMouseScrollWrapper(handleMouse)
        self.on_draw = draw
        self.clear()

        pyglet.app.run()

    def closeWindow(self):
        pyglet.app.exit()

    def screenFlush(self):
        self._batch.draw()

