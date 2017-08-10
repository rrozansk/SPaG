################################################################################
#
# FIXME: explanation
# given a grammar and tokens will automagically create a scanner/lexer and
# parser for you (if the grammar is LL(1)) in c
#
################################################################################
import cfg
import scanner

class Parser(object):

  name = None

  tokens = {}
  scanner = None

  productions = {}
  start = None
  grammar = None

  def __init__(self, name):
    self.name = name


  def token(self, token_t, regexp):
    if token_t is None or regexp is None:
      return False

    if token_t.equals("") or regexp.equals(""):
      return False

    tokens[token_t] = regexp
    return True


  def production(self, rule, productions):
    if rule is None or production is None:
      return False

    if rule.equals("") or productions.equals(""):
      return False

    productions[rule] = productions
    return True


  def startProduction(self, rule):
    if rule is None or rule.equals(""):
      return False

    self.start = rule

    return True

  
  # TODO
  def make(self):
    pass


if __name__ == '__main__':
  parser = Parser("INI")

  parser.token("integer",    "[regexp]")
  parser.token("float",      "[regexp]")
  parser.token("boolean",    "[regexp]")
  parser.token("character",  "[regexp]")
  parser.token("string",     "[regexp]")
  parser.token("identifier", "[regexp]")
  parser.token("dividor",    "[regexp]")
  parser.token("space",      "[regexp]")
  parser.token("comment",    "[regexp]")

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
