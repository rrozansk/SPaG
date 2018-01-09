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
import src.generators.c as generator  # NOTE: import specific generator

# ******************************* SCANNER ********************************
SCANNER = scanner.RegularGrammar("scan")

SCANNER.token("int",      "(-|+)?[1-9][0-9]*")
SCANNER.token("float",    "(-|+)?([1-9][0-9]*)?\.[0-9]+")
SCANNER.token("bool",     "true|false")
SCANNER.token("char",     "'([a-z]|[A-Z]|[0-9])'")
SCANNER.token("id",       "([a-z]|[A-Z])*")
SCANNER.token("string",   "\".*\"")
SCANNER.token("space",    "(\s|\t|\n|\r|\f|\v)*")  # not in parser; discard
SCANNER.token("comment",  "(#|;).*\n")             # not in parser; discard
SCANNER.token("lbracket", "[")
SCANNER.token("rbracket", "]")
SCANNER.token("lcurly",   "{")
SCANNER.token("rcurly",   "}")
SCANNER.token("comma",    ",")
SCANNER.token("dividor",  ":|=")

# ******************************* PARSER *********************************
PARSER = parser.ContextFreeGrammar("parse")

PARSER.production("<Ini>",       "<Section> <Ini'>")
PARSER.production("<Ini'>",      "<Section> <Ini'> |")
PARSER.production("<Section>",   "<Header> <Settings>")
PARSER.production("<Header>",    "lbracket id rbracket")
PARSER.production("<Settings>",  "<Setting> <Settings'>")
PARSER.production("<Settings'>", "<Setting> <Settings'> |")
PARSER.production("<Setting>",   "id dividor <Value>")
PARSER.production("<Value>",     "int | float | bool | char | string | lcurly <Array> rcurly")
PARSER.production("<Array>",     "<Ints> | <Floats> | <Bools> | <Chars> | <Strings>")
PARSER.production("<Ints>",      "int <Ints'>")
PARSER.production("<Ints'>",     "comma int <Ints'>|")
PARSER.production("<Floats>",    "float <Floats'>")
PARSER.production("<Floats'>",   "comma float <Floats'>|")
PARSER.production("<Bools>",     "bool <Bools'>")
PARSER.production("<Bools'>",    "comma bool <Bools'>|")
PARSER.production("<Chars>",     "char <Chars'>")
PARSER.production("<Chars'>",    "comma char <Chars'>|")
PARSER.production("<Strings>",   "string <Strings'>")
PARSER.production("<Strings'>",  "comma string <Strings'>|")

PARSER.start("<Ini>")

# ****************************** GENERATOR *******************************
GENERATOR = generator.Generator()

GENERATOR.set_scanner(SCANNER)
GENERATOR.set_parser(PARSER)

FILENAME = "example"

GENERATOR.output(FILENAME)
