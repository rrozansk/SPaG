"""
Testing for Generator subclass objects located in src/generators/*.py
"""
import pytest
from spag.generators import __all__
from spag.scanner import RegularGrammar
from spag.parser import ContextFreeGrammar


class TestGenerator:
    """
    A test suite for testing the Generator subclass object.
    """

    @staticmethod
    def test_supported_generators():
        """
        Assert __all__ (i.e. the generators we support officially) is what is
        expected.
        """
        assert len(__all__) == 3
        supported = sorted(['c', 'go', 'python'])
        _supported = sorted(__all__)
        for key, value in enumerate(supported):
            assert _supported[key] == value

    @staticmethod
    def test_importable_generators():
        """
        Ensure all supported generators are importable and follow the proper
        naming conventions.
        """
        for language in __all__:
            cls = language.capitalize()
            module = __import__('spag.generators.'+language, fromlist=[cls])
            generator = getattr(module, cls)
            assert generator(), 'constructor failed'

    @staticmethod
    @pytest.mark.parametrize("language", [
        "c",
        pytest.param("go", marks=pytest.mark.xfail(
            reason='Calls super (base Generator) output method.',
            raises=NotImplementedError,
        )),
        pytest.param("python", marks=pytest.mark.xfail(
            reason='Calls super (base Generator) output method.',
            raises=NotImplementedError,
        )),
    ])
    def test_overrides_output(language):
        """
        Make sure the generators properly override the output method.
        """
        module = __import__('spag.generators.'+language.lower(), fromlist=[language.capitalize()])
        generator = getattr(module, language.capitalize())()
        assert generator, 'constructor failed'
        generator.scanner = RegularGrammar('test', {'foo': ['b', 'a', 'r']})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        assert generator.generate(), 'no result returned'
