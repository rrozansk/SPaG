"""
Testing for Generator subclass objects located in src/generators/*.py
"""
import pytest
from spag.generators import __all__
from spag.scanner import RegularGrammar
from spag.parser import ContextFreeGrammar


class TestGenerator(object):
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
    def test_overrides_output_c():
        """
        Make sure the 'C' generator properly overrides the output method.
        """
        module = __import__('spag.generators.c', fromlist=['C'])
        generator = getattr(module, 'C')()
        assert generator, 'constructor failed'
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        assert generator.generate(), 'no result returned'

    @staticmethod
    @pytest.mark.xfail(
        reason='Calls super (base Generator) output method.',
        raises=NotImplementedError,
    )
    def test_overrides_output_go():
        """
        Make sure the 'Go' generator properly overrides the output method.
        """
        module = __import__('spag.generators.go', fromlist=['Go'])
        generator = getattr(module, 'Go')()
        assert generator, 'constructor failed'
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        assert generator.generate(), 'no result returned'

    @staticmethod
    @pytest.mark.xfail(
        reason='Calls super (base Generator) output method.',
        raises=NotImplementedError,
    )
    def test_overrides_output_python():
        """
        Make sure the 'Python' generator properly overrides the output method.
        """
        module = __import__('spag.generators.python', fromlist=['Python'])
        generator = getattr(module, 'Python')()
        assert generator, 'constructor failed'
        generator.scanner = RegularGrammar('test', {'foo': 'bar'})
        generator.parser = ContextFreeGrammar('test', {'S': [['a']]}, 'S')
        assert generator.generate(), 'no result returned'
