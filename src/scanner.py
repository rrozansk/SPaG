################################################################################
# During Lexical Analysis the Lexer/Scanner recognizes regular expressions as
# corresponding token types. These tokens are then sent to the parser.
# Tokens have a type and value, but can also have character and line number
# information as well. White space tokens and comments are usually discarded,
# but any token type desired may be discarded.
# 
# The difference between lexers and parser is that a lexer reconizes regular
# grammars/expressions, while parser recognize context free grammars. The main
# difference is regular grammars can be converted into NFA with epsilon prodcutions
# using thompsons algorithm, and then used to construct a corresponding DFA using
# subset construction. After this is completed it can further be minimized.
# Context free grammars can be converted into PDA's, which require a stack, but
# they are also more powerful than regular grammars since they can properly deal
# with recursion.
################################################################################
import uuid

class RegularGrammar(object):


  spaces = {'\s', '\t', '\v', '\f', '\r', '\n'}
  uppers = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}
  lowers = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}
  digits = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
  specials = {'!', '"', '#', '$', '%', '&', '\'', '`', '_', '/', ':', ';', '<',
              '=', '>', '-', '^', '\\', '{', '}', '~', ',', '@'}
  metas = { '?', '+', '[', ']', '.', '(', ')', '*', '|'}

  characters  = (self.uppers | self.lowers | self.digits | self.spaces | self.specials)

  Star = 0
  Union = 1
  Concat = 2
  Plus = 3
  Question = 4
  Epsilon = 5
  Left = 6
  Right = 7

  ops = {      # ***higher is more important***
      self.Left:     (3, None),
      self.Right:    (3, None),
      self.Star:     (2, False), # right-associative
      self.Plus:     (2, False), # right-associative
      self.Question: (2, False), # right-associative
      self.Concat:   (1, True),  # left-associative
      self.Union:    (0, True),  # left-associative
  }

  Dot = None       # internal rep of '.' regexp

  name = None      # name of scanner
  regexps = {}     # token dictionary ::=  name -> (regexp, keep)


  def __init__(self, name):
    self.name = name
    anything = list(self.uppers | self.lowers | self.digits | self.spaces | self.specials)
    anything += ['\\' + e for e in self.metas]
    l = []
    for e in anything:
      l.append(e)
      l.append(self.Union)
    l.append('\\e') # add epsilon
    self.Dot = l


  # only accepts printable ASCII char values (33-126)
  # and space chars ( \s, \t, \v, \f, \r, \n)
  def token(self, name, keep, regexp):
     self.regexps[name] = (regexp, keep)


  # 'pretreat' the regular expression to simplify and validate it.
  # also insert concatentation to make it explicit.
  # simplifies the following expressions:
  #   *       -> self.Start
  #   |       -> self.Union
  #   +       -> self.Plus
  #   ?       -> self.Question
  #   \e      -> self.Epsilon
  #   \\      -> \
  #   \[meta] -> [meta]
  #   (       -> self.Left
  #   )       -> self.Right
  #   .       -> ** anything **
  # future extns [], {}, \d, \w, etc.
  #   - 'd': None,   # any digit
  #   - 's': None,   # any space
  #   - 'l': None,   # any lower alpha
  #   - 'u': None,   # any upper alpha
  #   - 'w': None,   # any alpha numeric
  #   - 'm': None,   # any meta
  #   - 'g': None,   # any non meta graph
  def __expand__(self, regexp): # FIXME: inset concatenation to make it explicit
    call_stk = []
    expr = []
    escape = False
    for c in regexp:
      if c in self.characters:
        if not escape:
          if c == '\\': escape = True
          else: expr.append(c)  # TODO inset concat?
        else:
          escape = False
          if c == 'e': expr.append(self.Epsilon) # TODO inset concat?
          elif c == '\\': expr.append('\\') # TODO inset concat?
          else: return 'Error: invalid escape sequence'
      elif c in self.metas:
        if escape: # all meta's are escaped for literal
          escape = False
          expr.append(c) # TODO inset concat?
        else:
          if c == '*':
            if len(expr) == 0: return 'Error: empty kleene star (*) sequence'
            expr.append(self.Star)
          elif c == '|':
            if len(expr) == 0: return 'Error: empty union (|) sequence'
            expr.append(self.Union)
          elif c == '+':
            if len(expr) == 0: return 'Error: empty + sequence'
            expr.append(self.Plus)
          elif c == '?':
            if len(expr) == 0: return 'Error: empty ? sequence'
            expr.append(self.Question)
          elif c == '.': expr.append(self.Dot)
          elif c == '(':
            call_stk.append(expr)
            expr = []
          elif c == ')':
            if len(call_stk) == 0: return 'Error: invalid group () sequence'
            if len(expr) == 0: return 'Error: empty group () sequence'
            group = expr
            expr = call_stk.pop()
            expr.append(group)
          #elif c == '[': pass
          #elif c == ']': pass
      else: return 'Error: invalid/unrecognized character'
    if len(call_stk) > 0: return 'Error: unclosed group () sequence'
    if escape: return 'Error: empty escape sequence'
    if len(expr) == 0: return 'Error: empty expression'
    if expr[-1] == self.Union: return 'Error: invalid Union (|) sequence'
    return expr


  # as explained @https://en.wikipedia.org/wiki/Shunting-yard_algorithm
  def __shunt__(self, expression):
    stk = []  # operator stack
    q = []    # output Q

    for token in expression:
      if token in self.characters: q.append(token)
      elif token is self.Left: stk.append(self.Left)
      elif token is self.Right:
        while len(stk) > 0 and stk[-1] is not self.Left: q.append(stk.pop())
        if len(stk) is 0 or stk[-1] is not self.Left:
          return 'Error: mismatched parenthesis'
        stk.pop()
      elif token in self.ops:
        while len(stk) > 0 and self.ops[stk[-1]][0] >= self.ops[token][0] and self.ops[stk[-1]][1]:
            q.append(stk.pop())
        stk.append(token)
      else: return 'Error: invalid input'

    while len(stk) > 0:
      if stk[-1] is self.Left or stk[-1] is self.Right:
        return 'Error: mismatched parenthesis'
      q.append(stk.pop())

    return q # RPN (reverse polish notation) expression


  # converts a regular expression in RPN to an NFA with epsilon productions
  # using thompsons algorithm, which is able to handle: union |, kleene star *,
  # concatenation ., epsilon \e, literals, and syntax extensions + and ?.
  # adapted from section 4.1 in 'A taxonomy of finite automata construction
  # algorithms' by Bruce Watson, located at:
  # http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf
  def __eNFA__(self, expression): # exression is in RPN (postfix)
    stk = [] # NFA machine stk
    s, f, t = None, None, None # stk frame vars
    E = self.Epsilon # shorhand convience

    for token in expression:
      if token is self.ops:
        if token == self.Concat:
          M1 = stk.pop()
          M2 = stk.pop()
          s, f = M1['s'], M2['f']
          t = frozenset([(M1['f'], M2['s'], E)]) | M1['t'] | M2['t']
        elif token == self.Union:
          M1 = stk.pop()
          M2 = stk.pop()
          s, f = uuid.uuid1(), uuid.uuid1()
          t = frozenset([(s, M1['s'], E), (s, M2['s'], E), (M1['f'], f, E), (M2['f'], f, E)]) | M1['t'] | M2['t']
        elif token == self.Star:
          M = stk.pop()
          s, f = uuid.uuid1(), uuid.uuid1()
          t = frozenset([(s, f, E), (M['s'], M['f'], E), (s, M['s'], E), (M['f'], f, E)]) | M['t']
        elif token == self.Plus:
          M = stk.pop()
          s, f = uuid.uuid1(), uuid.uuid1()
          t = frozenset([(M['s'], M['f'], E), (s, M['s'], E), (M['f'], f, E)]) | M['t']
        elif token == self.Question:
          M = stk.pop()
          s, f = uuid.uuid1(), uuid.uuid1()
          t = frozenset([(s, f, E), (s, M['s'], E), (M['f'], f, E)]) | M['t']
        else: return 'Error: unrecognized operator in thompson construction'
      else: # token is a character literal or self.Epsilon
        s, f = uuid.uuid1(), uuid.uuid1()
        t = frozenset([(s, f, (s, f, token))])
      stk.push({ 's': s, 'f': f, 't': t })

    return stk.pop()


  # find the e closure: { q' | q ->*e q' } from a given start state q given a
  # dictionary of epsilon transitions in the form: in -> out, automatically
  # handling cycles
  def e_closure(q, etransitions):
    if q not in etransitions: return frozenset()

    explore = closure = etransitions[q]
    while len(explore) > 0:
      q = explore.pop()
      if q not in etransitions: continue 
      for transition in etransitions[q]:
        if transition in closure: continue
        closure |= frozenset(transition)
        explore |= frozenset(transition)

    return closure


  # converts the eNFA to DFA using subset construction and e closure conversion
  def __DFA__(self, eNFA):
    etransitions = {}
    for (s, f, t) in eNFA['t']:
      if t is self.Epsilon:
        if s in etransitions: etransitions[s] |= frozenset(f)
        else: etransitions[s] = frozenset(f)

    closures = {}

    DFA = {}
    # TODO: powerset construction with e_closure
    #if q in closures: return closures[q] # check cache
    #closure[q] = e_closure(q, etransitions) # add to cache
    #q0 = eNFA['s']
    #q0 = eNFA['f']
    #q0 = eNFA['t']
    return DFA


  # minimizes the DFA
  def __min__(self, DFA): # TODO
    return None


  # converts all tokens representing regular expressions (regular grammars) to
  # NFAs with epsilon transitions, which are then converted into equivalent DFAs
  # and finally minimized to a unique DFA capable of parsing any input in O(n)
  # time to produce a possible match
  def make(self):
    DFAs = {}
    for (name, (regexp, keep)) in self.regexps.items():
      DFAs[name] = {
        'keep': keep,
        'regexp': regexp,
      }
      expanded = self.__expand__(regexp)
      if type(expanded) is str:
        DFAs[name]['error'] = expanded 
        DFAs[name]['expanded'] = []
        DFAs[name]['NFA'] = None
        DFAs[name]['DFA'] = None
        DFAs[name]['min DFA'] = None
      else:
        DFAs[name]['error'] = None
        DFAs[name]['expanded'] = expanded
        DFAs[name]['NFA'] = self.__eNFA__(self.__format__(DFAs[name]['expanded']))
        DFAs[name]['DFA'] = self.__DFA__(DFAs[name]['NFA'])
        DFAs[name]['min DFA'] = self.__min__(DFAs[name]['DFA'])

    tokenizer = []
    for info in DFAs.values():
      if info['error'] is None: tokenizer.append('(' + info['regexp'] + ')')
    scanner = '|'.join(tokenizer)

    # FIXME: need smarter scanner. if token was not wanted i need to read those
    # and ignore them - i.e. continue in the FSM (recursive call)

    #formal = self.__expand__(scanner)
    #NFA = self.__eNFA__(formal)
    #DFA = self.__DFA__(NFA)
    #mdfa = self.__min__(DFA)
    #DFAs['__scanner__'] = {
    #    "keep": True,
    #    "error": None,
    #    "regexp": scanner,
    #    "NFA": NFA,
    #    "DFA": DFA,
    #    "min DFA": mdfa,
    #}

    return (self.name, DFAs)


if __name__ == '__main__':
  # -*- coding: UTF-8 -*-
  tokenizer = RegularGrammar('Test Scanner')

  # core syntax tests
  tokenizer.token('core_test0',   True,  '(\\e|a*b)') # wikipedia
  tokenizer.token('core_test1',   True, '((ab)|c)*') # https://www.cs.york.ac.uk/fp/lsa/lectures/REToC.pdf
  tokenizer.token('core_test2',   True, '(0|(1(01*(00)*0)*1)*)*')  # wikipedia
  #tokenizer.token('core_test3',  True, '(foo)+')
  #tokenizer.token('core_test4',  True, '(bar)?')
  # syntax extension tests
  #tokenizer.token('extn_test2',  True, 'some.thing')
  # invalid syntax tests
  tokenizer.token('error_test0',  True, '+')
  tokenizer.token('error_test1',  True, '?')
  tokenizer.token('error_test2',  True, '|')
  tokenizer.token('error_test3',  True, '*')
  tokenizer.token('error_test4',  True, '\\u')
  tokenizer.token('error_test5',  True, 'foo)')
  tokenizer.token('error_test6',  True, '()')
  tokenizer.token('error_test7',  True, 'fo\xc3o')
  tokenizer.token('error_test8',  True, 'bar\\')
  tokenizer.token('error_test9',  True, '(foo')
  tokenizer.token('error_test10', True, '')
  tokenizer.token('error_test11', True, 'a|')

  (name, tokenizers) = tokenizer.make()

  scanners = {
    'core_test0': {
        'keep': True,
        'error': None,
        'regexp': '(\\e|a*b)',
        'expanded': [[tokenizer.Epsilon, tokenizer.Union, 'a', tokenizer.Star, 'b']],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'core_test1': {
        'keep': True,
        'error': None,
        'regexp': '((ab)|c)*',
        'expanded': [[['a', 'b'], tokenizer.Union, 'c'], tokenizer.Star],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'core_test2': {
        'keep': True,
        'error': None,
        'regexp': '(0|(1(01*(00)*0)*1)*)*',
        'expanded': [['0', tokenizer.Union, ['1', ['0', '1', tokenizer.Star,
                        ['0', '0'], tokenizer.Star, '0'], tokenizer.Star, '1'],
                        tokenizer.Star], tokenizer.Star],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },

    'error_test0': {
        'keep': True,
        'error': 'Error: empty + sequence',
        'regexp': '+',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test1': {
        'keep': True,
        'error': 'Error: empty ? sequence',
        'regexp': '?',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test2': {
        'keep': True,
        'error': 'Error: empty union (|) sequence',
        'regexp': '|',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test3': {
        'keep': True,
        'error': 'Error: empty kleene star (*) sequence',
        'regexp': '*',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test4': {
        'keep': True,
        'error': 'Error: invalid escape sequence',
        'regexp': '\\u',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test5': {
        'keep': True,
        'error': 'Error: invalid group () sequence',
        'regexp': 'foo)',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test6': {
        'keep': True,
        'error': 'Error: empty group () sequence',
        'regexp': '()',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test7': {
        'keep': True,
        'error': 'Error: invalid/unrecognized character',
        'regexp': 'fo\xc3o',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test8': {
        'keep': True,
        'error': 'Error: empty escape sequence',
        'regexp': 'bar\\',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test9': {
        'keep': True,
        'error': 'Error: unclosed group () sequence',
        'regexp': '(foo',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test10': {
        'keep': True,
        'error': 'Error: empty expression',
        'regexp': '',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    },
    'error_test11': {
        'keep': True,
        'error': 'Error: invalid Union (|) sequence',
        'regexp': 'a|',
        'expanded': [],
        'NFA': None,
        'DFA': None,
        'min DFA': None,
    }
  }

  def cmp_digraph(_g, g):
    return _g['s'] == g['s'] and _g['f'] == g['f'] and _g['t'] == g['t']

  def cmp_deeplist(_ls, ls):
    if len(_ls) != len(ls): return False
    for i in range(0, len(_ls)):
      if type(_ls[i]) != type(ls[i]): return False
      if type(_ls[i]) is list:
        if not cmp_deeplist(_ls[i], ls[i]): return False
      else:
        if _ls[i] != ls[i]: return False
    return True

  if name != 'Test Scanner':
    raise ValueError('Error: Incorrect reporting of scanner name')

  if len(tokenizers) != len(scanners):
    raise ValueError('Error: Incorrect number of tokenizers produced')

  for (name, _tokenizer) in scanners.items():
    tokenizer = tokenizers.get(name, None)

    if tokenizer is None:
      raise ValueError('Error: Incorrect tokenizer name produced')

    if _tokenizer['regexp'] != tokenizer['regexp']:
      raise ValueError('Error: Incorrect reporting of regexp')

    if _tokenizer['keep'] != tokenizer['keep']:
      raise ValueError('Error: Incorrect reporting of keep')

    if _tokenizer['error'] != tokenizer['error']:
      raise ValueError('Error: Incorrect reporting of error')

    if not cmp_deeplist(_tokenizer['expanded'], tokenizer['expanded']):
      raise ValueError('Error: Incorrect expanded expression produced')

    if not cmp_digraph(_tokenizer['NFA'], tokenizer['NFA']):
      raise ValueError('Error: Incorrect NFA produced')

    if not cmp_digraph(_tokenizer['DFA'], tokenizer['DFA']):
      raise ValueError('Error: Incorrect DFA produced')

    if not cmp_digraph(_tokenizer['min DFA'], tokenizer['min DFA']):
      raise ValueError('Error: Incorrect minimized DFA produced')
