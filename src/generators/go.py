"""
A scanner/parser generator targeting go.
Generates a single golang (.go) file.
"""
from . import Generator


class Go(Generator):
    """
    A simple object for compiling scanner's and/or parser's to golang programs.
    """

    def _translate(self, filename):
        """
        Attempt to generate the golang (.go) source file with the corresponding
        scanner and/or parser currently set in the object.
        """
        return {
            filename+'.go': super(Go, self)._translate(filename)
        }
