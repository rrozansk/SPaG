################################################################################
# During Lexical Analysis the Lexer/Scanner recognizes regular expressions as
# corresponding token types. These tokens are then sent to the parser.
# Tokens have a type and value, but can also have character and line number
# information as well. White sapce tokens and comments can be discarded
# in this phase.
# 
# Lexical Analysis is usually called by the parser as a subroutine, each time a
# new token is needed, but it may also read the entire stream and hand it over as
# well.
# 
# The difference between lexers and parser is that a lexer reconizes regular
# grammars/expressions, while parser recognize context free grammars. The main
# difference is regular grammars can be converted into NFA with epsilon prodcutions
# using thompsons algorithm, and then used to construct a corresponding DFA using
# subset construction. After this is completed it can further be minimized.
# Context free grammars can be converted into PDA's, which require a stack, but
# they are also more powerful than regular grammars since they can properly deal
# with recursion.
# 
# NOTE: with little changes this class could easily become a regular expression 
# class. This is due to thomspons algorithm and NFA's equivalence to DFA's which
# is already being taken advantage of here. The resulting regular expression
# recognizer will run pretty performantly for ANY regular expression!
################################################################################

class Scanner(object):

  name = None   # name of scanner for function name upon calling output()
  regexps = {}  # dictionary of token -> (regular expression, minimized DFA)
  scanner = None


  def __init__(self, name):
    self.name = name


  # TODO
  def __valid__(self, regexp):
    pass


  # converts regexps to NFA with epsilon productions using thompsons algorithm
  # TODO
  def __NFA__(self, regexp):
    if len(regexp) == 0:
      return None


  # converts the NFA to DFA using subset construction
  # TODO
  def __DFA__(self, NFA):
    return None


  # minimizes the DFA
  # TODO
  def __minimize__(self, DFA):
    return None


  def token(self, name, regexp):
    if name is None or regexp is None:
      return False

    if not self.__valid__(regexp):
      return False
    
    regexps[name] = (regexp, __minimize__(__DFA__(__NFA__(regexp))))
    return True

  # we need to merge all rules/machines together to form a regexp like -> (...)|(...)|...
  # however, that is not valid since | (union) can only take 2 things!
  # TODO
  def make(self):
    scanner = None # make the scanner 

    self.Scanner = scanner

    return True


if __name__ == '__main__':
  scanner = Scanner("Test Scanner")

  # common language tokens
  if not scanner.token("integer",    "[regexp]"): print "invalid integer rule"
  if not scanner.token("float",      "[regexp]"): print "invalid float rule"
  if not scanner.token("boolean",    "[regexp]"): print "invalid boolean rule"
  if not scanner.token("character",  "[regexp]"): print "invalid character rule"
  if not scanner.token("string",     "[regexp]"): print "invalid string rule"
  if not scanner.token("space",      "[regexp]"): print "invalid space rule"
  if not scanner.token("comment",    "[regexp]"): print "invalid comment rule"

  graph = scanner.make() # FIXME: return a graph from make??

  # TODO: write some tests here...  ??
