"""
The Generator is a simple superclass to control the getting/setting of the
parser and/or scanner used for code generation. Each targeted language for
generation should be implemented as a subclass which only needs to override
the output method.
"""
import scanner as scan
import parser as parse


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

    def set_scanner(self, scanner):
        """
        Set the scanner to be used for code generation, if any.

        Runtime: O(1) - constant.

        Input Type:
          scanner: None | RegularGrammar

        Output Type: None | ValueError
        """
        if scanner and type(scanner) is not scan.RegularGrammar:
            raise ValueError('Invalid Input: scanner not a RegularGrammar')

        self._scanner = scanner

    def get_scanner(self):
        """
        Query for the scanner to be used for code generation, if any.

        Runtime: O(1) - constant.

        Output Type: None | RegularGrammar
        """
        return self._scanner

    def set_parser(self, parser):
        """
        Set the parser to be used for code generation, if any.

        Runtime: O(1) - constant.

        Input Type:
          parser: None | ContextFreeGrammar

        Output Type: None | ValueError
        """
        if parser and type(parser) is not parse.ContextFreeGrammar:
            raise ValueError('Invalid Input: parser not a ContextFreeGrammar')

        self._parser = parser

    def get_parser(self):
        """
        Query for the parser to be used for code generation, if any.

        Runtime: O(1) - constant.

        Output Type: None | ContextFreeGrammar
        """
        return self._parser

    def output(self, filename):
        """
        Override this method in subclasses to write the necessary files for the
        specific language to be generated.

        Runtime: O(1) - constant.

        Input Type:
          filename: String

        Output Type: ValueError
        """
        raise ValueError('Error: output not implemented for Generator')
