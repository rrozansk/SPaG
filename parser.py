################################################################################
#
# FIXME: explanation
# given a grammar and tokens will automagically create a scanner/lexer and
# parser for you (if the grammar is LL(1)) in c
#
################################################################################
import grammar
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
    self.scanner = scanner.Scanner()

    for (token, regexp) in self.tokens:
      if not self.scanner.token(token, regexp):
        return False # failure

    self.dfa_graph = scanner.make()

    self.grammar = grammar.ContextFreeGrammar()

    for (rule, productions) in self.productions:
      self.grammer.ProductionRule(rule, productions)

    self.StartSymbol(self.start)

    self.grammar_dict = self.grammar.make()

    return True


if __name__ == '__main__':
  parser = Parser("INI")

  # common language tokens

  # FIXME: pay attention to the return values and act appropriately
  parser.token("integer",    "[1-9][0-9]*")
  parser.token("float",      "[-+]?[0-9]*\.[0-9]+")
  parser.token("boolean",    "true|false")
  parser.token("character",  "'[a-zA-Z0-9]'")
  parser.token("string",     "\".*\"")
  parser.token("space",      "\s")
  parser.token("comment",    "(#|;).*\n")

  # FIXME: different productions here for testing
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

  parser = parser.make() # return combined dictionary from scanner/cfg??
  # FIXME: whats the point of this class then? abstrating over two other classes and
  # error handling! also this means the generator just creates a parser and if
  # successful can just output code in a given language

  # TODO: tests here
