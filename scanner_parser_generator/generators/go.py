"""
A scanner/parser generator targeting go.
Generates a single golang (.go) file.
"""
from . import Generator


class Go(Generator):
    """
    A simple object for compiling scanner's and/or parser's to golang.
    """

    def _output(self, filename):
        super(Go, self).output(filename)

    def output(self, filename):
        """
        Attempt to generate and write the golang (.go) source file with the
        corresponding scanner and/or parser currently set in the object.
        """
        if not isinstance(filename, str):
            raise ValueError('Invalid Input [Go Gen]: filename must be a string')

        if not filename:
            raise ValueError('Invalid Input [Go Gen]: filename must be a non empty string')

        with open(filename+".go", 'w') as _file:
            _file.write(self._output(filename))
