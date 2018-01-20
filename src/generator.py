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
    A simple superclass object for getting and setting RegularGrammars and/or
    ContextFreeGrammars so subclasses which override the output method may
    generate a scanner and/or parser for the specified language of interest.
    """

    _scanner = None
    _parser = None

    def __init__(self):
        pass

    def set_scanner(self, _scanner):
        """
        Set the scanner to be used for code generation.

        Runtime: O(1) - constant
        Type: None | RegularGrammar -> None | ValueError
        """
        if _scanner is not None and\
           type(_scanner) is not scanner.RegularGrammar:
            raise ValueError('Invalid Input: scanner not a RegularGrammar')

        self._scanner = _scanner

    def get_scanner(self):
        """
        Get the scanner [to be] used for code generation.

        Runtime: O(1) - constant
        Type: None | RegularGrammar
        """
        return self._scanner

    def set_parser(self, _parser):
        """
        Set the parser to be used for code generation.

        Runtime: O(1) - constant
        Type: None | ContextFreeGrammar -> None | ValueError
        """
        if _parser is not None and\
           type(_parser) is not parser.ContextFreeGrammar:
            raise ValueError('Invalid Input: parser not a ContextFreeGrammar')

        self._parser = _parser

    def get_parser(self):
        """
        Get the parser [to be] used for code generation.

        Runtime: O(1) - constant
        Type: None | ContextFreeGrammar
        """
        return self._parser

    def output(self, filename):
        """
        Override this method in subclasses to write the necessary files for the
        specific language to be generated.

        Runtime: O(?) - ?
        Type: string -> None | ValueError
        """
        pass
