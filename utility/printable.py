class Printable:
    """
    Allows a class to be printed as a string
    """

    def __repr__(self):
        return str(self.__dict__)
