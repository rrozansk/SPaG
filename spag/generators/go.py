"""Golang generator.

A scanner/parser generator targeting go. Generates a single golang (.go) file.
"""
from spag.generator import Generator


class Go(Generator):
    """Golang generator.

    A simple object for compiling scanner's and/or parser's to golang programs.
    """

    def _translate(self):
        """Override the superclass method to generate source code.

        Attempt to generate the golang (.go) source file with the corresponding
        scanner and/or parser currently set in the object.
        """
        return {self.filename+'.go': super(Go, self)._translate()}
