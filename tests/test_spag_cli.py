"""
Testing for SPaG CLI script located in spag/__main__.py
"""
import pytest
#from spag.__main__ import main


class TestSPaGCLI:
    """
    A test suite for testing the SPaG CLI script.
    """

    @staticmethod
    def test_version(script_runner):
        """
        Ensure the version matches the expected output.
        """
        ret = script_runner.run('spag_cli', '--version')
        assert ret.success
        assert ret.stdout == 'SPaG-CLI v1.0.0a0\n'
        assert ret.stderr == ''

    @staticmethod
    def test_default_help():
        """
        Ensure help is the default behavior.
        """
        return 0

    @staticmethod
    def test_help_non_empty():
        """
        Ensure help message output is non-empty.
        """
        return 0

    @staticmethod
    def test_rcfile_generation():
        """
        Ensure valid configuration file (INI) generation.
        """
        return 0

    @staticmethod
    def test_rcfile_input():
        """
        Ensure the default configuration file has sane defaults.
        """
        return 0

    @staticmethod
    def test_scanner_examples():
        """
        Ensure all scanners under the examples directory are sucessfully run through SPaG.
        """
        return 0

    @staticmethod
    def test_parser_examples():
        """
        Ensure all parsers under the examples directory are sucessfully run through SPaG.
        """
        return 0

    @staticmethod
    def test_liscence_distro():
        """
        Ensure the LISCENCE is in distribution.
        """
        # import pkg_resources
        return 0

    @staticmethod
    @pytest.mark.xfail(
        reason='...',
        raises=ValueError,
    )
    def test_invalid_language():
        """
        Ensure invalid languages produce an error.
        """
        raise ValueError('...')

    # NOTE: test other flags as well
    # - 'force' successfully overwrites files
    # - 'force' fails if not True or False
    # - 'output' is contained in the filename
    # - 'output' fails if not string
    # - 'encoding'
    # - 'generate'
    # - 'parsers'
    # - 'scanners'
    # - 'time'
    # - 'verbose'
