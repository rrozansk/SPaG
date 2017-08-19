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
  Epsilon = 2

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
  #   *     -> self.Start
  #   |     -> self.Union
  #   \e    -> self.Epsilon
  #   \\    -> \
  #   +     -> a+ = aa*
  #   ?     -> a? = a|epsilon
  #   [x-y] -> [a-c] = (a|b|c)
  #   .     -> [a-z]|[A-Z]|[0-9] or space...
  #   ()    -> python list
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
          else: return 'Error: invalid escape sequence'
      elif c in self.metas:
        if escape: # all meta's are escaped for literal
          escape = False
          expr.append(c)
        else:
          if c == '*':
            if len(expr) == 0: return 'Error: invalid kleene star (*) sequence'
            expr.append(self.Star)
          elif c == '|':
            if len(expr) == 0: return 'Error: invalid union (|) sequence'
            expr.append(self.Union)
          elif c == '+':
            if len(expr) == 0: return 'Error: invalid + sequence'
            expr.append(expr[-1])
            expr.append(self.Star)
          elif c == '?':
            if len(expr) == 0: return 'Error: invalid ? sequence'
            expr.append(self.Union)
            expr.append(self.Epsilon)
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
    if len(call_stk) > 0: return 'Error: invalid group () sequence'
    if escape: return 'Error: invalid escape sequence'
    return expr
    

  # converts regexps to NFA with epsilon productions using thompsons algorithm
  # thomspsons algorithms can handle -> # union | , concat, kleene star *, epsilon,
  # and literals. must also recognize parenthesis (sublists/recursive calls) for
  # grouping purposes
  def __NFA__(self, regexp): # TODO
    return None


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
      formal = self.__expand__(regexp)
      if type(formal) is str:
        DFAs[name] = {
          "regexp": None,
          "keep": None,
          "formal expr": None,
          "NFA": None,
          "DFA": None,
          "min DFA": None,
          "error": formal,
        }
      else:
        NFA = self.__NFA__(formal)
        DFA = self.__DFA__(NFA)
        mdfa = self.__min__(DFA)
        DFAs[name] = {
          "regexp": regexp,
          "keep": keep,
          "formal expr": formal,
          "NFA": NFA,
          "DFA": DFA,
          "min DFA": mdfa,
          "error": None,
        }

    tokenizer = []
    for info in DFAs.values():
      if info['error'] is None: tokenizer.append('(' + info['regexp'] + ')')
    scanner = '|'.join(tokenizer)

    # FIXME: need smarter scanner. if token was not wanted i need to read those
    # and ignore them - i.e. continue in the FSM (recursive call)

    formal = self.__expand__(scanner)
    NFA = self.__NFA__(formal)
    DFA = self.__DFA__(NFA)
    mdfa = self.__min__(DFA)
    DFAs['__scanner__'] = {
        "regexp": scanner,
        "keep": True,
        "formal expr": formal,
        "NFA": NFA,
        "DFA": DFA,
        "min DFA": mdfa,
    }

    return (self.name, DFAs)


if __name__ == '__main__':
  tokenizer = RegularGrammar("Test Scanner")

  tokenizer.token("test_reg",      True, 'foobar')
  tokenizer.token("test_eps",      True, '\e')
  tokenizer.token("test_star",     True, 'fo*bar')
  tokenizer.token("test_union",    True, 'f|b')
  tokenizer.token("test_plus",     True, '0+')
  tokenizer.token("test_question", True, 'A?')
  tokenizer.token("test_group",    True, 'foo+(bar)?*')
  tokenizer.token("test_dot",      True, 'foo.bar')
  tokenizer.token("test_range",    True, '[0-9]')
  tokenizer.token("test_err1",     True, ')')
  tokenizer.token("test_err2",     True, '+')

  (name, tokenizers) = tokenizer.make()

  scanners = { # TODO
    "[name]": {
        "keep": True,
        "error": True,
        "regexp": "",
        "formal expr": "",
        "NFA": None,
        "DFA": None,
        "min DFA": None,
    },
    "__scanner__": {
        "keep": True,
        "error": True,
        "regexp": "",
        "formal expr": "",
        "NFA": None,
        "DFA": None,
        "min DFA": None,
    }
  }

  def cmp_NFA(_NFA, nfa): # TODO
    pass

  def cmp_DFA(_DFA, dfa): # TODO
    pass

  def cmp_formal(_expr, expr): # TODO
    pass

  if name != "Test Scanner":
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

    if not cmp_formal(_tokenizer['formal expr'], tokenizer['formal expr']):
      raise ValueError('Error: Incorrect formal expression produced')

    if cmp_NFA(_tokenizer['NFA'], tokenizer['NFA']):
      raise ValueError('Error: Incorrect NFA produced')

    if cmp_DFA(_tokenizer['DFA'], tokenizer['DFA']):
      raise ValueError('Error: Incorrect DFA produced')

    if cmp_DFA(_tokenizer['min DFA'], tokenizer['min DFA']):
      raise ValueError('Error: Incorrect minimized DFA produced')

  print "ALL SCANNER TESTS PASSED!"
