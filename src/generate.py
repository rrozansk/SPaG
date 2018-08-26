"""
A python CLI program to drive the scanner/parser generation.

for help/information about [in/out]put run the following at the command line:

  $ python -m scanner_parser_generator.generate --help
"""

def collect_specification(_file):
    """
    Collect the specification for a scanner and/or parser from a file.

    Input Type:
      _file: File

    Output Type: Tuple[String, List[Tuple[String, String]]] | raise ValueError
    """
    if not isinstance(_file, file):
        raise ValueError('Error: _file must be of type file')

    name, rules = None, []

    for line in _file:
        items = line.split(None, 1)
        if not items:
            continue

        if name is None:
            if len(items) != 1:
                raise ValueError('Error: Invalid file format - name')
            name = items[0]
            continue

        if len(items) != 2:
            raise ValueError('Error: Invalid file format - rule')

        rules.append((items[0], items[1].rstrip()))

    return name, rules


if __name__ == '__main__':
    from argparse import ArgumentParser
    from importlib import import_module
    from os.path import isfile
    from time import time

    from scanner.scanner import RegularGrammar
    from parser.parser import ContextFreeGrammar
    from generators import __all__ as languages

    CLI = ArgumentParser(
        description='''
        Simple CLI (Command Line Interface) program to generate lexer(s) and/or
        parser(s) for a given input specification. For information on data input,
        capabilities, limitation and more see the README or have a look at
        scanner_parser_generator/{scanner,parser}.py located here:
        https://github.com/rrozansk/Scanner-Parser-Generator
        '''
    )

    CLI.add_argument('-V', '--version', action='version',
                     version='Lexer/Parser Generator v0.0.17',
                     help='show version information and exit')
    CLI.add_argument('-f', '--force', action='store_true',
                     help='overwrite output file(s) if already present')
    CLI.add_argument('-g', '--generate', action='store', type=str,
                     required=True, choices=languages,
                     help='target language for code generation')
    CLI.add_argument('-o', '--output', action='store', type=str,
                     help='base filename to use for generated output')
    CLI.add_argument('-p', '--parser', action='store', type=open,
                     help='file containing parser name and LL(1) BNF grammar')
    CLI.add_argument('-s', '--scanner', action='store', type=open,
                     help='file containing scanner name and type/token pairs')
    CLI.add_argument('-t', '--time', action='store_true',
                     help='display the wall time taken for each component')
    CLI.add_argument('-v', '--verbose', action='store_true',
                     help='output more information when running')

    ARGS = vars(CLI.parse_args())

    LANGUAGE = ARGS['generate']

    GENERATOR = getattr(import_module('scanner_parser_generator.generators.' + LANGUAGE),
                        LANGUAGE.capitalize(),
                        None)
    if GENERATOR is None:
        print('Error: Expected generator not found: ', LANGUAGE)
        exit(0)

    START, END = None, None

    SCANNER = None

    if ARGS['scanner'] is not None:
        try:
            if ARGS['verbose']:
                print('Collecting scanner specification from file.')

            NAME, TOKENS = collect_specification(ARGS['scanner'])

            if ARGS['verbose']:
                print('Collected specification: {0}'.format(NAME))

            if ARGS['verbose']:
                print('Compiling specification...')

            if ARGS['time']:
                START = time()

            SCANNER = RegularGrammar(NAME, TOKENS)

            if ARGS['time']:
                END = time()

            if ARGS['verbose']:
                print('Finished building scanner')

            if ARGS['time']:
                print('Time elapsed (scanner): {0}'.format(END - START))
        except ValueError as exception:
            print('Scanner creation failed: {0}'.format(exception))
            exit(0)
        except Exception as exception:
            print('Unknown error encountered: {0}'.format(exception))
            exit(0)

    PARSER = None

    if ARGS['parser'] is not None:
        try:
            if ARGS['verbose']:
                print('Collecting parser specification from file.')

            NAME, PRODUCTIONS = collect_specification(ARGS['parser'])
            STARTING = PRODUCTIONS[0][0]

            if ARGS['verbose']:
                print('Collected parser specification: {0}'.format(NAME))

            if ARGS['time']:
                START = time()

            PARSER = ContextFreeGrammar(NAME, dict(PRODUCTIONS), STARTING)

            if ARGS['time']:
                END = time()

            if ARGS['verbose']:
                print('Finished building parser')

            if ARGS['time']:
                print('Time elapsed (parser): {0}'.format(END - START))
        except ValueError as exception:
            print('Parser creation failed: {0}'.format(exception))
            exit(0)
        except Exception as exception:
            print('Unknown error encountered: {0}'.format(exception))
            exit(0)

    if PARSER is None and SCANNER is None:
        print('Error: Must provide atleast a scanner or a parser')
        exit(0)

    try:
        if ARGS['verbose']:
            print('Translating compiled scanner and/or parser to: {0}'.format(LANGUAGE))

        GENERATOR = GENERATOR(scanner=SCANNER, parser=PARSER)

        if ARGS['time']:
            START = time()

        FILES = GENERATOR.output(ARGS['output'])

        if ARGS['time']:
            END = time()

        if ARGS['verbose']:
            print('Finished building output files.')

        if ARGS['time']:
            print('Time elapsed (generator): {0}'.format(END - START))

        if ARGS['verbose']:
            print('Outputting files to disk...')

        for _file, content in FILES:
            if isfile(_file) and not ARGS['force']:
                print('{0} already exists. Use --force (-f) to overwrite.'.format(_file))
                continue

            with open(_file, 'w') as fd:
                fd.write(content)

            if ARGS['verbose']:
                print(_file)
    except ValueError as exception:
        print('Generator program compilation failed: {0}'.format(exception))
        exit(0)
    except Exception as exception:
        print('Unknown error encountered: {0}'.format(exception))
        exit(0)
