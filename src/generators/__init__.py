"""
The Generator is a simple superclass to control the getting/setting of the
parser and/or scanner used for code generation. Each targeted language for
generation should be implemented as a subclass which only needs to override
the output method.
"""
from os import listdir
from os.path import dirname, realpath
from parser.parser import ContextFreeGrammar
from scanner.scanner import RegularGrammar


__all__ = []
for _file in listdir(dirname(realpath(__file__))):
    if _file.endswith('.py') and _file != '__init__.py':
        __all__.append(_file.rsplit('.py', 1)[0])


class Generator(object):
    """
    A simple superclass object for getting and setting RegularGrammars and/or
    ContextFreeGrammars so subclasses which override the output method may
    generate a scanner and/or parser for the specified language of interest.
    """

    def __init__(self, scanner=None, parser=None):
        """
        Set the scanner and/or parser to be used for code generation, if any.

        Runtime: O(1) - constant.

        Input Type:
          scanner:      None | RegularGrammar
          parser:       None | ContextFreeGrammar

        Output Type: Generator | ValueError
        """
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise ValueError('Invalid Input: scanner not a RegularGrammar')

        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise ValueError('Invalid Input: parser not a ContextFreeGrammar')

        self.scanner = scanner
        self.parser = parser

    def set_scanner(self, scanner):
        """
        Set the scanner to be used for code generation, if any.

        Runtime: O(1) - constant.

        Input Type:
          scanner: None | RegularGrammar

        Output Type: None | ValueError
        """
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise ValueError('Invalid Input: scanner not a RegularGrammar or None')

        self.scanner = scanner

    def get_scanner(self):
        """
        Query for the scanner to be used for code generation, if any.

        Runtime: O(1) - constant.

        Output Type: None | RegularGrammar
        """
        return self.scanner

    def set_parser(self, parser):
        """
        Set the parser to be used for code generation, if any.

        Runtime: O(1) - constant.

        Input Type:
          parser: None | ContextFreeGrammar

        Output Type: None | ValueError
        """
        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise ValueError('Invalid Input: parser not a ContextFreeGrammar or None')

        self.parser = parser

    def get_parser(self):
        """
        Query for the parser to be used for code generation, if any.

        Runtime: O(1) - constant.

        Output Type: None | ContextFreeGrammar
        """
        return self.parser

    @staticmethod
    def output(filename):
        """
        Override this method in subclasses which should return the files and
        there content for the specific language to be generated.

        Runtime: O(1) - constant.

        Input Type:
          filename: String

        Output Type: List[Tuple[String, String]] | ValueError
        """
        if not isinstance(filename, str):
            raise ValueError('Invalid Input: filename not a string')

        raise ValueError('Error: output not implemented for Generator')
