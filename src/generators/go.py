"""
A scanner/parser generator targeting go.
Generates a single golang (.go) file.
"""
from . import Generator


class Go(Generator):
    """
    A simple object for compiling scanner's and/or parser's to golang programs.
    """

    def _output(self, filename):
        super(Go, self).output(filename)

    def output(self, filename):
        """
        Attempt to generate the golang (.go) source file with the corresponding
        scanner and/or parser currently set in the object.

        Input Type:
          filename: String

        Output Type: List[Tuple[String, String]] | ValueError
        """
        if not isinstance(filename, str):
            raise ValueError('Invalid Input [Go Gen]: filename must be a string')

        if not filename:
            raise ValueError('Invalid Input [Go Gen]: filename must be a non empty string')

        return [(filename+'.go', self._output(filename))]
