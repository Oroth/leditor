import libtcodpy as libtcod

KEY_ENTER = libtcod.KEY_ENTER
KEY_ESCAPE = libtcod.KEY_ESCAPE
KEY_BACKSPACE = libtcod.KEY_BACKSPACE
KEY_DELETE = libtcod.KEY_DELETE
KEY_F1 = libtcod.KEY_F1
KEY_F8 = libtcod.KEY_F8
KEY_LEFT = libtcod.KEY_LEFT
KEY_RIGHT = libtcod.KEY_RIGHT
KEY_UP = libtcod.KEY_UP
KEY_DOWN = libtcod.KEY_DOWN

class Key():
    def __init__(self, keyObj):
        self.keyObj = keyObj

    def match(self, key):
        if chr(self.keyObj.c) == key:
            return True
        elif self.keyObj.vk == key:
            return True
        else:
            return False

#def GetKey():

def isKey(keyObj, key):
    if chr(keyObj.c) == key:
        return True
    elif keyObj.vk == key:
        return True
    else:
        return False