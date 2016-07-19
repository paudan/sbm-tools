class MissingParameterException(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class NotConnectedException(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class BookmarkingException(Exception):

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

