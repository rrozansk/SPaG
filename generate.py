"""
generate.py is a simple python file which attempts to generate a scanner and
parser for the information given below. The scanner accepts any number of
tokens as regular expressions with some type and the Parser accepts only LL1
languages. For more detailed information on data input, capabilities, and
limitation see the README or have a look at src/{scanner, parser}.py.
Given below is an example for an ini like configuration file language.
"""
import src.scanner as scanner
import src.parser as parser

# import generators
import src.generators.c.C as C
import src.generators.go as Go
import src.generators.python as Python

generators = {
  "c":      C.C,
  "go":     Go.Go,
  "python": Python.Python
}

# ********************************** SCANNER **********************************
S_NAME = "scan"

TOKENS = {
    "int":      "(-|\+)?(1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*",
    "float":    "(-|\+)?((1|2|3|4|5|6|7|8|9)(0|1|2|3|4|5|6|7|8|9)*)?\.(0|1|2|3|4|5|6|7|8|9)+",
    "bool":     "true|false",
    "char":     "'(a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|w|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|W|Z|0|1|2|3|4|5|6|7|8|9)'",
    "id":       "(a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|w|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|W|Z)*",
    # "string":   "\"\_*\"",
    "space":    "( |\t|\n|\r|\f|\v)*",
    # "comment":  "(#|;)\_*\n",
    "lbracket": "[",
    "rbracket": "]",
    "lcurly":   "{",
    "rcurly":   "}",
    "comma":    ",",
    "dividor":  ":|="
}

SCANNER = scanner.RegularGrammar(S_NAME, TOKENS)

# ********************************** PARSER ***********************************
P_NAME = "parse"

PRODUCTIONS = {
    "<Ini>":       "<Section> <Ini'>",
    "<Ini'>":      "<Section> <Ini'> |",
    "<Section>":   "<Header> <Settings>",
    "<Header>":    "lbracket id rbracket",
    "<Settings>":  "<Setting> <Settings'>",
    "<Settings'>": "<Setting> <Settings'> |",
    "<Setting>":   "id dividor <Value>",
    "<Value>":     "int | float | bool | char | string | lcurly <Array> rcurly",
    "<Array>":     "<Ints> | <Floats> | <Bools> | <Chars> | <Strings>",
    "<Ints>":      "int <Ints'>",
    "<Ints'>":     "comma int <Ints'>|",
    "<Floats>":    "float <Floats'>",
    "<Floats'>":   "comma float <Floats'>|",
    "<Bools>":     "bool <Bools'>",
    "<Bools'>":    "comma bool <Bools'>|",
    "<Chars>":     "char <Chars'>",
    "<Chars'>":    "comma char <Chars'>|",
    "<Strings>":   "string <Strings'>",
    "<Strings'>":  "comma string <Strings'>|"
}

START_PRODUCTION = "<Ini>"

PARSER = parser.ContextFreeGrammar(P_NAME, PRODUCTIONS, START_PRODUCTION)

# ********************************* GENERATOR *********************************
TARGET = "c"

GENERATOR = generators[TARGET]()

GENERATOR.set_scanner(SCANNER)
GENERATOR.set_parser(PARSER)

FILENAME = "example"

GENERATOR.output(FILENAME)
