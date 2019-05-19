"""
Testing for SPaG CLI script located in spag/__main__.py
"""
import pytest
from pkg_resources import Environment


class TestSPaGCLI:
    """
    A test suite for testing the SPaG CLI script.
    """

    @staticmethod
    def test_liscence_distro():
        """
        Ensure the LISCENCE is in the distribution.
        """
        spag = Environment().__getitem__('spag')[0]
        assert spag.has_metadata('LICENSE.txt')
        pkg_license_output = spag.get_metadata('LICENSE.txt')
        git_license_output = ''
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
    def test_help_non_empty_1(script_runner):
        """
        Ensure help message output is non-empty.
        """
        ret_help = script_runner.run('spag_cli')
        assert ret_help.success
        assert ret_help.stderr == ''

    @staticmethod
    def test_help_non_empty_2(script_runner):
        """
        Ensure help message output is non-empty.
        """
        ret_help = script_runner.run('spag_cli', '--help')
        assert ret_help.success
        assert ret_help.stderr == ''

    @staticmethod
    def test_default_help(script_runner):
        """
        Ensure help is the default behavior.
        """
        ret_help = script_runner.run('spag_cli')
        assert ret_help.success
        assert ret_help.stderr == ''
        help_output = ret_help.stdout

        ret_default = script_runner.run('spag_cli', '-h')
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
        "examples/WordCount/scanner.json",
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
        "examples/WordCount/parser.json",
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

    @staticmethod
    @pytest.mark.xfail
    def test_invalid_encoding(script_runner):
        """
        Ensure an invalid encoding throws an error.
        """
        ret = script_runner.run('spag_cli', '-g', 'c', '-f', '-e', 'fast')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    @pytest.mark.xfail
    def test_invalid_match(script_runner):
        """
        Ensure an invalid match throws an error.
        """
        ret = script_runner.run('spag_cli', '-g', 'c', '-f', '-m', 'fast')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_boolean(script_runner):
        """
        Ensure an invalid boolean value in the configuration throws an error.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            encoding=direct
                            force=No
                            generate=c
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')

        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_false_boolean(script_runner):
        """
        Ensure false boolean value parses as expected.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            force=False
                            generate=c
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_conf_encoding(script_runner):
        """
        Ensure invalid configuration encoding thrown the proper error.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            encoding=fast
                            force=False
                            generate=c
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_conf_match(script_runner):
        """
        Ensure invalid configuration match throws the proper error.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            match=fast
                            encoding=direct
                            force=False
                            generate=c
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_conf(script_runner):
        """
        Ensure invalid configuration section.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[spag]
                            force=False
                            generate=c
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_scanner_file(script_runner):
        """
        Ensure invalid scanner file configuration fails.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            force=False
                            generate=c
                            scanners=examples/FOO/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_output(script_runner):
        """
        Ensure invalid generate file configuration option.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            force=False
                            generate=java
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_nothing(script_runner):
        """
        Ensure passing no parser or scanners does nothing.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            parsers=
                            scanners=
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_option(script_runner):
        """
        Ensure invalid key/value pair in file configuration throws error.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            foo=bar
                            generate=java
                            parsers=
                            scanners=
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 1
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_generate_nothing(script_runner):
        """
        Ensure generating no language still works as expected.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            generate=
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_generate_safe(script_runner):
        """
        Ensure generating again does not overwrite files.
        """
        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            force=False
                            verbose=True
                            generate=c
                            parsers=examples/Lisp/parser.json
                            scanners=examples/Lisp/scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_generate_force(script_runner):
        """
        Ensure generating again overwrite files if force flag is set.
        """
        ret = script_runner.run('spag_cli',
                                '-p', 'examples/Lisp/parser.json',
                                '-s', 'examples/Lisp/scanner.json',
                                '-g', 'c', '-f')
        assert ret.returncode == 0
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_scanner_spec(script_runner):
        """
        Ensure invalid scanner specification throws the right error.
        """
        with open('out_scanner.json', 'w') as rcfile:
            rcfile.write("{}")

        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            generate=c
                            scanners=out_scanner.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 2
        assert ret.stderr == ''
        assert ret.stdout == ''

    @staticmethod
    def test_invalid_parser_spec(script_runner):
        """
        Ensure invalid parser specification throws the right error.
        """
        with open('out_parser.json', 'w') as rcfile:
            rcfile.write("{}")

        with open('.spagrc', 'w') as rcfile:
            rcfile.write('''[SPaG]
                            generate=c
                            parsers=out_parser.json
                          ''')
        ret = script_runner.run('spag_cli', '-c', '.spagrc')
        assert ret.returncode == 3
        assert ret.stderr == ''
        assert ret.stdout == ''
