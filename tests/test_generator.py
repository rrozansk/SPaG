# pylint: disable=abstract-method
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
"""
Testing for Generator objects located in src/generator.py
"""
import pytest
from spag.scanner import RegularGrammar
from spag.parser import ContextFreeGrammar
from spag.generator import Generator


class TestGenerator(object):
    """
    A test suite for testing the base Generator object.
    """

    @staticmethod
    def test_constructor_empty():
        """
        Ensure successful creation of a Generator object with no scanner or
        parser.
        """
        generator = Generator()
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    def test_constructor_scanner():
        """
        Ensure successful creation of a Generator object with only a scanner.
        """
        generator = Generator(RegularGrammar('test', {'foo': 'bar'}), None)
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner not of type RegularGrammar.',
        raises=TypeError,
    )
    def test_constructor_scanner_invalid():
        """
        Ensure a TypeError is raised when constructing a Generator object if the
        scanner is not of type RegularGrammar.
        """
        Generator('invalid_scanner', None)

    @staticmethod
    def test_constructor_parser():
        """
        Ensure successful creation of a Generator object with only a parser.
        """
        generator = Generator(None, ContextFreeGrammar('test', {'S': [['a']]}, 'S'))
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser not of type ContextFreeGrammar.',
        raises=TypeError,
    )
    def test_constructor_parser_invalid():
        """
        Ensure a TypeError is raised when constructing a Generator object if the
        parser is not of type ContextFreeGrammar.
        """
        Generator(None, 'invalid_parser')

    @staticmethod
    def test_constructor_scanner_parser():
        """
        Ensure successful creation of a Generator object with both a scanner and
        parser.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    def test_scanner_get():
        """
        Ensure scanner retrieval works as expected upon successful creation of a
        Generator object.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        generator = Generator(scanner, None)
        assert generator.get_scanner() is scanner, 'Invalid scanner retrieved'

    @staticmethod
    def test_scanner_set():
        """
        Ensure overwriting the scanner works as expected when given proper input.
        """
        scanner_1 = RegularGrammar('test', {'foo': 'bar'})
        generator = Generator(scanner_1, None)
        scanner_2 = RegularGrammar('test', {'foo': 'bar'})
        generator.set_scanner(scanner_2)
        assert generator.get_scanner() is scanner_2, 'Invalid scanner retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner not of type RegularGrammar.',
        raises=TypeError,
    )
    def test_scanner_set_invalid():
        """
        Ensure a TypeError is raised when overwriting the Generator's object
        scanner if is not of type RegularGrammar.
        """
        generator = Generator(None, None)
        generator.set_scanner('invalid_scanner')

    @staticmethod
    def test_parser_get():
        """
        Ensure parser retrieval works as expected upon successful creation of a
        Generator object.
        """
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(None, parser)
        assert generator.get_parser() is parser, 'Invalid parser retrieved'

    @staticmethod
    def test_parser_set():
        """
        Ensure overwriting the parser works as expected when given proper input.
        """
        parser_1 = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(None, parser_1)
        parser_2 = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.set_parser(parser_2)
        assert generator.get_parser() is parser_2, 'Invalid parser retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser not of type ContextFreeGrammar.',
        raises=TypeError,
    )
    def test_parser_set_invalid():
        """
        Ensure a TypeError is raised when overwriting the Generator's object
        parser if is not of type ContextFreeGrammar.
        """
        generator = Generator(None, None)
        generator.set_parser('invalid_parser')

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner or parser required for generation.',
        raises=ValueError,
    )
    def test_output_no_scanner_parser():
        """
        Ensure a ValueError is raised if generation to source language
        is attempted without a set scanner and parser.
        """
        generator = Generator(None, None)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Options not of type dict.',
        raises=TypeError,
    )
    def test_output_options_invalid():
        """
        Ensure a TypeError is raised if the options is not a dict when
        attempting to output a scanner and/or parser.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        generator.output(None)

    @staticmethod
    @pytest.mark.xfail(
        reason='Options is an empty dict.',
        raises=ValueError,
    )
    def test_output_options_empty():
        """
        Ensure a ValueError is raised if the options is an empty dict when
        attempting to output a scanner and/or parser.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        generator.output(dict())

    @staticmethod
    @pytest.mark.xfail(
        reason='Options invalid dict key.',
        raises=TypeError,
    )
    def test_output_options_key_invalid():
        """
        Ensure a TypeError is raised if the options provided when attempting to
        output a scanner and/or parser contain an invalid key.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        generator.output({True: 'foo'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Options empty dict key.',
        raises=ValueError,
    )
    def test_output_options_key_empty():
        """
        Ensure a ValueError is raised if the options provided when attempting to
        output a scanner and/or parser contain an empty key.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        generator.output({'': 'bar'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Options invalid dict value.',
        raises=TypeError,
    )
    def test_output_options_value_invalid():
        """
        Ensure a TypeError is raised if the options provided when attempting to
        output a scanner and/or parser contain an invalid value type.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        generator.output({'invalid': scanner})

    @staticmethod
    @pytest.mark.xfail(
        reason='Output not handled by base Generator.',
        raises=NotImplementedError,
    )
    def test_translate_not_implemented():
        """
        Ensure a NotImplementedError is raised if generation to source language
        is attempted with the base Generator.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Output not overridden by child Generator.',
        raises=NotImplementedError,
    )
    def test_translate_not_overridden():
        """
        Ensure a NotImplementedError is raised if a child Generator does not
        override the private _translate(self, filename) method.
        """
        class _GenerateNothing(Generator):
            pass

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _GenerateNothing(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Invalid output type of child Generator.',
        raises=TypeError,
    )
    def test_translate_return_invalid():
        """
        Ensure a TypeError is raised if a child Generator returns invalid data.
        """
        class _InvalidFiles(Generator):
            def _translate(self, options):
                return list()

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _InvalidFiles(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Empty output of child Generator.',
        raises=ValueError,
    )
    def test_translate_return_empty():
        """
        Ensure a ValueError is raised if a child Generator returns empty data.
        """
        class _EmptyFiles(Generator):
            def _translate(self, options):
                return dict()

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _EmptyFiles(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Invalid filename output of child Generator.',
        raises=TypeError,
    )
    def test_translate_filename_invalid():
        """
        Ensure a TypeError is raised if a child Generator returns an invalid
        filename.
        """
        class _InvalidFilename(Generator):
            def _translate(self, options):
                return {None: 'invalid'}

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _InvalidFilename(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Empty filename output of child Generator.',
        raises=ValueError,
    )
    def test_translate_filename_empty():
        """
        Ensure a ValueError is raised if a child Generator returns an empty
        filename.
        """
        class _EmptyFilename(Generator):
            def _translate(self, options):
                return {'': 'invalid'}

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _EmptyFilename(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Invalid file contents output of child Generator.',
        raises=TypeError,
    )
    def test_translate_content_invalid():
        """
        Ensure a TypeError is raised if a child Generator returns invalid file
        contents.
        """
        class _InvalidContent(Generator):
            def _translate(self, options):
                return {options['filename']+'.txt': None}

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _InvalidContent(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    @pytest.mark.xfail(
        reason='Empty file contents output of child Generator.',
        raises=ValueError,
    )
    def test_translate_content_empty():
        """
        Ensure a ValueError is raised if a child Generator returns empty file
        contents.
        """
        class _EmptyContent(Generator):
            def _translate(self, options):
                return {options['filename']+'.txt': ''}

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _EmptyContent(scanner, parser)
        generator.output({'filename': 'test_failure.txt'})

    @staticmethod
    def test_translate_requirements():
        """
        Ensure correctly overwriting the abstract method in the child Generator
        works as expected.
        """
        class _OutputRequirements(Generator):
            def _translate(self, options):
                return {options['filename']+'.txt': 'hukarz'}

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _OutputRequirements(scanner, parser)
        generator.output({'filename': 'test_success.txt'})

    @staticmethod
    def test_translate_option_types():
        """
        Ensure correctly overwriting the abstract method in the child Generator
        works as expected when given option with the correct types.
        """
        class _OutputRequirements(Generator):
            def _translate(self, options):
                return {options['filename']+'.txt': 'hukarz'}

        scanner = RegularGrammar('test', {'foo': 'bar'})
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = _OutputRequirements(scanner, parser)
        generator.output({
            'filename': 'test_success.txt',
            'encoding': 'direct',
            'foo': False,
            'bar': 45,
            'baz': 4.7,
            'ber': 450L
        })
