"""A Python CLI script for scanner/parser generation using SPaG.

This script deals with all the file I/O including the definition of the input
file specification. It also properly handles the dynamic importing required
for the generator(s) of interest.
"""
from argparse import ArgumentParser, Action
from configparser import ConfigParser
from enum import IntEnum, unique
from json import loads
from os.path import isfile
from sys import argv, stdout
from time import time
from spag.generators import __all__ as languages
from spag.parser import ContextFreeGrammar
from spag.scanner import RegularGrammar


@unique
class Exit(IntEnum):
    """The Exit enumeration aggregates all possible exit codes for this script.

    Exit represents a unique collection of possible exit codes used by this
    script so that the exit status are well defined.
    """

    SUCCESS = 0         # Everything ran fine.
    INVALID_ARGS = 1    # Invalid CLI arguments supplied.
    INVALID_SCANNER = 2 # Invalid scanner specification.
    INVALID_PARSER = 3  # Invalid parser specification.
    FAIL_GENERATE = 4   # Program generation failed.

class DynamicGeneratorImport(Action):
    """Dynamically import the generator(s) required for source output."""

    @staticmethod
    def gather(generator):
        """Dynamically import the generator specified."""
        cls = generator.capitalize()
        module = __import__('spag.generators.'+generator, fromlist=[cls])
        return getattr(module, cls)

    def __call__(self, parser, namespace, values, option_string=None):
        generators = [DynamicGeneratorImport.gather(language) for language in values]
        setattr(namespace, self.dest, generators)

class CollectScannerSpecifications(Action):
    """Collect the JSON scanner specification(s) from file(s)."""

    _mapping = {
        '\\*': RegularGrammar.kleene_star(),
        '\\+': RegularGrammar.kleene_plus(),
        '\\.': RegularGrammar.concatenation(),
        '\\|': RegularGrammar.alternative(),
        '\\?': RegularGrammar.maybe(),
        '\\(': RegularGrammar.left_group(),
        '\\)': RegularGrammar.right_group(),
        '\\[': RegularGrammar.left_class(),
        '\\]': RegularGrammar.right_class(),
        '\\-': RegularGrammar.character_range(),
        '\\^': RegularGrammar.character_negation(),
        '\\{': RegularGrammar.left_interval(),
        '\\}': RegularGrammar.right_interval()
    }

    @staticmethod
    def collect(specification_file):
        """Collect the JSON specification from file."""
        specification = loads(specification_file.read())

        for expression in specification.get('expressions', {}).values():
            for idx, char in enumerate(expression):
                expression[idx] = CollectScannerSpecifications._mapping.get(char, char)

        return specification

    def __call__(self, parser, namespace, values, option_string=None):
        specifications = [CollectScannerSpecifications.collect(specification) for specification in values]
        setattr(namespace, self.dest, specifications)

class CollectParserSpecifications(Action):
    """Collect the JSON parser specification(s) from file(s)."""

    def __call__(self, parser, namespace, values, option_string=None):
        specifications = [loads(specification.read()) for specification in values]
        setattr(namespace, self.dest, specifications)

class CollectConfiguration(Action):
    """Collect the configuration (i.e. command line args) for the generator."""

    @staticmethod
    def bool(string):
        """Convert a string representation of a boolean to a python boolean."""
        if string == 'True':
            return True
        if string == 'False':
            return False
        raise ValueError('invalid boolean input value')

    def __call__(self, parser, namespace, values, option_string=None):
        configuration = ConfigParser()
        configuration.read_file(values)

        if not configuration.has_section('SPaG'):
            raise ValueError('missing runtime configuration section \'SPaG\'')

        for setting, value in configuration.items('SPaG'):
            if setting == 'encoding':
                if value not in ('table', 'direct'):
                    raise ValueError('invalid encoding value')
            elif setting == 'match':
                if value not in ('longest', 'shortest'):
                    raise ValueError('invalid match value')
            elif setting == 'generate':
                value = [lang.strip() for lang in value.split(',')]
                if len(value) == 1 and not value[0]:  # Empty setting check
                    value = []
                generators = []
                for language in value:
                    if language not in languages:
                        raise ValueError('unrecognized language for generation')
                    generators.append(DynamicGeneratorImport.gather(language))
                value = generators
            elif setting in ('parsers', 'scanners'):
                value = [spec.strip() for spec in value.split(',')]
                if len(value) == 1 and not value[0]:  # Empty setting check
                    value = []
                specifications = []
                for specification in value:
                    if not isfile(specification):
                        raise ValueError('input specification must be a file location')
                    with open(specification) as input_specification:
                        if setting == 'parsers':
                            specifications.append(loads(input_specification.read()))
                        elif setting == 'scanners':
                            specifications.append(CollectScannerSpecifications.collect(input_specification))
                value = specifications
            elif setting in ('force', 'time', 'verbose'):
                value = CollectConfiguration.bool(str(value))
            elif setting in ('configuration', 'output'):
                pass
            else:
                raise ValueError('unrecognized option: {0}'.format(setting))

            setattr(namespace, setting, value)

class GenerateConfiguration(Action):
    """Generate the configuration file for the generator."""

    def __call__(self, parser, namespace, values, option_string=None):
        with open(values, 'w') as rcfile:
            rcfile.write('''[SPaG]
# Path to the runtime configuration file.
# NOTE: Ignored and only present to mirror the command line option.
configuration={0}

# Choose the scanner/parser source encoding method. options include: 'table'
# or 'direct'.
encoding=direct

# Choose the scanner/parser source matching method. options include: 'longest'
# or 'shortest'.
match=longest

# Overwrite pre-exisintg files if they exist. Possible values include 'True' or
# 'False'.
force=True

# List any language(s) targeted for generation.
generate=c

# Base filename to derive the generated output filename(s).
output=out

# File path(s) to the JSON parser specification(s), if any.
# The file should contain a dictionary with keys:
#   - name (str): BNF grammar name.
#   - expressions (dict[str]list[list[str]]): Map [non]terminals to list of rules.
#   - start (str): nonterminal start rule.
parsers=examples/INI/parser.json,
        examples/JSON/parser.json,
        examples/Lisp/parser.json

# File path(s) to the JSON scanner specification(s), if any.
# The file should contain a dictionary with keys:
#   - name (str): Regular grammar name.
#   - expressions (dict[str]list[str]): Map tokens to sequences.
scanners=examples/INI/scanner.json,
         examples/JSON/scanner.json,
         examples/Lisp/scanner.json

# Time the various components and report it. Possible values include 'True' or
# 'False'.
time=True

# Output extra messages when run. Possible values include 'True' or 'False'.
verbose=True
'''.format(values))
        exit(Exit.SUCCESS)

def cli_program():
    """
    create a cli program
    """
    cli = ArgumentParser(
        prog='SPaG-CLI',
        usage='$ spag_cli --help',
        description='''
        A simple CLI (Command Line Interface) script which reads input file
        specification(s) to generate lexers and/or parsers for a given set of
        output languages with the use of the SPaG framework.
        ''',
        epilog='''
        As noted above it is possible to supply any number of scanners, parsers, and
        generators. This allows easy generation of any number of specifications for
        as many output languages desired. Simply stated this CLI script drives the
        genration of the cross product of LANGUAGES x SCANNERS x PARSERS. Also note
        it is possible to override configuration file defaults with command line
        flags as long as the flags are passed after the configuration file option.
        For more information on SPaG, it capabilities, limitation, and more, as well
        as numerous input file examples for scanners and parsers see the README.md
        and examples/ directory located in the github repository here:
        https://github.com/rrozansk/SPaG Also take note that this script adheres to
        well defined exit status: 0: Everything ran fine. 1: Invalid CLI arguments
        supplied. 2: Invalid scanner specification. 3: Invalid parser specification.
        4: Program generation failed.
        ''',
        add_help=False,
        allow_abbrev=False
    )

    cli.add_argument('-c', '--configuration', type=open, metavar='rcfile',
                     action=CollectConfiguration,
                     help='Collect arguments from rcfile instead of command line.')
    cli.add_argument('-e', '--encoding', type=str, default='direct',
                     choices=('table', 'direct'),
                     help='Source program encoding to use for the generated output.')
    cli.add_argument('-f', '--force', action='store_true',
                     help='Overwrite pre-exisitng output file(s).')
    cli.add_argument('-g', '--generate', type=str, nargs='*', default=[],
                     choices=languages, action=DynamicGeneratorImport,
                     help='Target language(s) for code generation.')
    cli.add_argument('-G', '--generate-rcfile', action=GenerateConfiguration, nargs='?',
                     default='.spagrc', const='.spagrc', metavar='rcfile',
                     help='Generate an rcfile and exit; .spagrc if not specified.')
    cli.add_argument('-h', '--help', action='store_true',
                     help='Show this help message and exit. The default behavior if '
                          'no arguments are supplied.')
    cli.add_argument('-m', '--match', type=str, default='longest',
                     choices=('longest', 'shortest'),
                     help='Source program text matching strategy to use in the '
                     'generated program.')
    cli.add_argument('-o', '--output', action='store', type=str, default='out',
                     metavar='base-filename',
                     help='Base-filename to derive generated output filename(s).')
    cli.add_argument('-p', '--parsers', type=open, action=CollectParserSpecifications,
                     default=[], nargs='*', metavar='filepath',
                     help='File path(s) to the JSON parser specification(s). '
                          'The file should contain a JSON dictionary with keys: '
                          '\'name\' (str), \'expressions\' '
                          '(dict[str]list[list[str]]), and \'start\' (str). The '
                          'first represents the BNF grammar\'s name. The second '
                          'represents a mapping of [non]terminals to a a list of '
                          'rules, with [] representing epsilon. The third '
                          'represents the nonterminal start rule fo the grammar.')
    cli.add_argument('-s', '--scanners', type=open, action=CollectScannerSpecifications,
                     default=[], nargs='*', metavar='filepath',
                     help='File path(s) to the JSON scanner specification(s). '
                          'The file should contain a JSON dictionary with keys: '
                          '\'name\' (str), and \'expressions\' '
                          '(dict[str]list[str]). The first represents the regular '
                          'grammar\'s name. The second represents a mapping of '
                          'token names to a sequence representing the expression. '
                          'The strings in the sequence should be of length one '
                          'unless excaping an operator (*,+,.,|,?,(,),[,],-,^).')
    cli.add_argument('-t', '--time', action='store_true',
                     help='Display the wall time taken for each component.')
    cli.add_argument('-v', '--verbose', action='store_true',
                     help='Output more information when running.')
    cli.add_argument('-V', '--version', action='version',
                     version='SPaG-CLI v1.0.0a0',
                     help='Show version information and exit.')
    return cli

# pylint: disable=too-many-branches,too-many-statements
def main():
    """
    main is the entry point which acts like a cli program.
    """
    cli = cli_program()
    try:
        args = vars(cli.parse_args())
    except Exception as exception:
        stdout.write('Failed to parse arguments:\n{0}\n'.format(exception))
        stdout.flush()
        exit(Exit.INVALID_ARGS)

    if len(argv) < 2 or args['help']:
        cli.print_help()
        exit(Exit.SUCCESS)

    start, end = None, None

    scanners = []
    for scanner in args['scanners']:
        if args['verbose']:
            stdout.write('Compiling {0} scanner specification...'.format(scanner['name']))
            stdout.flush()
        start = time()
        try:
            scanners.append(RegularGrammar(**scanner))
        except Exception as exception:
            stdout.write('Failed to create scanner:\n{0}\n'.format(exception))
            stdout.flush()
            exit(Exit.INVALID_SCANNER)
        end = time()
        if args['verbose']:
            stdout.write('done\n')
            stdout.flush()
        if args['time']:
            stdout.write('Elapsed time ({0} scanner): {1}s\n'.format(scanner['name'],
                                                                     end-start))
            stdout.flush()

    parsers = []
    for parser in args['parsers']:
        if args['verbose']:
            stdout.write('Compiling {0} parser specification...'.format(parser['name']))
            stdout.flush()
        start = time()
        try:
            parsers.append(ContextFreeGrammar(**parser))
        except Exception as exception:
            stdout.write('Failed to create parser:\n{0}\n'.format(exception))
            stdout.flush()
            exit(Exit.INVALID_PARSER)
        end = time()
        if args['verbose']:
            stdout.write('done\n')
            stdout.flush()
        if args['time']:
            stdout.write('Elapsed time ({0} parser): {1}s\n'.format(parser['name'],
                                                                    end-start))
        stdout.flush()

    generators = []
    for generator in args['generate']:
        target = generator.__name__
        generator = generator()
        generator.encoding = args['encoding']
        generator.match = args['match']
        generator.filename = args['output']
        generators.append((target, generator))

    # Cross product: GENERATORS x SCANNERS x PARSERS
    output = ((generator, scanner, parser)
              for generator in generators
              for scanner in (scanners or [None])
              for parser in (parsers or [None]))

    for (target, generator), scanner, parser in output:
        generator.parser = parser
        generator.scanner = scanner
        if scanner:
            target = target + '_' + scanner.name
        if parser:
            target = target + '_' + parser.name
        if args['verbose']:
            stdout.write('Generating {0} code...'.format(target))
            stdout.flush()
        start = time()
        try:
            files = generator.generate()
        except Exception as exception:
            stdout.write('Failed to generate program:\n{0}\n'.format(exception))
            stdout.flush()
            exit(Exit.FAIL_GENERATE)
        end = time()
        if args['verbose']:
            stdout.write('done\n')
            stdout.flush()
        if args['time']:
            stdout.write('Elapsed time (generator: {0}) {1}s\n'.format(target,
                                                                       end-start))
            stdout.flush()

        for name, content in files.items():
            if isfile(name) and not args['force']:
                if args['verbose']:
                    stdout.write('{0} already exists; not overwriting.\n'.format(name))
                    stdout.flush()
                continue

            with open(name, 'w') as fd:
                if args['verbose']:
                    stdout.write('Outputting {0} to disk...\n'.format(fd.name))
                    stdout.flush()
                fd.write(content)

    stdout.flush()
    exit(Exit.SUCCESS)
# pylint: enable=too-many-branches,too-many-statements

# python -m spag
if __name__ == '__main__':
    main()
