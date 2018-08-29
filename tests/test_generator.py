"""
Testing for Generator objects located in generators/__init__.py
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
        Generator(None, None)

    @staticmethod
    def test_constructor_scanner():
        """
        Ensure successful creation of a Generator object with only a scanner.
        """
        Generator(RegularGrammar('test', []), None)

    @staticmethod
    def test_constructor_parser():
        """
        Ensure successful creation of a Generator object with only a parser.
        """
        Generator(None, ContextFreeGrammar('test', {'S': ''}, 'S'))

    @staticmethod
    def test_constructor():
        """
        Ensure successful creation of a Generator object with no scanner and
        parser.
        """
        scanner = RegularGrammar('test', [])
        parser = ContextFreeGrammar('test', {'S': ''}, 'S')
        Generator(scanner, parser)

    @staticmethod
    def test_get_scanner():
        """
        Ensure get_scanner works correctly.
        """
        generator = Generator(RegularGrammar('test', []), None)
        generator.get_scanner()

    @staticmethod
    def test_set_scanner():
        """
        Ensure set_scanner works correctly when given proper input.
        """
        generator = Generator(RegularGrammar('test', []), None)
        generator.set_scanner(RegularGrammar('test', []))

    @staticmethod
    def test_get_parser():
        """
        Ensure get_parser works correctly.
        """
        generator = Generator(None, ContextFreeGrammar('test', {'S': ''}, 'S'))
        generator.get_parser()

    @staticmethod
    def test_set_parser():
        """
        Ensure set_parser works correctly when given proper input.
        """
        generator = Generator(None, ContextFreeGrammar('test', {'S': ''}, 'S'))
        generator.set_parser(ContextFreeGrammar('test', {'S': ''}, 'S'))

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner is not of type RegularGrammar.',
        raises=ValueError,
    )
    def test_constructor_invalid_scanner():
        """
        Ensure an error is thrown when constructing a Generator object if the
        scanner is not of type RegularGrammar.
        """
        Generator('invalid_scanner', None)

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner is not of type RegularGrammar.',
        raises=ValueError,
    )
    def test_set_invalid_scanner():
        """
        Ensure an error is thrown when setting the Generator's object scanner if
        is not of type RegularGrammar.
        """
        generator = Generator(None, None)
        generator.set_scanner('invalid_scanner')

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser is not of type ContextFreeGrammar.',
        raises=ValueError,
    )
    def test_constructor_invalid_parser():
        """
        Ensure an error is thrown when constructing a Generator object if the
        parser is not of type ContextFreeGrammar.
        """
        Generator(None, 'invalid_parser')

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser is not of type ContextFreeGrammar.',
        raises=ValueError,
    )
    def test_set_invalid_parser():
        """
        Ensure an error is thrown when setting the Generator's object parser if
        is not of type ContextFreeGrammar.
        """
        generator = Generator(None, None)
        generator.set_parser('invalid_parser')

    @staticmethod
    @pytest.mark.xfail(
        reason='Filename is not of type str.',
        raises=ValueError,
    )
    def test_output_invalid_filename():
        """
        Ensure an error is thrown if the filename is not a string.
        """
        generator = Generator(None, None)
        generator.output(None)

    @staticmethod
    @pytest.mark.xfail(
        reason='Output not handled by base Generator.',
        raises=ValueError,
    )
    def test_output_invalid():
        """
        Ensure an error is thrown if generation to source language is attempted
        with the base Generator.
        """
        generator = Generator(None, None)
        generator.output('test_failure.txt')
