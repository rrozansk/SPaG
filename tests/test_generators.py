"""
Testing for Generator subclass objects located in src/generators/*.py
"""
import pytest
from spag.generators import __all__


class TestGenerator(object):
    """
    A test suite for testing the Generator subclass object.
    """

    @staticmethod
    def test_supported_generators():
        """
        Ensure __all__ (i.e. the generators we support officially) is what is
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
        Ensure all __all__ (i.e. the generators we support officially) are
        importable and follow the proper conventions for naming.
        """
        for language in __all__:
            cls = language.capitalize()
            module = __import__('spag.generators.'+language, fromlist=[cls])
            generator = getattr(module, cls)
            assert generator(), 'constructor failed'

    @staticmethod
    @pytest.mark.xfail(
        reason='Calls super (base Generator) output method.',
        raises=NotImplementedError,
    )
    def test_overrides_output():
        """
        ...
        """
        pass
