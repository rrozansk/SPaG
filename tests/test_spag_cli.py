"""
Testing for SPaG CLI script located in spag/__main__.py
"""
import pytest
from pkg_resources import resource_string
# NOTE 1: expand tests to ensure other flags behave as expected.
# NOTE 2: when spag_cli is run in process i dont get any expected output!?


class TestSPaGCLI:
    """
    A test suite for testing the SPaG CLI script.
    """

    @staticmethod
    def test_liscence_distro():
        """
        Ensure the LISCENCE is in the distribution.
        """
        pkg_license_output = resource_string('spag', 'LICENSE.txt').decode('ascii')
        with open('LICENSE.txt') as fd:
            git_license_output = fd.read()
        assert git_license_output == pkg_license_output

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
    def test_help_non_empty(script_runner):
        """
        Ensure help message output is non-empty.
        """
        ret_help = script_runner.run('spag_cli', '--help')
        assert ret_help.success
        assert ret_help.stderr == ''
        assert ret_help.stdout != ''

    @staticmethod
    @pytest.mark.script_launch_mode('subprocess')
    def test_default_help(script_runner):
        """
        Ensure help is the default behavior.
        """
        ret_help = script_runner.run('spag_cli', '-h')
        assert ret_help.success
        assert ret_help.stderr == ''
        help_output = ret_help.stdout

        ret_default = script_runner.run('spag_cli')
        assert ret_default.success
        assert ret_default.stderr == ''
        default_output = ret_default.stdout

        assert help_output == default_output

    @staticmethod
    def test_rcfile_generation(script_runner):
        """
        Ensure valid configuration file (INI) generation.
        """
        ret_help = script_runner.run('spag_cli', '-G')
        assert ret_help.success
        assert ret_help.stderr == ''
        assert ret_help.stdout == ''
        with open('.spagrc') as fd:
            configuration = fd.read()
        assert configuration != ''

    @staticmethod
    def test_rcfile_input(script_runner):
        """
        Ensure the default configuration file has sane defaults.
        """
        ret_help = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret_help.returncode == 0
        assert ret_help.stderr == ''
        assert ret_help.stdout == ''

    @staticmethod
    @pytest.mark.parametrize("specification", [
        "examples/INI/scanner.json",
        "examples/JSON/scanner.json",
        "examples/Lisp/scanner.json",
        pytest.param("examples/Foobar/hukarz.json", marks=pytest.mark.xfail),
    ])
    def test_scanner_examples(script_runner, specification):
        """
        Ensure all scanners under the examples directory are sucessfully run
        through SPaG.
        """
        ret = script_runner.run('spag_cli', '-s', specification, '-v', '-t')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    @pytest.mark.parametrize("specification", [
        "examples/INI/parser.json",
        "examples/JSON/parser.json",
        "examples/Lisp/parser.json",
        pytest.param("examples/Foobar/hukarz.json", marks=pytest.mark.xfail),
    ])
    def test_parser_examples(script_runner, specification):
        """
        Ensure all parsers under the examples directory are sucessfully run
        through SPaG.
        """
        ret = script_runner.run('spag_cli', '-p', specification, '-v', '-t')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    @pytest.mark.parametrize("language", [
        "c",
        "go",
        "python",
        pytest.param("hukarz", marks=pytest.mark.xfail),
    ])
    def test_generator_examples(script_runner, language):
        """
        Ensure all supported generators are sucessful when imported.
        """
        ret = script_runner.run('spag_cli', '-g', language, '-f')
        assert ret.returncode == 4
        assert ret.stderr == ''
        assert ret.stdout == ''
