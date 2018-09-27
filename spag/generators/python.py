"""Python generator.

A scanner/parser generator targeting python. Generates a single python (.py)
file.
"""
from spag.generator import Generator


class Python(Generator):
    """Python generator.

    A simple object for compiling scanner's and/or parser's to python programs.
    """

    def _translate(self):
        """Override the superclass method to generate source code.

        Attempt to generate the python (.py) source file with the corresponding
        scanner and/or parser currently set in the object.
        """
        return {self.filename+'.py': super(Python, self)._translate()}
