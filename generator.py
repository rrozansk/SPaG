################################################################################
# The generator is responsible for all I/O output including code generation.
# Currently only c code is generated. Code can be generated individually for the
# lexer and the parser, but they can also be combined into a single program if
# desired.
################################################################################
import parser
import scanner

class Generator(object):

  # What to output/generate
  SCANNER = 1
  PARSER = 2
  ANALYSIS = 4

  # The language to generate
  C = 0

  # parser Objects to generate code for
  parser = {
   "rules":         None,
   "terminals":     None,
   "nonterminals":  None,
   "first":         None,
   "follow":        None,
   "table":         None,
   "parsable?":     None,
   "conflicts":     None,
  }
  scanner = None # a graph representing an FSM
  fielname = None

  def __init__(self, parser, scanner):
    self.parser = parser
    self.scanner = scanner


  def __gen_c__(self, what):
    program = ""

    return program


  def output(self, what, language):
    if language == self.C: return __gen_c(what)
    # other language generators...
    else: return "INVALID LANGUAGE SELECTED FOR GENERATION"


  def PrintBNF(self):
    _max = max([len(_tuple[0]) for _tuple in self.Productions])
    print ' ' * 32, "::BNF GRAMMMAR::", ' ' * 32
    for _tuple in self.Productions:
      print '\t%-*s ::= ' % (_max, _tuple[0]),
      first = True
      for rhs in _tuple[1]:
        if not first:
          print ' | ',
        if len(rhs) == 0:
          print 'epsilon',
        else:
          print ' '.join(rhs),
        first = False
      print
    print


  def Analyze(self): # FIXME: var names not self.
    self.__terminals__()
    self.__nonterminals__()
    self.__first__()
    self.__follow__()
    self.__parseTable__()

    print "Terminals Set: ", self.Terminals, '\n'

    print "Nonterminals Set: ", self.Nonterminals, '\n'

    print "First Set: {"
    for k in self.First:
      if k in self.Nonterminals:
        print '\t', k, '\t->\t', self.First[k]
    print '}\n'

    print "Follow Set: {"
    for k in self.Follow:
      if k in self.Nonterminals:
        print '\t', k, '\t->\t', self.Follow[k]
    print '}\n'
    
    _max = max([len(_tuple[0]) for _tuple in self.Productions])
    print ' ' * 26, "::BNF GRAMMMAR PRODUCTIONS::", ' ' * 26
    k = 0
    for (rule, productions) in self.Productions:
      for production in productions:
        if len(production) == 0: # FIXME: ignoring epsilon production like above for now
          #print 'epsilon'
          continue
        print '%i)\t%-*s ::= ' % (k, _max, rule),
        k += 1
        print ' '.join(production)
    print

    print "LL(1) Parsable: ", self.LL1, '\n'

    if not self.LL1:
      print "Conflicts: {"
      for r in range(1, len(self.ParseTable)):
        for c in range(1, len(self.ParseTable[0])):
          if len(self.ParseTable[r][c]) > 1:
            print '\tT[\'%s\'][\'%s\'] = ' % (self.ParseTable[r][0], self.ParseTable[0][c]), self.ParseTable[r][c]
      print '}\n'

    print "Parse Table: {"
    for r in self.ParseTable:
      print '\t[',
      for c in r:
        print c, '\t',
      print ']'
    print '}\n'


if __name__ == '__main__':
  import parser
  import scanner

  ################################## SCANNER ###################################
  scanner = scanner.RegularGrammar("Test Scanner")

  scanner.token("integer",    "[1-9][0-9]*")
  scanner.token("float",      "[-+]?[0-9]*\.[0-9]+")
  scanner.token("boolean",    "true|false")
  scanner.token("character",  "'[a-zA-Z0-9]'")
  scanner.token("string",     "\".*\"")
  scanner.token("space",      "\s")
  scanner.token("comment",    "(#|;).*\n")

  tokenizer = scanner.make()

  ################################## PARSER ####################################
  parser = parser.ContextFreeGrammar()

  parser.ProductionRule('<E>',   '<T> <E\'>')
  parser.ProductionRule('<E\'>', '+ <T> <E\'> |')
  parser.ProductionRule('<T>',   '<F> <T\'>')
  parser.ProductionRule('<T\'>', '* <F> <T\'> |')
  parser.ProductionRule('<F>',   '( <E> )')
  parser.ProductionRule('<F>',   'id')

  parser.StartSymbol('<E>')

  LL1 = parser.make()

  ################################# GENERATOR ##################################
  generator = Generator(parser, scanner)

  what = generator.PARSER|generator.SCANNER|generator.ANALYSIS
  language = generator.C
  filename = "foo.c"

  program = generator.output(what, language, filename)

  print program
