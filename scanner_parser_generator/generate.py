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

    from scanner_parser_generator.scanner import RegularGrammar
    from scanner_parser_generator.parser import ContextFreeGrammar
    from scanner_parser_generator.generators import __all__ as languages

    CLI = ArgumentParser(description='''
    Simple CLI (Command Line Interface) program to generate lexer(s) and/or
    parser(s) for a given input specification. For information on data input,
    capabilities, limitation and more see the README or have a look at
    scanner_parser_generator/{scanner, parser}.py located here:
    https://github.com/rrozansk/Scanner-Parser-Generator
    ''')

    CLI.add_argument('-v', '--version', action='version',
                     version='Lexer/Parser Generator v1.0',
                     help='version information')
    CLI.add_argument('-s', '--scanner', action='store', type=open,
                     help='file containing scanner name and type/token pairs')
    CLI.add_argument('-p', '--parser', action='store', type=open,
                     help='file containing parser name and LL(1) BNF grammar')
    CLI.add_argument('-o', '--output', action='store', required=True, type=str,
                     choices=languages,
                     help='code generation target language')
    CLI.add_argument('-f', '--filename', action='store', required=True, type=str,
                     help='base filename to use for generated output')

    ARGS = vars(CLI.parse_args())

    LANGUAGE = ARGS['output']

    GENERATOR = getattr(import_module('scanner_parser_generator.generators.' + LANGUAGE),
                        LANGUAGE.capitalize(),
                        None)
    if GENERATOR is None:
        raise ValueError('Error: Expected generator not found: ', LANGUAGE)

    SCANNER = None

    if ARGS['scanner'] is not None:
        try:
            NAME, TOKENS = collect_specification(ARGS['scanner'])
            SCANNER = RegularGrammar(NAME, TOKENS)
        except ValueError as exception:
            print('Scanner creation failed\n', exception)

    PARSER = None

    if ARGS['parser'] is not None:
        try:
            NAME, PRODUCTIONS = collect_specification(ARGS['parser'])
            START = PRODUCTIONS[0]
            PARSER = ContextFreeGrammar(NAME, dict(PRODUCTIONS), START)
        except ValueError as exception:
            print('Parser creation failed\n', exception)

    if PARSER is None and SCANNER is None:
        raise ValueError('Error: Must provide atleast a scanner or a parser')

    GENERATOR = GENERATOR(scanner=SCANNER, parser=PARSER)
    GENERATOR.output(ARGS['filename'])
