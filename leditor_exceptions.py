
class GeneralException(Exception):
    def __init__(self, value=None, msg=None):
        self.value = " " + str(value) if value else ""
        self.message = " " + msg if self.message else ""

    def __str__(self):
        return "(" + self.__class__.__name__ + self.value + self.message + ")"

class ProgException(GeneralException):
    pass