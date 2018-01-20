"""
A scanner/parser generator targeting python.
Generates a single python (.py) file.
"""
import datetime
from .. import generator as generator


class Python(generator.Generator):
    """
    A simple object for compiling scanner's and/or parser's to python.
    """

    def _output(self, filename):
        pass

    def output(self, filename):
        """
        Attempt to generate and write the python (.py) source file with the
        corresponding scanner and/or parser currently set in the object.
        """
        if type(filename) != str:
            raise ValueError('Invalid Input: filename must be a string')

        if filename == "":
            raise ValueError('Invalid Input: filename must be non empty')

        with open(filename+".py", 'w') as _file:
            _file.write(self._output(filename))
