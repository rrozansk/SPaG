#! /usr/bin/python
# pylint: disable=too-few-public-methods

"""A Python CLI script for scanner/parser generation using SPaG.

This script deals with all the file I/O including the definition of the input
file specification. It also properly handles the dynamic importing required
for the generators of interest.
"""
from argparse import ArgumentParser, Action
from os.path import isfile
from sys import stdout
from time import time
from spag.generators import __all__ as languages
from spag.parser import ContextFreeGrammar
from spag.scanner import RegularGrammar

class DynamicGeneratorImport(Action):
    """Dynamically import the generator(s) required for source output."""

    def __call__(self, parser, namespace, values, option_string=None):
        generators = []
        for language in values:
            cls = language.capitalize()
            module = __import__('spag.generators.'+language, fromlist=[cls])
            generator = getattr(module, cls)
            generators.append(generator)
        setattr(namespace, self.dest, generators)

class CollectSpecification(Action):
    """Collect the specification for a scanner or parser from file."""

    def __call__(self, parser, namespace, values, option_string=None):
        name, rules = None, []
        for line in values:
            items = line.split(None, 1)
            if not items:
                continue

            if name is None:
                if len(items) != 1:
                    raise ValueError('Invalid file format - name')
                name = items[0]
                continue

            if len(items) != 2:
                raise ValueError('Invalid file format - rule')

            rules.append((items[0], items[1].rstrip()))

        if name is None:
            raise ValueError('Specification must be non empty.')

        setattr(namespace, self.dest, {'name': name, 'rules': rules})

CLI = ArgumentParser(
    prog='SPaG-CLI',
    usage='$ generate.py --help',
    description='''
    A simple CLI (Command Line Interface) script which reads some input file
    specification(s) to generate lexers and/or parsers for a given set of
    output languages with the use of SPaG.
    ''',
    epilog='''
    For more information on SPaG, it capabilities, limitation, and more, as well
    as numerous input file examples for scanners and parsers see the README.md
    and examples/ directory located in the github repository here:
    https://github.com/rrozansk/SPaG
    '''
)

CLI.add_argument('-e', '--encoding', type=str, default='direct',
                 choices=('table', 'direct'),
                 help='encoding to use for the generated output')
CLI.add_argument('-f', '--force', action='store_true',
                 help='overwrite output file(s) if already present')
CLI.add_argument('-g', '--generate', type=str, nargs='+', default=[],
                 choices=languages, required=True,
                 action=DynamicGeneratorImport,
                 help='target language(s) for code generation')
CLI.add_argument('-o', '--output', action='store', type=str, default='out',
                 help='base filename to use for generated output')
CLI.add_argument('-p', '--parser', type=open, action=CollectSpecification,
                 help='file containing parser name and LL(1) BNF grammar')
CLI.add_argument('-s', '--scanner', type=open, action=CollectSpecification,
                 help='file containing scanner name and type/token pairs')
CLI.add_argument('-t', '--time', action='store_true',
                 help='display the wall time taken for each component')
CLI.add_argument('-v', '--verbose', action='store_true',
                 help='output more information when running')
CLI.add_argument('-V', '--version', action='version',
                 version='Lexer/Parser Generator v1.0.0a0',
                 help='show version information and exit')

try:
    ARGS = vars(CLI.parse_args())
    START, END = None, None

    SCANNER = None
    if ARGS['scanner'] is not None:
        if ARGS['verbose']:
            stdout.write('Compiling scanner specification...')
            stdout.flush()
        START = time()
        SCANNER = RegularGrammar(ARGS['scanner']['name'],
                                 dict(ARGS['scanner']['rules']))
        END = time()
        if ARGS['verbose']:
            stdout.write('done\n')
            stdout.flush()
        if ARGS['time']:
            stdout.write('Elapsed time (scanner): {0}\n'.format(END-START))
            stdout.flush()

    PARSER = None
    if ARGS['parser'] is not None:
        if ARGS['verbose']:
            stdout.write('Compiling parser specification...')
            stdout.flush()
        START = time()
        PARSER = ContextFreeGrammar(ARGS['parser']['name'],
                                    dict(ARGS['parser']['rules']),
                                    ARGS['parser']['rules'][0][0])
        END = time()
        if ARGS['verbose']:
            stdout.write('done\n')
            stdout.flush()
        if ARGS['time']:
            stdout.write('Elapsed time (parser): {0}\n'.format(END-START))
            stdout.flush()


    OPTIONS = {
        'filename': ARGS['output'],
        'encoding': ARGS['encoding'],
        'scanner': True if ARGS['scanner'] else False,
        'parser': True if ARGS['parser'] else False
    }
    for GENERATOR in ARGS['generate']:
        GENERATOR = GENERATOR(SCANNER, PARSER)
        if ARGS['verbose']:
            stdout.write('Generating {0} code...'.format(type(GENERATOR)))
            stdout.flush()
        START = time()
        FILES = GENERATOR.output(OPTIONS)
        END = time()
        if ARGS['verbose']:
            stdout.write('done\n')
            stdout.flush()
        if ARGS['time']:
            stdout.write('Elapsed time (generator: {0}): {1}\n'.format(type(GENERATOR),
                                                                       END-START))
            stdout.flush()

        for NAME, CONTENT in FILES.items():
            if isfile(NAME) and not ARGS['force']:
                if ARGS['verbose']:
                    stdout.write('{0} already exists; not overwriting.\n'.format(NAME))
                    stdout.flush()
                continue

            with open(NAME, 'w') as FILE:
                if ARGS['verbose']:
                    stdout.write('Outputting {0} to disk...\n'.format(FILE.name))
                    stdout.flush()
                FILE.write(CONTENT)
except TypeError as exception:
    stdout.write('Invalid input type: {0}\n'.format(exception))
except ValueError as exception:
    stdout.write('Invalid input value: {0}\n'.format(exception))
except Exception as exception:
    stdout.write('Unknown exception encountered: {0}\n'.format(exception))
finally:
    stdout.flush()
    exit(0)
