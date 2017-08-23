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

  parser = None # parser obj to generate code for
  scanner = None # scanner obj to generate code for


  def __init__(self, parser, scanner):
    self.parser = parser
    self.scanner = scanner


  def __gen_c__(self, what):
    comments = ""
    if what & 4 == 1: comments = __analyze__()

    program = ""

    return comments + program


  def output(self, what, language):
    if language == self.C: return self.__gen_c__(what)
    # other language generators...
    else: return "INVALID LANGUAGE SELECTED FOR GENERATION"


  def __analyze__(self):
    # TODO "rules":         rules,
    _max = max([len(_tuple[0]) for _tuple in self.parser['productions']])
    print ' ' * 26, "::BNF GRAMMMAR PRODUCTIONS::", ' ' * 26
    k = 0
    for (rule, productions) in self.parser['productions']:
      for production in productions:
        if len(production) == 0: # FIXME: ignoring epsilon production like above for now
          #print 'epsilon'
          continue
        print '%i)\t%-*s ::= ' % (k, _max, rule),
        k += 1
        print ' '.join(production)
    print

    # TODO "start":         self.Start,

    print "Terminals Set: ", self.parser['terminals'], '\n'

    print "Nonterminals Set: ", self.parser['nonterminals'], '\n'

    print "First Set: {"
    for k in self.parser['first']:
      if k in self.parser['nonterminals']:
        print '\t', k, '\t->\t', self.parser['first'][k]
    print '}\n'

    print "Follow Set: {"
    for k in self.parser['follow']:
      if k in self.parser['nonterminals']:
        print '\t', k, '\t->\t', self.parser['follow'][k]
    print '}\n'
    
    # TODO "predictions":   predictions,

    print "Parse Table: {"
    for r in self.parser['table']:
      print '\t[',
      for c in r:
        print c, '\t',
      print ']'
    print '}\n'

    print "LL(1) Parsable: ", self.parser['parsable?'], '\n'

    # FIXME: correct?
    if not self.parser['conflicts']:
      print "Conflicts: {"
      for r in range(1, len(self.ParseTable)):
        for c in range(1, len(self.ParseTable[0])):
          if len(self.ParseTable[r][c]) > 1:
            print '\tT[\'%s\'][\'%s\'] = ' % (self.ParseTable[r][0], self.ParseTable[0][c]),
            print self.ParseTable[r][c]
      print '}\n'
