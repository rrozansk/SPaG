"""
A scanner/parser generator targeting python.
Generates a single python (.py) file.
"""
from . import Generator


class Python(Generator):
    """
    A simple object for compiling scanner's and/or parser's to python.
    """

    def _output(self, filename):
        super(Python, self).output(filename)

    def output(self, filename):
        """
        Attempt to generate and write the python (.py) source file with the
        corresponding scanner and/or parser currently set in the object.
        """
        if not isinstance(filename, str):
            raise ValueError('Invalid Input [Python Gen]: filename must be a string')

        if not filename:
            raise ValueError('Invalid Input [Python Gen]: filename must be a non empty string')

        with open(filename+".py", 'w') as _file:
            _file.write(self._output(filename))
