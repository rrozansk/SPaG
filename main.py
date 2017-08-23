#!/usr/bin/python

################################################################################
# main.py is a simple python script which attempts to generate a scanner, parser
# and language analysis info ([non]terminals, first/follow/predict sets, etc.).
# The only thing required from the user is that they change the tokenizer and
# LL1 grammar to what they desire. It is important to note that only LL1 parsers
# are generated. This means for a parser to be generated the grammar is required
# to be left factored and have no left recursion. If there are any conflicts
# however, they will be reported. So, in that reguard it is possible to specify
# any grammar desired. As for the tokens, they all must be specified as regular
# expressions (the formal kind). Currently only generation to c code is possible
# but this is easily extendible in the future by adding other 'generators'
# inside the generator object. Also note that the string given to the object at
# instantiation will become the name of the function in the corresponding
# generated code and it will be written out in the specified file mentioned
# below. If you choose to have the language analysis done it will be written out
# in the comments of the file. The current example below is a ini like
# configuration file which recognizes basic data types. 
#
# TODO: continue, and explain more about what is generated and it
# efficientcy/runtime analysis and other important information like the AST
# produced and what constitues a token (line/char #, type, data), etc.
# ...likewise if invalid regular expressions are given they will not be
# recognized in the generated scanner.
################################################################################
import src.parser as parser
import src.scanner as scanner
import src.generator as generator

################################### SCANNER ####################################
tokenizer = scanner.RegularGrammar("ScanINI")

tokenizer.token("int",     True, "(-|+)?[1-9][0-9]*")
tokenizer.token("float",   True, "(-|+)?([1-9][0-9]*)?\.[0-9]+")
tokenizer.token("bool",    True, "true|false")
tokenizer.token("char",    True, "'([a-z]|[A-Z]|[0-9])'") # FIXME: specials, metas?
tokenizer.token("id",      True, "[a-z]|[A-Z]*") # FIXME: must have alphas
tokenizer.token("string",  True, "\".*\"") # FIXME: escapes?
tokenizer.token("space",   False, "\s|\t|\n|\r|\f|\v")
tokenizer.token("comment", False, "(#|;).*\n")

scanner = tokenizer.make()

################################### PARSER #####################################
LL1 = parser.ContextFreeGrammar("ParseINI")

LL1.production('<Ini>',        '<Section> <Ini\'>')
LL1.production('<Ini\'>',      '<Section> <Ini\'> |')
LL1.production('<Section>',    '<Header> <Settings>')
LL1.production('<Header>',     '[ id ]')
LL1.production('<Settings>',   '<Setting> <Settings\'>')
LL1.production('<Settings\'>', '<Setting> <Settings\'> |')
LL1.production('<Setting>',    'identifier dividor <Value>')
LL1.production('<Value>',      'int | float | bool | char | string | { <Array> }')
LL1.production('<Array>',      '<Ints> | <Floats> | <Bools> | <Chars> | <Strings>')
LL1.production('<Ints>',       'int <Ints\'>')
LL1.production('<Ints\'>',     ', int <Ints\'>|')
LL1.production('<Floats>',     'float <Floats\'>')
LL1.production('<Floats\'>',   ', float <Floats\'>|')
LL1.production('<Bools>',      'bool <Bools\'>')
LL1.production('<Bools\'>',    ', bool <Bools\'>|')
LL1.production('<Chars>',      'char <Chars\'>')
LL1.production('<Chars\'>',    ', char <Chars\'>|')
LL1.production('<Strings>',    'string <Strings\'>')
LL1.production('<Strings\'>',  ', string <Strings\'>|')

LL1.start('<Ini>')

parser = LL1.make()

################################## GENERATOR ###################################
generator = generator.Generator(parser, scanner)

what = generator.PARSER|generator.SCANNER|generator.ANALYSIS
language = generator.C

program = generator.output(what, language)

filename = "ini.c"

f = open(filename, "w")
f.write(program)
f.close()
