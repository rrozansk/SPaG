"""Base Generator which protects against bad input and return values.

The Generator is a simple superclass which protect subclasses from bad user
input when trying to generate output programs. Likewise, it also protects the
user from bad developer output. It does this by performing simple validations
before and after program generation is attempted. The base Generator also
controls the getting/setting of options used for code generation. Each targeted
language for generation should be implemented as a subclass which only needs to
override the '_translate(self)' method.
"""
from spag.parser import ContextFreeGrammar
from spag.scanner import RegularGrammar


class Generator(object):
    """The Base Generator which performs [in/out]put validations.

    A simple superclass object for performing validation on user input as well
    as developer output so subclasses can focus on translating the IR returned
    by the ContextFreeGrammar and RegularGrammar classes.
    """

    def __init__(self):
        """Construct a base Generator for code generation with default options.

        instantiate a new generator with the defaults populated for all the
        properties in the object.
        """
        self._scanner = None
        self._parser = None
        self._filename = 'out'
        self._encoding = 'direct'

    @property
    def scanner(self):
        """Get or set the scanner to be used for generation, if any.

        Query for or attempt to set the scanner to be used for code generation.
        This allows the child language Generators to be reused rather than
        recreated if attempting to generate source for multiple scanners.

        Args:
          scanner (RegularGrammar): The scanner to be used for generation. If
              generation of the scanner is no longer desired it may also be set
              to None.

        Return:
          None: The default if the scanner was not previously set.
          RegularGrammar: If scanner was set.

        Raises:
          TypeError: If `scanner` is not None or a RegularGrammar when
              attempting to set.
        """
        return self._scanner

    @scanner.setter
    def scanner(self, scanner):
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise TypeError('scanner not a RegularGrammar or None')

        self._scanner = scanner

    @property
    def parser(self):
        """Get of set the parser to be used for generation, if any.

        Query for or attempt to set the parser to be used for code generation.
        This allows the child language Generators to be reused rather than
        recreated if attempting to generate source for multiple parsers.

        Args:
          parser (ContextFreeGrammar): The parser to be used for generation. If
              generation of the parser is no longer desired it may also be set
              to None.

        Return:
          None: The default if the parser was not previously set.
          ContextFreeGrammar: If parser was set.

        Raises:
          TypeError: If `parser` is not None or a ContextFreeGrammar when
              attempting to set.
        """
        return self._parser

    @parser.setter
    def parser(self, parser):
        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise TypeError('parser not a ContextFreeGrammar or None')

        self._parser = parser

    @property
    def filename(self):
        """Get or set the base filename to be used for generation.

        Query for or attempt to set the base filename to be used for code
        generation of the scanner and/or parser.

        Args:
          filename (str): The base filename to be used for generation.

        Return:
          str: 'out' if not set (default), otherwise the last set filename.

        Raises:
          TypeError if filename is not of type string when being set.
          ValueError if an empty filename is given when being set.
        """
        return self._filename

    @filename.setter
    def filename(self, filename):
        if not isinstance(filename, str):
            raise TypeError('filename must be of type string')

        if not filename:
            raise ValueError('filename must be non empty')

        self._filename = filename

    @property
    def encoding(self):
        """Get or set the encoding to be used for generation.

        Query for or attempt to set the table encoding to be used when
        generating source for the scanner and/or parser. Possible options
        include:
          'direct': encode the table into the source.
          'table': use a small driver and utilize the table for lookup.

        Args:
          encoding (str): the encoding to use when generating code.

        Return:
          str: 'direct' if not set (default), otherwise the last set encoding.

        Raises:
          TypeError if encoding is not if type string
          ValueError if encoding is empty
          ValueError if given encoding is not recognized
        """
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        if not isinstance(encoding, str):
            raise TypeError('encoding must be of type string')

        if not encoding:
            raise ValueError('encoding must be non empty')

        if encoding not in ('table', 'direct'):
            raise ValueError('encoding type not recognized')

        self._encoding = encoding

    def _translate(self):
        """The method which subclasses must override to construct the output.

        Override this method in subclasses which should translate the (IR)
        intermediate representation of the given scanner and/or parser to the
        targeted language. It should return the files and there content in a
        dictionary allowing multiple files to be returned for a given language.
        This is the only required function a child generators must implement.

        Return:
          dict[str, str]: Generated file names/paths and associated content.

        Raises:
          NotImplementedError: If not overriden in subclasses.
        """
        raise NotImplementedError('Base Generator incapable of translation')

    def _verify_options(self):
        """Verify the current configuration of set options in the generator.

        Ensure the set options in the given generator do not conflict with one
        another and are a 'sane' configuration for generating output.

        Raises:
          ValueError: if neither a scanner nor a parser is set.
        """
        if not self.scanner and not self.parser:
            raise ValueError('scanner and/or parser must be provided for generation')

    @staticmethod
    def _verify_output(files):
        """Verify the output returned from the subclass generator.

        Ensure the subclasses generated files/content are valid and non-empty.

        Args:
          files (dict[str, str]): Generated file names/paths and content.

        Raises:
          TypeError:  If the generated output is not of type dict.
          ValueError: If no output was generated.
          TypeError:  If any generated filename is not of type string.
          ValueError: If an empty filename was generated.
          TypeError:  If any generated content is not of type string.
          ValueError: If generated file contents are empty.
        """
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

    def generate(self):
        """Generate a scanner and/or parser with the set generator options.

        Translate the compiled intermediate representation (IR) of the set
        scanner and/or parser to a given output language confined by the choices
        present in options.

        Return:
          dict[str, str]: Generated file names/paths and associated content.

        Raises:
          NotImplementedError: If generation is attempted with base Generator.
          ValueError: if neither a scanner nor a parser is set.
          TypeError:  If the generated output is not of type dict.
          ValueError: If no output was generated.
          TypeError:  If any generated filename is not of type string.
          ValueError: If an empty filename was generated.
          TypeError:  If any generated content is not of type string.
          ValueError: If generated file contents are empty.
        """
        self._verify_options()

        files = self._translate()

        Generator._verify_output(files)

        return files
