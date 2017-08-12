#!/bin/python

################################################################################
#
# FIXME: explanation
# main.py reads in the grammar from a file and constructs the lexer/parser
# possibly outputting only one or the other or both out to a file in the given
# language main just deals with read IO from the users grammar/spec and the
# generation deals with all output IO.
#
################################################################################
import parser
import scanner
import generator

################################### SCANNER ####################################
scanner = scanner.RegularGrammar("ScanINI")

scanner.token("integer",    "[1-9][0-9]*")
scanner.token("float",      "[-+]?[0-9]*\.[0-9]+")
scanner.token("boolean",    "true|false")
scanner.token("character",  "'[a-zA-Z0-9]'")
scanner.token("string",     "\".*\"")
scanner.token("space",      "\s")
scanner.token("comment",    "(#|;).*\n")

tokenizer = scanner.make()

################################### PARSER #####################################
parser = parser.ContextFreeGrammar("ParseINI")

parser.production('<Ini>',        '<Section> <Ini\'>')
parser.production('<Ini\'>',      '<Section> <Ini\'> |')
parser.production('<Section>',    '<Header> <Settings>')
parser.production('<Header>',     '[ identifier ]')
parser.production('<Settings>',   '<Setting> <Settings\'>')
parser.production('<Settings\'>', '<Setting> <Settings\'> |')
parser.production('<Setting>',    'identifier dividor <Value>')
parser.production('<Value>',      'int | float | bool | char | string | { <Array> }')
parser.production('<Array>',      '<Ints> | <Floats> | <Bools> | <Chars> | <Strings>')
parser.production('<Ints>',       'int <Ints\'>')
parser.production('<Ints\'>',     ', int <Ints\'>|')
parser.production('<Floats>',     'float <Floats\'>')
parser.production('<Floats\'>',   ', float <Floats\'>|')
parser.production('<Bools>',      'bool <Bools\'>')
parser.production('<Bools\'>',    ', bool <Bools\'>|')
parser.production('<Chars>',      'char <Chars\'>')
parser.production('<Chars\'>',    ', char <Chars\'>|')
parser.production('<Strings>',    'string <Strings\'>')
parser.production('<Strings\'>',  ', string <Strings\'>|')

parser.startProduction('<Ini>')

LL1 = parser.make()

################################## GENERATOR ###################################
generator = Generator(LL1, scanner)

what = generator.PARSER|generator.SCANNER|generator.ANALYSIS
language = generator.C

program = generator.output(what, language)

print program # fwrite(program, "ini.c")
