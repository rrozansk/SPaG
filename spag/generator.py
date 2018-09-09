"""
The Generator is a simple superclass to control the getting/setting of the
parser and/or scanner used for code generation. Each targeted language for
generation should be implemented as a subclass which only needs to override
the output method.
"""
#from os import listdir
#from os.path import dirname, realpath, join
from spag.parser import ContextFreeGrammar
from spag.scanner import RegularGrammar


SUPPORTED = ['c', 'go', 'python']
# FIXME/TODO dynamically find and populate SUPPORTED
#for _file in listdir(join(dirname(realpath(__file__)), 'generators')):
#    if _file.endswith('.py') and _file != '__init__.py':
#        SUPPORTED.append(_file.rsplit('.py', 1)[0])


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

        Output Type: Generator | TypeError
        """
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise TypeError('scanner not a RegularGrammar')

        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise TypeError('parser not a ContextFreeGrammar')

        self.scanner = scanner
        self.parser = parser

    def set_scanner(self, scanner):
        """
        Set the scanner to be used for code generation, if any.

        Runtime: O(1) - constant.

        Input Type:
          scanner: None | RegularGrammar

        Output Type: None | TypeError
        """
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise TypeError('scanner not a RegularGrammar or None')

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

        Output Type: None | TypeError
        """
        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise TypeError('parser not a ContextFreeGrammar or None')

        self.parser = parser

    def get_parser(self):
        """
        Query for the parser to be used for code generation, if any.

        Runtime: O(1) - constant.

        Output Type: None | ContextFreeGrammar
        """
        return self.parser

    def _translate(self, filename):
        """
        Override this method in subclasses which should translate the internal
        representation of the given scanner and/or parser to the targeted
        language. It should return the files and there content in a dictionary
        allowing multiple files to be returned for a given language. This is the
        only required function a child generators must implement.

        Input Type:
          filename: String

        Output Type: Dict[String, String] |
                     NotImplementedError
        """
        raise NotImplementedError('Base Generator incapable of translation')

    def output(self, filename):
        """
        Output the given scanner and or parser in the given language.

        Input Type:
          filename: String

        Output Type: Dict[String, String] |
                     TypeError |
                     ValueError |
                     NotImplementedError
        """
        if not isinstance(filename, str):
            raise TypeError('filename not a string')

        if not filename:
            raise ValueError('filename must be non empty')

        if not self.scanner and not self.parser:
            raise ValueError('Scanner and/or parser must be provided for generation')

        files = self._translate(filename)

        if not isinstance(files, dict):
            raise TypeError('generated files must be of type dict')

        if not files:
            raise ValueError('generated files must be of non empty')

        for name, content in files.items():
            if not isinstance(name, str):
                raise TypeError('generated file name must be of type string')

            if not name:
                raise ValueError('generated file name must be non empty')

            if not isinstance(content, str):
                raise TypeError('generated file content must be of type string')

            if not content:
                raise ValueError('generated file content must be non empty')

        return files
