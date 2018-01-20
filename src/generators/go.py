"""
A scanner/parser generator targeting go.
Generates a single golang (.go) file.
"""
import datetime
from .. import generator as generator


class Go(generator.Generator):
    """
    A simple object for compiling scanner's and/or parser's to golang.
    """

    def _output(self, filename):
        pass

    def output(self, filename):
        """
        Attempt to generate and write the golang (.go) source file with the
        corresponding scanner and/or parser currently set in the object.
        """
        if type(filename) != str:
            raise ValueError('Invalid Input: filename must be a string')

        if filename == "":
            raise ValueError('Invalid Input: filename must be non empty')

        with open(filename+".go", 'w') as _file:
            _file.write(self._output(filename))
