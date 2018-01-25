"""
A python CLI program to drive the scanner/parser generation.
"""
import src.scanner as scanner
import src.parser as parser

import src.generators.c as C
import src.generators.go as Go
import src.generators.python as Python

import argparse

GENERATORS = {
  "c":      C.C,
  "go":     Go.Go,
  "python": Python.Python
}

CLI = argparse.ArgumentParser(description='simple cli (command line interface)\
                                           program to generate lexer(s) and/or\
                                           parser(s) for a given output\
                                           language')

CLI.add_argument('-v', '--version', action='version',
                 version='Lexer/Parser Generator v1.0',
                 help='version information')
CLI.add_argument('-s', '--scanner', action='store', type=file,
                 help='file containing scanner name and type/token pairs')
CLI.add_argument('-p', '--parser', action='store', type=file,
                 help='file containing parser name and LL(1) BNF grammar')
CLI.add_argument('-o', '--output', action='store', required=True, type=str,
                 choices=GENERATORS.keys(),
                 help='code generation target language')
CLI.add_argument('-f', '--filename', action='store', required=True, type=str,
                 help='base filename (w/o extns) to use for generated output')

ARGS = vars(CLI.parse_args())

GENERATOR = GENERATORS[ARGS['output']]()

if ARGS['scanner'] is not None:
    NAME = None
    TOKENS = {}
    for line in ARGS['scanner']:
        items = line.split(None, 1)
        if len(items) == 0:
            continue

        if NAME is None:
            if len(items) != 1:
                raise ValueError('Error: Invalid file format - scanner name')
            NAME = items[0]
            continue

        if len(items) != 2:
            raise ValueError('Error: Invalid file format - scanner token')

        TOKENS[items[0]] = items[1].rstrip()
    try:
        SCANNER = scanner.RegularGrammar(NAME, TOKENS)
        GENERATOR.set_scanner(SCANNER)
    except ValueError as e:
        print 'Scanner creation failed\n', e

if ARGS['parser'] is not None:
    NAME = None
    START = None
    PRODUCTIONS = {}
    for line in ARGS['parser']:
        items = line.split(None, 1)
        if len(items) == 0:
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
        print 'Parser creation failed\n', e

GENERATOR.output(ARGS['filename'])
