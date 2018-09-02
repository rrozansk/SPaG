"""
A scanner/parser generator targeting python.
Generates a single python (.py) file.
"""
from . import Generator


class Python(Generator):
    """
    A simple object for compiling scanner's and/or parser's to python programs.
    """

    def _translate(self, filename):
        """
        Attempt to generate the python (.py) source file with the corresponding
        scanner and/or parser currently set in the object.
        """
        return {
            filename+'.py': super(Python, self)._translate(filename)
        }
