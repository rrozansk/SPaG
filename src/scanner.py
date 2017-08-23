################################################################################
# During Lexical Analysis the Lexer/Scanner recognizes regular expressions as
# corresponding token types. These tokens are then sent to the parser.
# Tokens have a type and value, but can also have character and line number
# information as well. White space tokens and comments are usually discarded
# in this phase, but any token type desired may be discarded.
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

  Star = 0
  Union = 1
  Concat = 2
  Plus = 3
  Question = 4

  Epsilon = 5

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
  # simplifies the following expressions:
  #   *      -> self.Start
  #   |      -> self.Union
  #   +      -> self.Plus
  #   ?      -> self.Question
  #   \e     -> self.Epsilon
  #   \\     -> \
  #   .      -> ** anything **
  # future extns [], {}, \d, \w, etc.
  #   ()     -> python list
  def __expand__(self, regexp):
    call_stk = []
    expr = []
    escape = False
    cs = (self.uppers | self.lowers | self.digits | self.spaces | self.specials)
    for c in regexp:
      if c in cs:
        if not escape:
          if c == '\\': escape = True
          else: expr.append(c) 
        else:
          escape = False
          if c == 'e': expr.append(self.Epsilon)
          elif c == '\\': expr.append('\\')
          # 'd': None,   # any digit
          # 's': None,   # any space
          # 'l': None,   # any lower alpha
          # 'u': None,   # any upper alpha
          # 'w': None,   # any alpha numeric
          # 'm': None,   # any meta
          # 'g': None,   # any non meta graph
          else: return 'Error: invalid escape sequence'
      elif c in self.metas:
        if escape: # all meta's are escaped for literal
          escape = False
          expr.append(c)
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

  # reformats the epression into prefix triples (op, e0, e1) this also allows
  # the removal of the list/parenthesis groupings
  def __format__(regexp): # TODO: | is the only infix operator --> all others are postfix (concat is implicit)
    _type = type(regexp)
    if _type is list: # grouping
      expr = [__format__(e) for e in regexp]
      args = []
      for e in expr:
        _type = type(e)
        if _type is str: return e # bubble error up
        elif _type is int: # op
          if len(args) != 1: return 'Error: *,+,? only require a single argument'
          if e == self.Star: args.append((self.Star, args.pop(), None))
          if e == self.Union: args.append((self.Union, args.pop(), None)) # FIXME: 2nd arg needed
          elif e == self.Plus: args.append((self.Plus, args.pop(), None))
          elif e == self.Question: args.append((self.Question, args.pop(), None))
          else: return 'Error: unknown operator encountered during formatting'
        elif _type is tuple: # implicit concat 
          # push or make concat 
          if len(args) != 2: return 'Error: concatenation requires 2 arguments'
          e1 = args.pop()
          e0 = args.pop()
          args.append((self.Concat, e0, e1))
        else: return 'Error: unknown type encountered during formatting'
      return expr
    elif _type is int:
      if regexp == self.Epsilon: return  (None, regexp, None) # epsilon
      else: return regexp # op (+, ?, *, |) 
    elif _type is str: return (None, regexp, None) # character
    else: return 'Error: unknown type encountered during regexp formatting'


  # converts a regular expression to an NFA with epsilon productions using
  # thompsons algorithm, which is able to handle: union |, kleene star *,
  # concatenation ., epsilon \e, literals, and syntax extensions + and ?.
  # followed the algorithm set forth in 'A taxonomy of finite automata
  # construction algorithms' by Bruce Watson, located at:
  # http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf
  def __NFA__(self, regexp):
    E = self.Epsilon # shorhand convience

    def gen_state():
      for i in range(0, sys.maxint): yield i

    # return set of state transitions of the form: (in, out, on)
    def thompson(s, f, (op, e0, e1)):
      if op == self.Concat:
        p = gen_state()
        q = gen_state()
        M1 = thompson(s, p, e0)
        M2 = thompson(q, f, e1)
        return frozenset([(p, q, E)]) | M1 | M2
      elif op == self.Union:
        p = gen_state()
        q = gen_state()
        r = gen_state()
        t = gen_state()
        M1 = thompson(p, q, e0)
        M2 = thompson(r, t, e1)
        return frozenset([(s, p, E), (s, r, E), (q, f, E), (t, f, E)]) | M1 | M2
      elif op == self.Star:
        p = gen_state()
        q = gen_state()
        M = thompson(p, q, e0)
        return frozenset([(s, p, E), (q, p, E), (s, f, E), (q, f, E)]) | M
      elif op == self.Plus:
        p = gen_state()
        q = gen_state()
        M = thompson(p, q, e0)
        return frozenset([(s, p, E), (q, p, E), (q, f, E)]) | M
      elif op == self.Question:
        p = gen_state()
        q = gen_state()
        M = thompson(p, q, e0)
        return frozenset([(s, p, E), (q, f, E), (s, f, E)]) | M
      else: # op == None, literal or epsilon
        return frozenset([(s, f, e0)])

    s = gen_state()
    f = gen_state()
    return {
      's': s,
      'f': f,
      't': thompson(s, f, regexp)
    }
     

  # converts the NFA to DFA using subset construction
  def __DFA__(self, NFA): # TODO
    return None


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
        DFAs[name]['NFA'] = None
        #DFAs[name]['NFA'] = self.__NFA__(DFAs[name]['expanded'])
        DFAs[name]['DFA'] = self.__DFA__(DFAs[name]['NFA'])
        DFAs[name]['min DFA'] = self.__min__(DFAs[name]['DFA'])

    tokenizer = []
    for info in DFAs.values():
      if info['error'] is None: tokenizer.append('(' + info['regexp'] + ')')
    scanner = '|'.join(tokenizer)

    # FIXME: need smarter scanner. if token was not wanted i need to read those
    # and ignore them - i.e. continue in the FSM (recursive call)

    #formal = self.__expand__(scanner)
    #NFA = self.__NFA__(formal)
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
    if _g['s'] != g['s']: return False
    if _g['f'] != g['f']: return False
    return _g['t'] == g['t']

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
