"""
A python CLI program to drive the scanner/parser generation.

for help/information about [in/out]put run the following at the command line:

 $ python generate.py --help
"""
from argparse import ArgumentParser
from importlib import import_module

import src.scanner as scanner
import src.parser as parser
import src.generators

CLI = ArgumentParser(description='''
Simple CLI (Command Line Interface) program to generate lexer(s) and/or
parser(s) for a given input specification. For information on data input,
capabilities, limitation and more see the README or have a look at
src/{scanner, parser}.py.
''')

CLI.add_argument('-v', '--version', action='version',
                 version='Lexer/Parser Generator v1.0',
                 help='version information')
CLI.add_argument('-s', '--scanner', action='store', type=open,
                 help='file containing scanner name and type/token pairs')
CLI.add_argument('-p', '--parser', action='store', type=open,
                 help='file containing parser name and LL(1) BNF grammar')
CLI.add_argument('-o', '--output', action='store', required=True, type=str,
                 choices=src.generators.__all__,
                 help='code generation target language')
CLI.add_argument('-f', '--filename', action='store', required=True, type=str,
                 help='base filename to use for generated output')

ARGS = vars(CLI.parse_args())

OUT = ARGS['output']

GENERATOR = getattr(import_module('src.generators.' + OUT), OUT.capitalize(), None)
if not GENERATOR:
    raise ValueError('Error: Expected generator not found: ', OUT)

GENERATOR = GENERATOR()

if ARGS['scanner'] is not None:
    NAME = None
    TOKENS = []
    for line in ARGS['scanner']:
        items = line.split(None, 1)
        if not items:
            continue

        if NAME is None:
            if len(items) != 1:
                raise ValueError('Error: Invalid file format - scanner name')
            NAME = items[0]
            continue

        if len(items) != 2:
            raise ValueError('Error: Invalid file format - scanner token')

        TOKENS.append((items[0], items[1].rstrip()))
    try:
        SCANNER = scanner.RegularGrammar(NAME, TOKENS)
        GENERATOR.set_scanner(SCANNER)
    except ValueError as e:
        print('Scanner creation failed\n', e)

if ARGS['parser'] is not None:
    NAME = None
    START = None
    PRODUCTIONS = {}
    for line in ARGS['parser']:
        items = line.split(None, 1)
        if not items:
            continue

        if NAME is None:
            if len(items) != 1:
                raise ValueError('Error: Invalid file format - parser name')
            NAME = items[0]
            continue

        if START is None:
            if len(items) != 1:
                raise ValueError('Error: Invalid file format - parser start')
            START = items[0]
            continue

        if len(items) != 2:
            raise ValueError('Error: Invalid file format - parser production')

        PRODUCTIONS[items[0]] = items[1].rstrip()
    try:
        PARSER = parser.ContextFreeGrammar(NAME, PRODUCTIONS, START)
        GENERATOR.set_parser(PARSER)
    except ValueError as e:
        print('Parser creation failed\n', e)

if not GENERATOR.get_parser() and not GENERATOR.get_scanner():
    raise ValueError('Error: Must provide atleast a scanner or a parser')

GENERATOR.output(ARGS['filename'])
