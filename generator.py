################################################################################
#
# FIXME: explanation
# the generator is the abstration that output the code
#
################################################################################
import parser

class Generator(object):

  parser = None

  def __init__(self, parser):
    self.parser = parser

  # TODO: code generation for given languages
  def output(self, language):
    pass

if __name__ == '__main__':
  import parser

  parser.token("integer",    "[1-9][0-9]*")
  parser.token("float",      "[-+]?[0-9]*\.[0-9]+")
  parser.token("boolean",    "true|false")
  parser.token("character",  "'[a-zA-Z0-9]'")
  parser.token("string",     "\".*\"")
  parser.token("space",      "\s")
  parser.token("comment",    "(#|;).*\n")

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

  parser = parser.make()

  generator = Generator(parser)

  generator.output("c")
