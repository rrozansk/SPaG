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
    def test_constructor():
        """
        Ensure successful creation of a Generator object.
        """
        generator = Generator()
        assert generator is not None, 'No Generator produced'

    @staticmethod
    def test_scanner_default():
        """
        Ensure default scanner retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.scanner is None, 'Invalid scanner default retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Scanner not of type RegularGrammar or None.',
        raises=TypeError,
    )
    def test_scanner_invalid():
        """
        Ensure a TypeError is raised when overwriting the Generator object's
        scanner property if it is not of type RegularGrammar or None.
        """
        generator = Generator()
        generator.scanner = 'invalid_scanner'

    @staticmethod
    def test_scanner_valid():
        """
        Ensure overwriting the scanner property works as expected when given
        proper input as a RegularGrammar.
        """
        scanner = RegularGrammar('test', {'foo': 'bar'})
        generator = Generator()
        generator.scanner = scanner
        assert generator.scanner is scanner, 'Invalid scanner set/retrieved'

    @staticmethod
    def test_scanner_none():
        """
        Ensure overwriting the scanner property works as expected when given
        proper input as None.
        """
        generator = Generator()
        generator.scanner = None
        assert generator.scanner is None, 'Invalid scanner set/retrieved'

    @staticmethod
    def test_parser_default():
        """
        Ensure default parser retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.parser is None, 'Invalid parser default retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Parser not of type ContextFreeGrammar or None.',
        raises=TypeError,
    )
    def test_parser_invalid():
        """
        Ensure a TypeError is raised when overwriting the Generator's object
        parser property if it is not of type ContextFreeGrammar or None.
        """
        generator = Generator()
        generator.parser = 'invalid_parser'

    @staticmethod
    def test_parser_valid():
        """
        Ensure overwriting the paser property works as expected when given
        proper input as a ContextFreeGrammar.
        """
        parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator = Generator()
        generator.parser = parser
        assert generator.parser is parser, 'Invalid parser set/retrieved'

    @staticmethod
    def test_parser_none():
        """
        Ensure overwriting the paser property works as expected when given
        proper input as None.
        """
        generator = Generator()
        generator.parser = None
        assert generator.parser is None, 'Invalid parser set/retrieved'

    @staticmethod
    def test_filename_default():
        """
        Ensure default filename retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.filename == 'out', 'Invalid default filename retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Filename not of type string.',
        raises=TypeError,
    )
    def test_filename_invalid():
        """
        Ensure a TypeError is raised when overwriting the Generator object's
        filename property if it is not of type string.
        """
        generator = Generator()
        generator.filename = None

    @staticmethod
    @pytest.mark.xfail(
        reason='Filename must be a non empty string.',
        raises=ValueError,
    )
    def test_filename_empty():
        """
        Ensure a ValueError is raised when overwriting the Generator object's
        filename property if it is an empty string.
        """
        generator = Generator()
        generator.filename = ''

    @staticmethod
    def test_filename_valid():
        """
        Ensure overwriting the filename property works as expected when given
        proper input as a non empty string.
        """
        generator = Generator()
        generator.filename = 'foobar'
        assert generator.filename == 'foobar', 'Invalid filename set/retrieved'

    @staticmethod
    def test_encoding_default():
        """
        Ensure default encoding retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.encoding == 'direct', 'Invalid default encoding retrieved'

    @staticmethod
    @pytest.mark.xfail(
        reason='Encoding not of type string.',
        raises=TypeError,
    )
    def test_encoding_invalid():
        """
        Ensure a TypeError is raised when overwriting the Generator object's
        encoding property if it is not of type string.
        """
        generator = Generator()
        generator.encoding = None

    @staticmethod
    @pytest.mark.xfail(
        reason='Encoding must be a non empty string.',
        raises=ValueError,
    )
    def test_encoding_empty():
        """
        Ensure a ValueError is raised when overwriting the Generator object's
        encoding property if it is an empty string.
        """
        generator = Generator()
        generator.encoding = ''

    @staticmethod
    @pytest.mark.xfail(
        reason='Encoding value not recognized.',
        raises=ValueError,
    )
    def test_encoding_unrecognized():
        """
        Ensure a ValueError is raised when overwriting the Generator object's
        encoding property if given an unrecognized string value.
        """
        generator = Generator()
        generator.encoding = 'foo'

    @staticmethod
    def test_encoding_table():
        """
        Ensure overwriting the encoding property works as expected when given
        proper input as the string 'table'.
        """
        generator = Generator()
        generator.encoding = 'table'
        assert generator.encoding == 'table', 'Invalid encoding set/retrieved'

    @staticmethod
    def test_encoding_direct():
        """
        Ensure overwriting the encoding property works as expected when given
        proper input as the string 'direct'.
        """
        generator = Generator()
        generator.encoding = 'direct'
        assert generator.encoding == 'direct', 'Invalid encoding set/retrieved'

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
        generator = Generator()
        generator.generate()

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
        generator = Generator()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
        # pylint: disable=abstract-method
        class _GenerateNothing(Generator):
            pass
        # pylint: enable=abstract-method

        generator = _GenerateNothing()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
            def _translate(self):
                return list()

        generator = _InvalidFiles()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
            def _translate(self):
                return dict()

        generator = _EmptyFiles()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
            def _translate(self):
                return {None: 'invalid'}

        generator = _InvalidFilename()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
            def _translate(self):
                return {'': 'invalid'}

        generator = _EmptyFilename()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
            def _translate(self):
                return {self.filename+'.txt': None}

        generator = _InvalidContent()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

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
            def _translate(self):
                return {self.filename+'.txt': ''}

        generator = _EmptyContent()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()

    @staticmethod
    def test_translate_requirements():
        """
        Ensure correctly overwriting the abstract method in the child Generator
        works as expected.
        """
        class _OutputRequirements(Generator):
            def _translate(self):
                return {self.filename+'.txt': 'hukarz'}

        generator = _OutputRequirements()
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()
