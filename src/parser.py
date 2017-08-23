################################################################################
# ContextFreeGrammar represents a BNF grammar which can be programatically
# transformed into a LL1 parse table given the following requirements:
#   1. No left recursion
#   2. Must be left factored
# Although, it is possible for any grammar to be specified as all conflicts will
# be reported if any exist in the grammar.
#
# This object can be tested by directly calling it with python like:
#   $ python parser.py
# You should see the following output if everything went well: 
#   ALL PARSER TESTS PASSED!
# otherwise a value error is thrown with the appropriate error.
################################################################################

class ContextFreeGrammar(object):


  name = None

  Dollar = 0
  Epsilon = 1

  Start = None         # which grammar rule is the start symbol of grammar
  Productions = []     # all the production rules in the grammar


  def __init__(self, name):
    self.name = name


  def start(self, start):
    self.Start = start


  # splits a series of productions intos the form:
  # (rule #, [[seq of symbols for a production] ...the rest of the productions])
  # empty list [] specifies an epsilon production.
  def production(self, lhs, rhs):
    rule = (lhs , [productions.split() for productions in rhs.split('|')])
    self.Productions.append(rule)


  # all literal symbols which appear in the grammar
  def __terminals__(self):
    terminals = frozenset()
    lhs = {key for (key, _) in self.Productions}
    for (_, v) in self.Productions:
      for production in v:
        for symbol in production:
          if symbol not in lhs:
            terminals |= frozenset([symbol])
    return terminals


  # all non terminals are just the production rules
  def __nonterminals__(self):
    return frozenset({production for (production, _) in self.Productions})


  # calculate the first set following the algorithm set forth here:
  # http://www.jambe.co.nz/UNI/FirstAndFollowSets.html
  def __first__(self, terminals, nonterminals):
    first = {}

    # 1. If X is a terminal then First(X) is just X!
    for terminal in terminals:
      first[terminal] = frozenset([terminal])

    # --init first sets for nonterminals--
    for nonterminal in nonterminals:
      first[nonterminal] = frozenset()

    # 2. If there is a Production X -> epsilon then add epsilon to first(X)
    for (X, productions) in self.Productions:
      for production in productions:
        if len(production) == 0:
          first[X] |= frozenset([self.Epsilon])

    # 4. First(Y1Y2..Yk) is either:
    #   a. First(Y1) (if First(Y1) doesn't contain epsilon)
    #   b. OR (if First(Y1) does contain epsilon) then everything in First(Y1)
    #      <except for epsilon> as well as everything in First(Y2..Yk)
    #   c. If First(Y1) First(Y2)..First(Yk) all contain epsilon then add
    #      epsilon to First(Y1Y2..Yk) as well
    def _first(Ys):
      if len(Ys) == 0: # from recursive call
        return frozenset()
      elif self.Epsilon not in first[Ys[0]]:
        return first[Ys[0]]
      elif self.Epsilon in first[Ys[0]]:
        s = ((first[Ys[0]] - frozenset([self.Epsilon])) | _first(Ys[1:]))
        for Y in Ys:
          if self.Epsilon not in first[Y]:
            return s
        return s | frozenset([self.Epsilon])

    # --need to repeat until the sets are no longer changing--
    while True:
      c = { k: v for (k, v) in first.items() }

      # 3. If there is a Production X -> Y1Y2..Yk
      #    then add first(Y1Y2..Yk) to first(X)
      for (X, productions) in self.Productions:
        for Ys in productions:
          if len(Ys) != 0: # we already took care of epsilon productions
            first[X] |= _first(Ys)
  
      if frozenset(c.items()) == frozenset(first.items()):
        return first


  # calculate the follow set following the algorithm set forth here:
  # http://www.jambe.co.nz/UNI/FirstAndFollowSets.html
  def __follow__(self, nonterminals, first):
    follow = {}

    # --init follow sets for nonterminals--
    for nonterminal in nonterminals:
      follow[nonterminal] = frozenset()

    # 1. First put $ (end of input marker) in Follow(S) (S is the start symbol)
    follow[self.Start] = frozenset([self.Dollar])

    def _follow(A, Ys):
      for k in range(0, len(Ys)):
        B = Ys[k]
        # find first nonterminal after terminal, or 2nd nonterminal
        if B in nonterminals and k > 0:
          # 3. If there is a production A -> aB,
          # then everything in FOLLOW(A) is in FOLLOW(B)
          if k == len(Ys)-1:
            follow[B] |= follow[A]
          else:
            # 2. If there is a production A -> aBb, (where a can be a whole
            # string) then everything in FIRST(b) except for epsilon is placed
            # in FOLLOW(B).
            b = Ys[k+1]
            follow[B] |= (first[b] - frozenset([self.Epsilon]))
            # 4. If there is a production A -> aBb, where FIRST(b) contains
            # epsilon, then everything in FOLLOW(A) is in FOLLOW(B)
            if self.Epsilon in first[b]:
              follow[B] |= follow[A]
          return

    # --need to repeat until the sets are no longer changing--
    while True:
      c = { k: v for (k, v) in follow.items() }

      for (X, productions) in self.Productions:
        for Ys in productions:
          if len(Ys) > 0: # ignore epsilon production
            _follow(X, Ys)

      if frozenset(c.items()) == frozenset(follow.items()):
        return follow

  # construct the LL(1) parsing table by finding predict sets
  def __table__(self, terminals, nonterminals, first, follow):
    # Predict(A --> X1...Xm) = 
    # First(X1...Xm) U (If X1...Xm --> epsilon then Follow(A) else null)
    # @https://www.cs.rochester.edu/~nelson/courses/csc_173/grammars/parsing.html
    def predict(X, Ys):
      if len(Ys) == 1 and Ys[0] == self.Epsilon:
        return follow[X]
      if len(Ys) == 0: # from recursive call
        return frozenset()
      elif self.Epsilon not in first[Ys[0]]:
        return first[Ys[0]]
      elif self.Epsilon in first[Ys[0]]:
        s = ((first[Ys[0]] - frozenset([self.Epsilon])) | predict(X, Ys[1:]))
        for Y in Ys:
          if self.Epsilon not in first[Y]:
            return s
        return s | follow[X]

    # flatten rules so they can be enumerated, and find predict sets
    productions = []
    predictions = []
    for (X, _productions) in self.Productions:
      for production in _productions:
        productions.append((X, production))
        if len(production) == 0:
          predictions.append((X, predict(X, [self.Epsilon])))
        else:
          predictions.append((X, predict(X, production)))

    # need to enumerate [non]terminals since we are putting them in a table
    terminals = list(terminals | frozenset([self.Dollar]))
    nonterminals = list(nonterminals)
    table = [[] for _ in nonterminals]
    for row in range(0, len(table)):
      table[row].append(nonterminals[row])
      for _ in terminals:
        table[row].append(frozenset())
    terminals.insert(0, ' ')
    table.insert(0, terminals)

    # fill in the table
    for k in range(0, len(predictions)):
      (Nonterminal, Terminals) = predictions[k]
      n = nonterminals.index(Nonterminal)+1 # account for column headers
      for Terminal in Terminals:
        t = terminals.index(Terminal)
        table[n][t] |= frozenset([k])

    return (table, productions, predictions)


  # grammar is ll(1) if parse table has (@maximum) a single entry per table slot
  # conflicting for the predicitions
  def __parsable__(self, table, rules):
    LL1 = True
    conflicts = []
    for r in range(1, len(table)): # ignore column headers
      for c in range(1, len(table[r])): # ignore row header
        if len(table[r][c]) > 1:
          LL1 = False
          conflicts.append((table[r][0], table[r][c]))
    return (LL1, conflicts)


  def make(self):
    terminals = self.__terminals__()
    nonterminals = self.__nonterminals__()
    first = self.__first__(terminals, nonterminals)
    follow = self.__follow__(nonterminals, first)
    (table, rules, predictions) = self.__table__(terminals, nonterminals, first, follow)
    (LL1, conflicts) = self.__parsable__(table, rules)

    return {
      "name":          self.name,
      "start":         self.Start,
      "rules":         rules,
      "predictions":   predictions,
      "terminals":     terminals,
      "nonterminals":  nonterminals,
      "first":         first,
      "follow":        follow,
      "table":         table,
      "parsable?":     LL1,
      "conflicts":     conflicts,
    }


if __name__ == "__main__":
  # test grammar @http://www.jambe.co.nz/UNI/FirstAndFollowSets.html
  # externally validated using tool located
  # @http://hackingoff.com/compilers/predict-first-follow-set 
  test = ContextFreeGrammar("Test Grammar")

  test.production('<E>',   '<T> <E\'>')
  test.production('<E\'>', '+ <T> <E\'> |')
  test.production('<T>',   '<F> <T\'>')
  test.production('<T\'>', '* <F> <T\'> |')
  test.production('<F>',   '( <E> ) | id')

  test.start('<E>')

  LL1 = test.make()

  if LL1['name'] != 'Test Grammar':
    raise ValueError('Invalid name produced')

  if LL1['start'] != '<E>':
    raise ValueError('Invalid start production produced')

  if not LL1['parsable?']:
    raise ValueError('Improper reporting of the grammars parsability')

  if len(LL1['conflicts']) > 0:
    raise ValueError('Invalid conflicts produced')

  if LL1['terminals'] != frozenset(['(', ')', '+', '*', 'id']):
    raise ValueError('Invalid terminal set produced')

  if LL1['nonterminals'] != frozenset(['<T>', '<F>', '<E>', "<E'>", "<T'>"]): 
    raise ValueError('Invalid nonterminal set produced')

  first = {
    '(': frozenset(['(']),
    ')': frozenset([')']),
    '+': frozenset(['+']),
    '*': frozenset(['*']),
    'id': frozenset(['id']),
    '<E>': frozenset(['(', 'id']),
    "<E'>": frozenset([1, '+']),
    '<T>': frozenset(['(', 'id']),
    "<T'>": frozenset([1, '*']),
    '<F>': frozenset(['(', 'id'])
  }

  for elem in LL1['first']:
    if first[elem] != LL1['first'][elem]:
      raise ValueError('Invalid first set produced')

  follow = {
    '<E>': frozenset([0, ')']),
    "<E'>": frozenset([0, ')']),
    '<T>': frozenset([0, ')', '+']),
    "<T'>": frozenset([0, ')', '+']),
    '<F>': frozenset([0, ')', '+', '*'])
  }

  for nonterminal in LL1['follow']:
    if follow[nonterminal] != LL1['follow'][nonterminal]:
      raise ValueError('Invalid follow set produced')

  rules = [ # flattened set in the order we entered them earlier
    ('<E>',  ['<T>', "<E'>"]),
    ("<E'>", ['+', '<T>', "<E'>"]),
    ("<E'>", []),
    ('<T>',  ['<F>', "<T'>"]),
    ("<T'>", ['*', '<F>', "<T'>"]),
    ("<T'>", []),
    ('<F>',  ['(', '<E>', ')']),
    ('<F>',  ['id'])
  ]

  if len(LL1['rules']) != 8:
    raise ValueError('Invalid rule set produced')

  for rule in range(0, 8):
    if rules[rule][0] != LL1['rules'][rule][0]:
      raise ValueError('Invalid rule LHS produced')
    if len(rules[rule][1]) != len(LL1['rules'][rule][1]):
      raise ValueError('Invalid rule RHS produced')
    for i in range(0, len(rules[rule][1])):
      if rules[rule][1][i] != LL1['rules'][rule][1][i]:
        raise ValueError('Invalid rule RHS produced')

  predictions = [ # 1:1 correspondence with rules
    ('<E>',  frozenset(['(', 'id'])),
    ("<E'>", frozenset(['+'])),
    ("<E'>", frozenset([0, ')'])),
    ('<T>',  frozenset(['(', 'id'])),
    ("<T'>", frozenset(['*'])),
    ("<T'>", frozenset(['+', 0, ')'])),
    ('<F>',  frozenset(['('])),
    ('<F>',  frozenset(['id']))
  ]

  if len(LL1['predictions']) != 8:
    raise ValueError('Invalid prediction set produced')

  for prediction in range(0, 8):
    if predictions[prediction][0] != LL1['predictions'][prediction][0]:
      raise ValueError('Invalid prediction LHS produced')
    if predictions[prediction][1] != LL1['predictions'][prediction][1]:
      raise ValueError('Invalid prediction RHS produced')

  table = [
    [' ',    0,              ')',            '(',            '+',            '*',            'id'          ],
    ['<E>',  frozenset([]),  frozenset([]),  frozenset([0]), frozenset([]),  frozenset([]),  frozenset([0])],
    ["<E'>", frozenset([2]), frozenset([2]), frozenset([]),  frozenset([1]), frozenset([]),  frozenset([]) ],
    ["<T>",  frozenset([]),  frozenset([]),  frozenset([3]), frozenset([]),  frozenset([]),  frozenset([3])],
    ["<T'>", frozenset([5]), frozenset([5]), frozenset([]),  frozenset([5]), frozenset([4]), frozenset([]) ],
    ["<F>",  frozenset([]),  frozenset([]),  frozenset([6]), frozenset([]),  frozenset([]),  frozenset([7])]
  ]

  if len(LL1['table']) != 6:
    raise ValueError('Invalid number of table rows produced')

  for r in range(0, len(LL1['table'])):
    if len(LL1['table'][r]) != 7:
      raise ValueError('Invalid number of table columns produced')

  # sort table rows so both tables match allowing comparison
  for row in range(0, len(table)):
    for _row in range(0, len(LL1['table'])):
      if table[row][0] == LL1['table'][_row][0] and row != _row:
        LL1['table'][row], LL1['table'][_row] = LL1['table'][_row], LL1['table'][row]

  for r in range(0, 6): 
    for c in range(0, 7):
      if LL1['table'][r][c] != table[r][c]:
        raise ValueError('Invalid table value produced')
