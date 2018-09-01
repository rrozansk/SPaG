"""
Testing for Generator objects located in src/generators/__init__.py
"""
import pytest
from src.scanner.scanner import RegularGrammar
from src.parser.parser import ContextFreeGrammar
from src.generators import Generator


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
        generator = Generator(None, None)
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    def test_constructor_valid_scanner():
        """
        Ensure successful creation of a Generator object with only a scanner.
        """
        generator = Generator(RegularGrammar('test', []), None)
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner is not of type RegularGrammar.',
        raises=TypeError,
    )
    def test_constructor_invalid_scanner():
        """
        Ensure a TypeError is raised when constructing a Generator object if the
        scanner is not of type RegularGrammar.
        """
        Generator('invalid_scanner', None)

    @staticmethod
    def test_constructor_valid_parser():
        """
        Ensure successful creation of a Generator object with only a parser.
        """
        generator = Generator(None, ContextFreeGrammar('test', {'S': ''}, 'S'))
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser is not of type ContextFreeGrammar.',
        raises=TypeError,
    )
    def test_constructor_invalid_parser():
        """
        Ensure a TypeError is raised when constructing a Generator object if the
        parser is not of type ContextFreeGrammar.
        """
        Generator(None, 'invalid_parser')

    @staticmethod
    def test_constructor_full():
        """
        Ensure successful creation of a Generator object with both scanner and
        parser.
        """
        scanner = RegularGrammar('test', [])
        parser = ContextFreeGrammar('test', {'S': ''}, 'S')
        generator = Generator(scanner, parser)
        assert generator is not None, 'Invalid Generator produced'

    @staticmethod
    def test_get_scanner():
        """
        Ensure get_scanner works as expected.
        """
        scanner = RegularGrammar('test', [])
        generator = Generator(scanner, None)
        assert generator.get_scanner() == scanner, 'Invalid scanner retrieved'

    @staticmethod
    def test_set_scanner():
        """
        Ensure set_scanner works as expected when given proper input.
        """
        scanner_1 = RegularGrammar('test', [])
        generator = Generator(scanner_1, None)
        scanner_2 = RegularGrammar('test', [])
        generator.set_scanner(scanner_2)
        assert generator.get_scanner() == scanner_2, 'Invalid scanner retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner is not of type RegularGrammar.',
        raises=TypeError,
    )
    def test_set_invalid_scanner():
        """
        Ensure a TypeError is raised when setting the Generator's object scanner
        if is not of type RegularGrammar.
        """
        generator = Generator(None, None)
        generator.set_scanner('invalid_scanner')

    @staticmethod
    def test_get_parser():
        """
        Ensure get_parser works as expected.
        """
        parser = ContextFreeGrammar('test', {'S': ''}, 'S')
        generator = Generator(None, parser)
        assert generator.get_parser() == parser, 'Invalid parser retrieved'

    @staticmethod
    def test_set_parser():
        """
        Ensure set_parser works as expected when given proper input.
        """
        parser_1 = ContextFreeGrammar('test', {'S': ''}, 'S')
        generator = Generator(None, parser_1)
        parser_2 = ContextFreeGrammar('test', {'S': ''}, 'S')
        generator.set_parser(parser_2)
        assert generator.get_parser() == parser_2, 'Invalid parser retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser is not of type ContextFreeGrammar.',
        raises=TypeError,
    )
    def test_set_invalid_parser():
        """
        Ensure a TypeError is raised when setting the Generator's object parser
        if is not of type ContextFreeGrammar.
        """
        generator = Generator(None, None)
        generator.set_parser('invalid_parser')

    @staticmethod
    @pytest.mark.xfail(
        reason='Filename is not of type str.',
        raises=TypeError,
    )
    def test_output_invalid_filename():
        """
        Ensure a TypeError is raised if the filename is not a string.
        """
        generator = Generator(None, None)
        generator.output(None)

    @staticmethod
    @pytest.mark.xfail(
        reason='Output not handled by base Generator.',
        raises=NotImplementedError,
    )
    def test_output_not_implemented():
        """
        Ensure a NotImplementedError is raised if generation to source language
        is attempted with the base Generator.
        """
        generator = Generator(None, None)
        generator.output('test_failure.txt')
