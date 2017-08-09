################################################################################
# During Lexical Analysis the Lexer/Scanner recognizes regular expressions as
# corresponding token types. These tokens are what is sent to the parser.
# Tokens have a type and value, but can also have character and line number
# information in them as well. White sapce tokens and comments can be discarded
# in this phase as well.
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
################################################################################

class Scanner(object):

  name = None
  regexps = []


  def __init__(name):
    self.name = name


  def __valid__(regexp):
    pass


  def addToken(name, regexp):
    if name is None or regexp is None:
      return False

    if not __valid__(regexp):
      return False
    
    regeps.append((name, regexp))
    return True


  # converts regexps to NFA with epsilon productions using thompsons algorithm
  def NFA(self):
    if len(regexp) == 0:
      return None


  # converts the NFA to DFA using subset construction and then minimizes the DFA
  def DFA(self):
    if len(regexp) == 0:
      return None

if __name__ == '__main__':
  scanner = Scanner("Test Scanner")

  if not scanner.addToken("integer",    "[regexp]"): print "invalid integer rule"
  if not scanner.addToken("float",      "[regexp]"): print "invalid float rule"
  if not scanner.addToken("boolean",    "[regexp]"): print "invalid boolean rule"
  if not scanner.addToken("character",  "[regexp]"): print "invalid character rule"
  if not scanner.addToken("string",     "[regexp]"): print "invalid string rule"
  if not scanner.addToken("identifier", "[regexp]"): print "invalid identifier rule"
  if not scanner.addToken("dividor",    "[regexp]"): print "invalid dividor rule"
  if not scanner.addToken("space",      "[regexp]"): print "invalid space rule"
  if not scanner.addToken("comment",    "[regexp]"): print "invalid comment rule"

  NFA = scanner.NFA()

  DFA = scanner.DFA()
