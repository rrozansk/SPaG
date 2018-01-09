"""
The generator is a simple super class to control the getting/setting of the
parser and/or scanner used for code generation. Each targeted language for
generation should be implemented as a subclass which only needs to override
the output method.
"""
import scanner as scanner
import parser as parser


class Generator(object):
    """
    A simple object for compiling scanner's and/or parser's to other languages.
    """

    _scanner = None
    _parser = None

    def __init__(self):
        pass

    def set_scanner(self, _scanner):
        """
        Set the scanner which is to be used for code generation.
        """
        if _scanner is None:
            self._scanner = None
            return

        if type(_scanner) is not scanner.RegularGrammar:
            raise ValueError('Invalid Input: scanner not a RegularGrammar')

        self._scanner = _scanner.make()

    def get_scanner(self):
        """
        Get the scanner which is to be used for code generation.
        """
        return self._scanner

    def set_parser(self, _parser):
        """
        Set the parser which is to be used for code generation.
        """
        if _parser is None:
            self._parser = None
            return

        if type(_parser) is not parser.ContextFreeGrammar:
            raise ValueError('Invalid Input: parser not a ContextFreeGrammar')

        self._parser = _parser.make()

    def get_parser(self):
        """
        Get the parser which is to be used for code generation.
        """
        return self._parser

    def output(self, filename):
        """
        Override this method in subclass for specific language generation.
        """
        pass
