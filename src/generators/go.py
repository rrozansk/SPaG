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
            raise TypeError('[Go Gen]: filename must be a string')

        if not filename:
            raise TypeError('[Go Gen]: filename must be a non empty string')

        if self.scanner is None and self.parser is None:
            raise ValueError('Must provide atleast a scanner or a parser for generation')

        return [(filename+'.go', self._output(filename))]
