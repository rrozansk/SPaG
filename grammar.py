################################################################################
#
# FIXME: explanation
#
################################################################################
import copy

class ContextFreeGrammar(object):

  Dollar = 0
  Epsilon = 1

  Terminals = None     # set of grammar terminals
  Nonterminals = None  # set of grammar nonterminals
  ParseTable = None    # the parse table generated
  LL1 = None           # boolean to indicate if grammar is LL(1)
  First = None         # dictionary ::= [non]terminal -> first set
  Follow = None        # dictionary ::= terminal -> follow set
  Start = None         # which grammar rule is the start symbol of grammar
  Productions = []     # all the production rules in the grammar


  def StartSymbol(self, start):
    self.Start = start


  # rule -> (rule #, [[seq of symbols for a production] ...the rest of the productions])
  # empty list [] specifies an epsilon production.
  def ProductionRule(self, lhs, rhs):
    self.Productions.append((lhs , [productions.split() for productions in rhs.split('|')]))


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


  # all literal symbols which appear in the grammar
  def __terminals__(self):
    self.Terminals = set()
    lhs = {key for (key, _) in self.Productions}
    for (_, v) in self.Productions:
      for production in v:
        for symbol in production:
          if symbol not in lhs:
            self.Terminals.add(symbol)


  # all non terminals are just the production rules
  def __nonterminals__(self):
    self.Nonterminals = {_tuple[0] for _tuple in self.Productions}


  # calculate the first set following the algorithm set forth here:
  # http://www.jambe.co.nz/UNI/FirstAndFollowSets.html
  def __first__(self):
    self.First = {}

    # 1. If X is a terminal then First(X) is just X!
    for terminal in self.Terminals:
      self.First[terminal] = set([terminal])

    # --init first sets for nonterminals--
    for nonterminal in self.Nonterminals:
      self.First[nonterminal] = set()

    # 2. If there is a Production X -> epsilon then add epsilon to first(X)
    for (X, productions) in self.Productions:
      for production in productions:
        if len(production) == 0:
          self.First[X].add(self.Epsilon)

    # 4. First(Y1Y2..Yk) is either:
    #   a. First(Y1) (if First(Y1) doesn't contain epsilon)
    #   b. OR (if First(Y1) does contain epsilon) then everything in First(Y1) <except for epsilon> as well as everything in First(Y2..Yk)
    #   c. If First(Y1) First(Y2)..First(Yk) all contain epsilon then add epsilon to First(Y1Y2..Yk) as well
    def first(Ys):
      if len(Ys) == 0: # from recursive call
        return set()
      elif self.Epsilon not in self.First[Ys[0]]:
        return self.First[Ys[0]]
      elif self.Epsilon in self.First[Ys[0]]:
        s = ((self.First[Ys[0]] - set([self.Epsilon])) | first(Ys[1:]))
        for Y in Ys:
          if self.Epsilon not in self.First[Y]:
            return s
        return s | set([self.Epsilon])

    # 3. If there is a Production X -> Y1Y2..Yk then add first(Y1Y2..Yk) to first(X)
    def find():
      for (X, productions) in self.Productions:
        for Ys in productions:
          if len(Ys) != 0: # we already took care of epsilon productions
            self.First[X].update(first(Ys))

    # --need to repeat until the sets are no longer changing--
    while True:
      c = copy.deepcopy(self.First)
      find()
      changed = False
      for k in self.First:
        if self.First[k] != c[k]:
          changed = True
          break

      if not changed:
        return


  # calculate the follow set following the algorithm set forth here:
  # http://www.jambe.co.nz/UNI/FirstAndFollowSets.html
  def __follow__(self):
    self.Follow = {}

    # --init follow sets for nonterminals--
    for nonterminal in self.Nonterminals:
      self.Follow[nonterminal] = set()

    # 1. First put $ (the end of input marker) in Follow(S) (S is the start symbol)
    self.Follow[self.Start].add(self.Dollar)

    def  follow(A, Ys):
      for k in range(0, len(Ys)):
        B = Ys[k]
        if B in self.Nonterminals and k > 0: # find first nonterminal after terminal, or 2nd nonterminal
          # 3. If there is a production A -> aB, then everything in FOLLOW(A) is in FOLLOW(B)
          if k == len(Ys)-1:
            self.Follow[B].update(self.Follow[A])
          else:
            # 2. If there is a production A -> aBb, (where a can be a whole string) then everything in FIRST(b) except for epsilon is placed in FOLLOW(B).
            b = Ys[k+1]
            self.Follow[B].update(self.First[b] - set([self.Epsilon]))
            # 4. If there is a production A -> aBb, where FIRST(b) contains epsilon, then everything in FOLLOW(A) is in FOLLOW(B)
            if self.Epsilon in self.First[b]:
              self.Follow[B].update(self.Follow[A])
          return

    def find():
      for (X, productions) in self.Productions:
        for Ys in productions:
          if len(Ys) > 0: # ignore epsilon production
            follow(X, Ys)

    # --need to repeat until the sets are no longer changing--
    while True:
      c = copy.deepcopy(self.Follow)
      find()
      changed = False
      for k in self.Follow:
        if self.Follow[k] != c[k]:
          changed = True
          break

      if not changed:
        return

  # grammar is ll(1) if parse table has (@maximum) a single entry per table slot
  # conflicting for the predicitions
  def __parseTable__(self):
    # flatten rules so they can be enumerated
    productions = []
    for (X, _productions) in self.Productions:
      for production in _productions:
        if len(production) != 0:                   # FIXME: printing production below is off because of this...should i be ignoring these??
          productions.append((X, production))

    # Predict(A --> X1...Xm) = First(X1...Xm) U 
    #   If X1...Xm --> epsilon then Follow(A) else null
    def predict(X, Ys):
      if len(Ys) == 0: # from recursive call
        return set()
      elif self.Epsilon not in self.First[Ys[0]]:
        return self.First[Ys[0]]
      elif self.Epsilon in self.First[Ys[0]]:
        s = ((self.First[Ys[0]] - set([self.Epsilon])) | predict(X, Ys[1:]))
        for Y in Ys:
          if self.Epsilon not in self.First[Y]:
            return s
        return s | self.Follow[X]

    predictions = []
    for (X, production) in productions:
      if len(production) != 0:
        predictions.append(predict(X, production))
   
    terminals = [t for t in (self.Terminals | set([self.Dollar]))]
    nonterminals = [n for n in self.Nonterminals]
    self.ParseTable = [[set() for column in terminals] for row in nonterminals]

    for k in range(0, len(predictions)):
      (Nonterminal, _) = productions[k]
      n = 0
      for _n in nonterminals:
        if _n == Nonterminal:
          break
        n += 1

      Terminals = predictions[k]
      for Terminal in Terminals:
        t = 0
        for _t in terminals:
          if _t == Terminal:
            break
          t += 1

        self.ParseTable[n][t].add(k)

    # check grammar is LL1
    self.LL1 = True
    done = False
    for r in self.ParseTable:
      for c in r:
        if len(c) > 1:
          self.LL1 = False
          done = True
        if done: break
      if done: break

    # put row labels
    for r in range(0, len(self.ParseTable)):
      self.ParseTable[r].insert(0, nonterminals[r])

    # put column labels
    col_lbls = [' ']
    col_lbls.extend(terminals)
    self.ParseTable.insert(0, col_lbls)


  # find the [non]terminals, first and follow sets, and construct the parse
  # table to figure out if the grammar is LL(1)
  def Analyze(self, doPrint):
    self.__terminals__()
    self.__nonterminals__()
    self.__first__()
    self.__follow__()
    self.__parseTable__()

    if not doPrint:
      return

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


if __name__ == "__main__":
# test grammar @http://www.jambe.co.nz/UNI/FirstAndFollowSets.html
  test = ContextFreeGrammar()

  test.ProductionRule('<E>',   '<T> <E\'>')
  test.ProductionRule('<E\'>', '+ <T> <E\'> |')
  test.ProductionRule('<T>',   '<F> <T\'>')
  test.ProductionRule('<T\'>', '* <F> <T\'> |')
  test.ProductionRule('<F>',   '( <E> )')
  test.ProductionRule('<F>',   'id')

  test.StartSymbol('<E>')

  test.PrintBNF()

  test.Analyze(True) # FIXME: change to make, erase printing and return a dictionary with the sets and parse tbl??

  print "\t\t**EXPECTED RESULTS**\n"
  print "FIRST(E)   = {(, id}"
  print "FIRST(E')  = {+, epsilon}"
  print "FIRST(T)   = {(, id}"
  print "FIRST(T')  = {*, epsilon}"
  print "FIRST(F)   = {(, id}\n"
  print "FOLLOW(E)  = {$, )}"
  print "FOLLOW(E') = {$, )}"
  print "FOLLOW(T)  = {+, $, )}"
  print "FOLLOW(T') = {+, $, )}"
  print "FOLLOW(F)  = {*, +, $, )}"
