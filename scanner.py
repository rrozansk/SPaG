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

class RegularGrammar(object):


  name = None      # name of scanner
  regexps = {}     # token dictionary -> (regexp, minimized DFA)


  def __init__(self, name):
    self.name = name


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
    if not (name is None or regexp is None):
      regexps[name] = (regexp, __minimize__(__DFA__(__NFA__(regexp))))

  # TODO make NFA with epsilon transitions to all token DFA's then do the
  # process again of nfa->dfa->minimize
  def make(self):
    tokenizer = None # single minimized DFA for all tokens

    #regexps[name] = (regexp, __minimize__(__DFA__(__NFA__(regexp))))

    return self.regexps


if __name__ == '__main__':
  scanner = RegularGrammar("Test Scanner")

  scanner.token("integer",    "[regexp]")
  scanner.token("float",      "[regexp]")
  scanner.token("boolean",    "[regexp]")
  scanner.token("character",  "[regexp]")
  scanner.token("string",     "[regexp]")
  scanner.token("space",      "[regexp]")
  scanner.token("comment",    "[regexp]")

  tokenizer = scanner.make()

  passed = True

  #TODO: asset the tokenizer (minimized DFA as a graph) is what i think it should be

  if passed:
    print "PARSER TEST PASSED!"
  else:
    print "PARSER TEST FAILED..."
