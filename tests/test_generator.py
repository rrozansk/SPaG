"""
Testing for Generator objects located in src/generator.py
"""
import pytest
from spag.generator import Generator
from spag.parser import ContextFreeGrammar
from spag.scanner import RegularGrammar


class TestGenerator:
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
    @pytest.mark.parametrize('scanner', [
        None,
        RegularGrammar('test', {'foo': ['b', 'a', 'r']}),
        pytest.param('invalid_scanner', marks=pytest.mark.xfail(
            reason='Scanner not of type RegularGrammar or None.',
            raises=TypeError,
        )),
    ])
    def test_scanner(scanner):
        """
        Ensure the Generator object's scanner property behaves as expected.
        """
        generator = Generator()
        generator.scanner = scanner
        assert generator.scanner is scanner, 'Invalid scanner set/retrieved'

    @staticmethod
    def test_scanner_default():
        """
        Ensure default scanner retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.scanner is None, 'Invalid scanner default retrieved'

    @staticmethod
    @pytest.mark.parametrize('parser', [
        None,
        ContextFreeGrammar('test', {'S': [['a']]}, 'S'),
        pytest.param('invalid_parser', marks=pytest.mark.xfail(
            reason='Parser not of type ContextFreeGrammar or None.',
            raises=TypeError,
        )),
    ])
    def test_parser(parser):
        """
        Ensure the Generator object's parser property behaves as expected.
        """
        generator = Generator()
        generator.parser = parser
        assert generator.parser is parser, 'Invalid parser set/retrieved'

    @staticmethod
    def test_parser_default():
        """
        Ensure default parser retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.parser is None, 'Invalid parser default retrieved'

    @staticmethod
    @pytest.mark.parametrize('filename', [
        'foobar',
        pytest.param(None, marks=pytest.mark.xfail(
            reason='Filename not of type string.',
            raises=TypeError,
        )),
        pytest.param('', marks=pytest.mark.xfail(
            reason='Filename must be a non empty string.',
            raises=ValueError,
        )),
    ])
    def test_filename(filename):
        """
        Ensure the Generator object's filename property behaves as expected.
        """
        generator = Generator()
        generator.filename = filename
        assert generator.filename == filename, 'Invalid filename set/retrieved'

    @staticmethod
    def test_filename_default():
        """
        Ensure default filename retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.filename == 'out', 'Invalid default filename retrieved'

    @staticmethod
    @pytest.mark.parametrize('encoding', [
        'table',
        'direct',
        pytest.param(None, marks=pytest.mark.xfail(
            reason='Encoding not of type string.',
            raises=TypeError,
        )),
        pytest.param('', marks=pytest.mark.xfail(
            reason='Encoding must be a non empty string.',
            raises=ValueError,
        )),
        pytest.param('foo', marks=pytest.mark.xfail(
            reason='Encoding value not recognized.',
            raises=ValueError,
        )),
    ])
    def test_encoding(encoding):
        """
        Ensure the Generator object's encoding property behaves as expected.
        """
        generator = Generator()
        generator.encoding = encoding
        assert generator.encoding == encoding, 'Invalid encoding set/retrieved'

    @staticmethod
    def test_encoding_default():
        """
        Ensure default encoding retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.encoding == 'direct', 'Invalid default encoding retrieved'

    @staticmethod
    @pytest.mark.parametrize('match', [
        'longest',
        'shortest',
        pytest.param(None, marks=pytest.mark.xfail(
            reason='Match not of type string.',
            raises=TypeError,
        )),
        pytest.param('', marks=pytest.mark.xfail(
            reason='Match must be a non empty string.',
            raises=ValueError,
        )),

        pytest.param('foo', marks=pytest.mark.xfail(
            reason='Match value not recognized.',
            raises=ValueError,
        )),
    ])
    def test_match(match):
        """
        Ensure the Generator object's match property behaves as expected.
        """
        generator = Generator()
        generator.match = match
        assert generator.match == match, 'Invalid matching-strategy set/retrieval'

    @staticmethod
    def test_matching_default():
        """
        Ensure default matching retrieval works as expected upon successful
        creation of a Generator object.
        """
        generator = Generator()
        assert generator.match == 'longest', 'Invalid default match retrieved'

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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
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
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        generator.generate()
