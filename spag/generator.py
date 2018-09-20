"""Base Generator which protects against bad input and return values.

The Generator is a simple superclass which protect subclasses from bad user
input when trying to generate output programs. Likewise, it also protects the
user from bad developer output. It does this by performing simple validations
before and after program generation is attempted. The base Generator also
controls the getting/setting of the parser and/or scanner used for code
generation. Each targeted language for generation should be implemented as a
subclass which only needs to override the '_translate(self, options)' method.
"""
from spag.parser import ContextFreeGrammar
from spag.scanner import RegularGrammar


class Generator(object):
    """The Base Generator which performs [in/out]put validations.

    A simple superclass object for performing validation on user input as well
    as developer output so subclasses can focus on translating the IR returned
    by the ContextFreeGrammar and RegularGrammar classes.

    Attributes:
      scanner (RegularGrammar): The scanner to be used for generation.
      parser  (ContextFreeGrammar): The parser to be used for generation.
    """

    def __init__(self, scanner=None, parser=None):
        """Construct a new base Generator.

        Set the scanner and/or parser to be used for code generation, if any,
        during the construction of the base generator.

        Args:
          scanner (RegularGrammar): The scanner to be used for generation.
          parser  (ContextFreeGrammar): The parser to be used for generation.

        Raises:
          TypeError: If `scanner` is not None or a RegularGrammar.
          TypeError: If `parser` is not None or a ContextFreeGrammar.
        """
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise TypeError('scanner not a RegularGrammar')

        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise TypeError('parser not a ContextFreeGrammar')

        self.scanner = scanner
        self.parser = parser

    def set_scanner(self, scanner=None):
        """Set the scanner to be used for generation.

        [Re]Set the scanner to be used for code generation, if any. This allows
        The child language Generators to be reused rather than recreated.

        Args:
          scanner (RegularGrammar): The scanner to be used for generation.

        Raises:
          TypeError: If `scanner` is not None or a RegularGrammar.
        """
        if not isinstance(scanner, (RegularGrammar, type(None))):
            raise TypeError('scanner not a RegularGrammar or None')

        self.scanner = scanner

    def get_scanner(self):
        """Get the scanner to be used for generation.

        Query for the scanner to be used for code generation, if any.

        Return:
          None: If the scanner is not set.
          RegularGrammar: If scanner was set.
        """
        return self.scanner

    def set_parser(self, parser=None):
        """Set the parser to be used for generation.

        [Re]Set the parser to be used for code generation, if any. This allows
        The child language Generators to be reused rather than recreated.

        Args:
          parser (ContextFreeGrammar): The parser to be used for generation.

        Raises:
          TypeError: If `parser` is not None or a ContextFreeGrammar.
        """
        if not isinstance(parser, (ContextFreeGrammar, type(None))):
            raise TypeError('parser not a ContextFreeGrammar or None')

        self.parser = parser

    def get_parser(self):
        """Get the parser to be used for generation.

        Query for the parser to be used for code generation, if any.

        Return:
          None: If the parser is not set.
          ContextFreeGrammar: If the parser was set.
        """
        return self.parser

    def _translate(self, options):
        """The method which subclasses must override to construct the output.

        Override this method in subclasses which should translate the (IR)
        intermediate representation of the given scanner and/or parser to the
        targeted language. It should return the files and there content in a
        dictionary allowing multiple files to be returned for a given language.
        This is the only required function a child generators must implement.

        Args:
          options (dict[str, union[str, bool, int, float, long]]): Choices to be
              used for code generation.

        Return:
          dict[str, str]: Generated file names/paths and associated content.

        Raises:
          NotImplementedError: If not overriden in subclasses.
        """
        raise NotImplementedError('Base Generator incapable of translation')

    @staticmethod
    def _verify_options(options):
        """Verify the given options for generation.

        Ensure the options given for generation are valid and non-empty.

        Args:
          options (dict[str, union[str, bool, int, float, long]]): Choices to be
              used for code generation.

        Raises:
          TypeError:  If options not a dictionary.
          ValueError: If options is empty.
          TypeError:  If option name not of type string.
          ValueError: If option name is empty.
          TypeError:  If option value is not a str, bool, int, float, or long.
        """
        if not isinstance(options, dict):
            raise TypeError('options not a dict')

        if not options:
            raise ValueError('options must be non empty')

        for option, value in options.items():
            if not isinstance(option, str):
                raise TypeError('option name must be of type string')

            if not option:
                raise ValueError('option name must be non empty')

            if not isinstance(value, (str, bool, int, float, long)):
                raise TypeError('option value must be of type: str, bool, int, float, long')

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

    def output(self, options):
        """Generate a scanner and/or parser with the given options.

        Translate the compiled intermediate representation (IR) of the set
        scanner and/or parser to a given output language confined by the choices
        present in options. well known option include:
          filename (str):  the basename to be used for naming.
          encoding (str):  'direct' or 'table' encoding of scanner/parser.
          scanner  (bool): whether or not to generate a scanner.
          parser   (bool): whether or not to generate a parser.

        Args:
          options (dict[str, union[str, bool, int, float, long]]): Choices to be
              used for code generation.

        Return:
          dict[str, str]: Generated file names/paths and associated content.

        Raises:
          NotImplementedError: If generation is attempted with base Generator.
          ValueError: If no scanner or parser is provided for generation.
          TypeError:  If options not a dictionary.
          ValueError: If options is empty.
          TypeError:  If option name not of type string.
          ValueError: If option name is empty.
          TypeError:  If option value must not of type string or bool.
          TypeError:  If the generated output is not of type dict.
          ValueError: If no output was generated.
          TypeError:  If any generated filename is not of type string.
          ValueError: If an empty filename was generated.
          TypeError:  If any generated content is not of type string.
          ValueError: If generated file contents are empty.
        """
        if not self.scanner and not self.parser:
            raise ValueError('scanner and/or parser must be provided for generation')

        Generator._verify_options(options)

        files = self._translate(options)

        Generator._verify_output(files)

        return files
