"""
 scanner.py includes the implementation and testing of RegularGrammar objects.

 The RegularGrammar object represents a group of formal regular expressions
 which can be programatically transformed into a minimal DFA.

 The entire transformation on the input can be visualized as:

   regular expression => epsilon NFA => DFA => minimal DFA

 The final DFA produced will have a complete delta (transition) function and
 will include an extra sink/error state to absorb all invalid input if needed.

 Regular expressions must be specified following these guidelines:
    - only printable ascii characters (33-126) and spaces are supported
    - supported operators:
        |                (union -> choice -> either or)
        ?                (question -> choice -> 1 or none)
        .                (concatenation -> combine)
        *                (kleene star -> repitition >= 0)
        +                (plus -> repitition >= 1)
        ()               (grouping -> disambiguation -> any expression)
        [ab]             (character class -> choice -> any specified char)
        [a-c] or [c-a]  (character range -> choice -> any char between the two)
        [^ab] or [^a-c] (character negation -> choice -> all but the specified)
        NOTES: '^' is required to come first after the bracket for negation.
               If alone ([^]) it is translated as all alphabet characters.
               It is still legal for character ranges as well ([b-^] and
               negated as [^^-b]). Note that the reverse range was needed. If
               the first character is a '^' it will always mean negation! If a
               single '^' is wanted then there is no need to use a class/range.
               Classes and ranges can be combined between the same set of
               brackets ([abc-z]), even multiple times if wanted/needed. Due to
               this though the '-' char must come as the last character in the
               class if the literal is wanted. For literal right brackets an
               escape is needed if mentioned ([\]]). All other characters are
               treated as literals.
    - concat can be either implicit or explicit
    - supported escape sequences:
        operator literals -> \?, \*, \., \+, \|
        grouping literals -> \(, \), \[, \]
        whitespace literals -> \s, \t, \n, \r, \f, \v

 Testing is implemented in a table driven fashion using the black box method.
 The test may be run at the command line with the following invocation:

   $ python scanner.py

 If all tests passed no output will be produced. In the event of a failure a
 ValueError is thrown with the appropriate error/failure message. Both positive
 and negative tests cases are extensively tested.
"""
from uuid import uuid4
from string import printable
from copy import deepcopy


class RegularGrammar(object):
    """
    RegularGrammar represents a collection of formal regular expressions which
    can be programatically transformed/compiled into a minmal DFA.
    """

    # Map internal representation of operators -> literals
    _literals = dict(enumerate('*|.+?()[]'))

    # Map operator literals -> internal representation
    _operators = {v:k for k,v in _literals.items()}

    # Set of acceptable input characters (printable ascii) including:
    # uppercase, lowercase, digits, punctuation, whitespace
    _characters = set(printable)

    # Operator precedence for the shunting yard algorithm.
    # (higher binds tighter)
    _precedence = {
        _operators['(']: (3, None),
        _operators[')']: (3, None),
        _operators['*']: (2, False),  # right-associative
        _operators['+']: (2, False),  # right-associative
        _operators['?']: (2, False),  # right-associative
        _operators['.']: (1, True),   # left-associative
        _operators['|']: (0, True),   # left-associative
    }

    _name   = None
    _exprs  = None
    _states = None
    _alphas = None
    _deltas = None
    _starts = None
    _finals = None

    def __init__(self, name, expressions):
        """
        Attempt to initialize a RegularGrammar object with the specified name,
        recognizing the given expressions. Expr's have a type/name/descriptor
        and an associated pattern/regular expression. If creation is
        unsuccessful a value error will be thrown, otherwise the results can be
        queried through the API provided below.

        Type: string x dict[string]string -> None | raise ValueError
        """
        if type(name) is not str:
            raise ValueError('Invalid Input: name must be a string')

        self._name = name

        if type(expressions) is not dict:
            raise ValueError('Invalid Input: expressions must be a dictionary')

        _pattern = ''
        self._exprs = dict()

        for name, pattern in expressions.items():
            if type(name) is not str:
                raise ValueError('Invalid Input: name must be a string')

            if type(pattern) is not str:
                raise ValueError('Invalid Input: pattern must be a string')

            self._exprs[name] = pattern
            _pattern += '|(' + pattern + ')'

        _pattern = _pattern[1:]

        expr = self._scan(_pattern)
        expr = self._expand_char_class_range(expr)
        expr = self._expand_concat(expr)
        expr = self._shunt(expr)

        nfa = self._NFA(expr)

        dfa = self._DFA(nfa)
        dfa = self._total(dfa)
        dfa = self._Hopcroft(dfa)

        Q, V, T, S, F = self._alpha(dfa)

        self._states = Q
        self._alphas = V
        self._deltas = T
        self._start = S
        self._finals = F

    def name(self):
        """
        Get the name of the Regular Grammar.

        Type: None -> string
        """
        return deepcopy(self._name)

    def expressions(self):
        """
        Get the patterns recognized by the Regular Grammar.

        Type: None -> dict[string]string
        """
        return deepcopy(self._exprs)

    def states(self):
        """
        Get the states in the grammars equivalent minimal DFA.

        Type: None -> set
        """
        return deepcopy(self._states)

    def alphabet(self):
        """
        Get the alphabet of characters recognized by the grammars DFA.

        Type: None -> set
        """
        return deepcopy(self._alphas)

    def transitions(self):
        """
        Get the state transitions defining the grammars DFA.

        Type: None -> dict, dict, list x list 
        """
        return deepcopy(self._deltas)

    def start(self):
        """
        Get the start state of the grammars DFA.

        Type: None -> string
        """
        return deepcopy(self._start)

    def accepting(self):
        """
        Get all accepting states of the grammars DFA.

        Type: None -> set
        """
        return deepcopy(self._finals)

    def _scan(self, expr):
        """
        Convert an external representation of a token (regular expression) to
        an internal one. Ensures all characters and escape sequences are valid.

        Character conversions:
          meta -> internal representation (integer enum)
          escaped meta -> character
          escaped escape -> escape
          escaped whitespace -> whitespace

        Runtime: O(n) - linear to the length of expr
        Type: string -> list | raise ValueError
        """
        output = []
        escape = False
        for char in expr:
            if escape:
                escape = False
                if char in self._operators: output.append(char)
                elif char == '\\': output.append('\\')
                elif char == 's': output.append(' ')
                elif char == 't': output.append('\t')
                elif char == 'n': output.append('\n')
                elif char == 'r': output.append('\r')
                elif char == 'f': output.append('\f')
                elif char == 'v': output.append('\v')
                else: raise ValueError('Error: invalid escape seq: \\' + char)
            else:
                if char == '\\': escape = True
                elif char in self._operators: output.append(self._operators[char])
                elif char in self._characters: output.append(char)
                else: raise ValueError('Error: unrecognized character: ' + char)
        if escape:
            raise ValueError('Error: empty escape sequence')
        return output

    def _expand_char_class_range(self, expr):
        """
        Expand the internal representation of the expression so that
        character classes and ranges are eliminated.

        Runtime: O(n) - linear to the length of expr
        Type: list -> list | raise ValueError
        """
        output, literals = [], []
        expansion, negation, prange = False, False, False
        for char in expr:
            if char == self._operators['['] and not expansion:
                expansion = True
            elif char == self._operators[']']:
                if not expansion:
                    raise ValueError('Error: Invalid character class/range; no start')
                expansion = False
                if prange:
                    prange = False
                    literals.append('-')
                if negation:
                    negation = False
                    literals = list(self._characters - set(literals))
                if literals:
                    literals = list(set(literals))
                    output.append(self._operators['('])
                    while literals:
                        output.append(literals.pop())
                        output.append(self._operators['|'])
                    output[-1] = self._operators[')']
            elif not expansion:
                output.append(char)
            elif char == '^' and not literals and not negation:
                negation = True
            elif char == '-' and literals and not prange:
                prange = True
            elif prange:
                prange = False
                _char = literals.pop()
                literals.extend(map(chr, range(ord(min(_char, char)), ord(max(_char, char))+1)))
            else:
                literals.append(self._literals.get(char, char))
        if expansion:
            raise ValueError('Error: character class/range end not specified')
        return output

    def _expand_concat(self, expr):
        """
        Expand the internal representation of the expression so that
        concatentation is explicit throughout.

        Runtime: O(n) - linear to the length of expr
        Type: list -> list
        """
        output = []
        for elem in expr:
            if output and \
               output[-1] != self._operators['('] and \
               output[-1] != self._operators['|'] and \
               output[-1] != self._operators['.'] and \
               (elem == self._operators['('] or elem in self._characters):
                output.append(self._operators['.'])
            output.append(elem)
        return output

    def _shunt(self, expr):
        """
        Convert the input expression to be entirely in postfix notation (RPN;
        Reverse Polish Notation) allowing all parenthesis to be dropped.
        Adapted from Dijkstra's Shunting yard algorithm which can be viewed
        @https://en.wikipedia.org/wiki/Shunting-yard_algorithm.

        Runtime: O(n) - linear to the length of expr
        Type: list -> list | raise ValueError
        """
        stack, queue = [], []  # operators, output expression

        for token in expr:
            if token in self._characters:
                queue.append(token)
            elif token == self._operators['(']:
                stack.append(self._operators['('])
            elif token == self._operators[')']:
                while stack and stack[-1] != self._operators['(']:
                    queue.append(stack.pop())
                if not stack:
                    raise ValueError('Error: unbalanced parenthesis')
                stack.pop()
            elif token in self._precedence:
                while stack and stack[-1] != self._operators['('] and\
                      self._precedence[token][0] <= \
                      self._precedence[stack[-1]][0]\
                      and self._precedence[token][1]:  # left-associative?
                    queue.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError('Error: invalid input in shuting yard')

        while stack:
            token = stack.pop()
            if token == self._operators['('] or token == self._operators[')']:
                raise ValueError('Error: unbalanced parenthesis')
            queue.append(token)

        return queue

    def _state(self):
        """
        Generate a new universally unique state name/label.

        Runtime: O(1) - constant
        Type: None -> string
        """
        return str(uuid4())

    def _NFA(self, expr):
        """
        Attempt to convert an internal representation of a regular expression
        in RPN to an epsilon NFA. Operators handled: union |, kleene star *,
        concatenation ., literals, and syntax extensions kleene plus + and
        choice ?. Adapted to a iterative stacked based evaluation algorithm
        (standard RPN evaluation algorithm) from thompson construction as
        described in section 4.1 in 'A taxonomy of finite automata construction
        algorithms' by Bruce Watson,
        located @http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf

        Runtime: O(n) - linear to the length of expr
        Type: list -> set x set x set x dict x string x string
        """
        Q = set()   # states
        V = set()   # input symbols (alphabet)
        T = set()   # transition relation: T in P(Q x V x Q)
        E = dict()  # e-transition relation: E in P(Q x Q)
        S = None    # start state S in Q
        F = None    # accepting state F in Q

        def e_update(s, f):
            E[s] = E.get(s, set())
            E[s].add(f)

        stk = []  # NFA machine stk
        for token in expr:
            if token in self._characters:
                S, F = self._state(), self._state()
                V.add(token)
                T.add((S, token, F))
            elif token == self._operators['.']:
                if len(stk) < 2:
                    raise ValueError('Error: not enough args to op .')
                p, F = stk.pop()
                S, q = stk.pop()
                e_update(q, p)
            elif token == self._operators['|']:
                if len(stk) < 2:
                    raise ValueError('Error: not enough args to op |')
                p, q = stk.pop()
                r, t = stk.pop()
                S, F = self._state(), self._state()
                e_update(S, p)
                e_update(S, r)
                e_update(q, F)
                e_update(t, F)
            elif token == self._operators['*']:
                if len(stk) < 1:
                    raise ValueError('Error: not enough args to op *')
                p, q = stk.pop()
                S, F = self._state(), self._state()
                e_update(S, p)
                e_update(q, p)
                e_update(q, F)
                e_update(S, F)
            elif token == self._operators['+']:
                if len(stk) < 1:
                    raise ValueError('Error: not enough args to op +')
                p, q = stk.pop()
                S, F = self._state(), self._state()
                e_update(S, p)
                e_update(q, p)
                e_update(q, F)
            elif token == self._operators['?']:
                if len(stk) < 1:
                    raise ValueError('Error: not enough args to op ?')
                p, q = stk.pop()
                S, F = self._state(), self._state()
                e_update(S, p)
                e_update(S, F)
                e_update(q, F)
            else:
                raise ValueError('Error: invalid input in NFA construction')
            Q.update([S, F])
            stk.append((S, F))

        if len(stk) != 1:
            raise ValueError('Error: invalid expression')
        S, F = stk.pop()
        return Q, V, T, E, S, F

    def _e_closure(self, q, E, cache):
        """
        Find the epsilon closure of state q and epsilon transitions E. A cache
        is utilized to speed things up for repeated invocations. Stated in set
        notation: { q' | q ->*e q' }, from a given start state q find all
        states q' which are reachable using only epsilon transitions, handling
        cycles appropriately.

        Runtime: O(n) - linear in the number of epsilon transitions
        Type: string x dict[string]set x dict[string]set -> set
        """
        if q in cache:
            return cache[q]

        cache[q] = closure = set()
        explore = set([q])
        while explore:
            q = explore.pop()
            if q not in closure:
                closure.add(q)
                # perform a single step: { q' | q ->e q' }
                explore.update(E.get(q, set()))

        return closure

    def _DFA(self, eNFA):
        """
        Convert the epsilon NFA to a DFA using subset construction and
        e-closure conversion. Only states wich are reachable from the start
        state are considered. This results in a minimized DFA with reguard to
        reachable states, but not with reguard to nondistinguishable states.

        Runtime: O(2^n) - exponential in the number of states
        Type: set x set x set x dict[string]set x string x string
                -> set x set x set x string x set
        """
        Q, V, T, E, S, F = eNFA

        cache = {}
        Sp = frozenset(self._e_closure(S, E, cache))
        Qp, Fp, Tp, explore = set(), set(), set(), set([Sp])
        while explore:
            q = explore.pop()  # DFA state; set of NFA states
            if q not in Qp:
                Qp.add(q)
                if F in q:
                    Fp.add(q)
                qps = {}
                for t in T:
                    if t[0] in q:
                        qp = qps[t[1]] = qps.get(t[1], set())
                        qp.update(self._e_closure(t[2], E, cache))
                for a, qp in qps.items():
                    qp = frozenset(qp)
                    explore.add(qp)
                    Tp.add((q, a, qp))

        return frozenset(Qp), V, Tp, Sp, frozenset(Fp)

    def _total(self, dfa):
        """
        Make the DFA's delta function total, if not already, by adding a
        sink/error state. All unspecified state transitions are then specified
        by adding a transition to the new sink/error state.

        Runtime: O(n) - linear in the number of states and transitions
        Type: set x set x set x string x set -> set x set x set x string x set
        """
        Q, V, T, S, F = dfa

        q_err = self._state()

        if len(T) != len(Q) * len(V):
            Q = Q | frozenset([q_err])

        states = {v:k for k,v in enumerate(Q)}
        symbols = {v:k for k,v in enumerate(V)}
        table = [[q_err for _ in states] for _ in symbols]
        for (state, symbol, dest) in T:
            table[symbols[symbol]][states[state]] = dest

        return Q, V, (states, symbols, table), S, F

    def _Hopcroft(self, dfa):
        """
        Minimize the DFA with reguard to nondistinguishable states using
        hopcrafts algorithm, which merges states together based on partition
        refinement.

        Runtime: O(ns log n) - linear log (n=number states; s=alphabet size)
        Type: set x set x set x set x set -> set x set x set x set x set
        """
        Q, V, (states, symbols, T), S, F = dfa

        P = set([F, Q - F]) - set([frozenset()])  # if Q - F was empty
        W = set([F])
        while W:
            A = W.pop()
            for vIdx in symbols.values():
                X = frozenset({q for q,qIdx in states.items() if T[vIdx][qIdx] in A})
                _P = set()
                for Y in P:
                    s1 = X & Y
                    s2 = Y - X
                    if s1 and s2:
                        _P.update([s1, s2])
                        if Y in W:
                            W.remove(Y)
                            W.update([s1, s2])
                        elif len(s1) <= len(s2):
                            W.update([s1])
                        else:
                            W.update([s2])
                    else:
                        _P.add(Y)
                P = _P

        _states = dict(zip(P, range(len(P))))
        Tp = [[None for state in P] for symbol in V]
        for source in states:
            for symbol in V:
                dest = T[symbols[symbol]][states[source]]
                s1, s2 = None, None
                for part in P:
                    if source in part:
                        s1 = part
                        if s2: break
                    if dest in part:
                        s2 = part
                        if s1: break
                Tp[symbols[symbol]][_states[s1]] = s2

        Sp = None
        for part in P:
            if S in part:
                Sp = part
                break

        Fp = {part for part in P if part & F}

        return P, V, (_states, symbols, Tp), Sp, Fp

    def _alpha(self, dfa):
        """
        Perform an alpha rename on all DFA states to simplify the
        representation which the end user will consume.

        Runtime: O(n) - linear in the number of states and transitions
        Type: set x set x set x string x set -> set x set x set x string x set
        """
        Q, V, (states, symbols, table), S, F = dfa
        rename = {q: self._state() for q in Q}
        Qp = set(rename.values())
        states = {rename[state]:idx for state,idx in states.items()}
        table = [[rename[col] for col in row] for row in table]
        Fp = {rename[f] for f in F}
        Sp = rename[S]

        return Qp, V, (states, symbols, table), Sp, Fp


if __name__ == '__main__':

    TESTS = [
        {
            'name': 'Single Alpha',
            'valid': True,
            'expressions': {
                'alpha': 'a'
            },
            'DFA': {
                'Q': set(['S', 'A', 'Err']),
                'V': set('a'),
                'T': [
                    [' ', 'S', 'A',   'Err'],
                    ['a', 'A', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['A'])
            }
        },
        {
            'name': 'Explicit Concatenation',
            'valid': True,
            'expressions': {
                'concat': 'a.b'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',   'A',   'B',   'Err'],
                    ['a', 'A',   'Err', 'Err', 'Err'],
                    ['b', 'Err', 'B',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Alternation',
            'valid': True,
            'expressions': {
                'alt': 'a|b'
            },
            'DFA': {
                'Q': set(['S', 'AB', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',  'AB',  'Err'],
                    ['a', 'AB', 'Err', 'Err'],
                    ['b', 'AB', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['AB'])
            }
        },
        {
            'name': 'Kleene Star',
            'valid': True,
            'expressions': {
                'star': 'a*'
            },
            'DFA': {
                'Q': set(['A']),
                'V': set('a'),
                'T': [
                    [' ', 'A'],
                    ['a', 'A']
                ],
                'S': 'A',
                'F': set(['A'])
            }
        },
        {
            'name': 'Kleene Plus',
            'valid': True,
            'expressions': {
                'plus': 'a+'
            },
            'DFA': {
                'Q': set(['S', 'A']),
                'V': set('a'),
                'T': [
                    [' ', 'S', 'A'],
                    ['a', 'A', 'A']
                ],
                'S': 'S',
                'F': set(['A'])
            }
        },
        {
            'name': 'Choice',
            'valid': True,
            'expressions': {
                'maybe': 'a?'
            },
            'DFA': {
                'Q': set(['S', 'A', 'Err']),
                'V': set('a'),
                'T': [
                    [' ', 'S', 'A',   'Err'],
                    ['a', 'A', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['S', 'A'])
            }
        },
        {
            'name': 'Grouping',
            'valid': True,
            'expressions': {
                'group': '(a|b)*'
            },
            'DFA': {
                'Q': set(['AB*']),
                'V': set('ab'),
                'T': [
                    [' ', 'AB*'],
                    ['a', 'AB*'],
                    ['b', 'AB*']
                ],
                'S': 'AB*',
                'F': set(['AB*'])
            }
        },
        {
            'name': 'Association',
            'valid': True,
            'expressions': {
                'assoc': 'a|b*'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S', 'A',   'B',   'Err'],
                    ['a', 'A', 'Err', 'Err', 'Err'],
                    ['b', 'B', 'Err', 'B',   'Err']
                ],
                'S': 'S',
                'F': set(['S', 'A', 'B'])
            }
        },
        {
            'name': 'Operator Alpha Literals',
            'valid': True,
            'expressions': {
                'concat': '\.',
                'alt': '\|',
                'star': '\*',
                'question': '\?',
                'plus': '\+',
                'slash': '\\\\',
                'lparen': '\(',
                'rparen': '\)',
                'lbracket': '\[',
                'rbracket': '\]'
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('.|*?+\\()[]'),
                'T': [
                    [' ',  'S', 'F',   'Err'],
                    ['.',  'F', 'Err', 'Err'],
                    ['|',  'F', 'Err', 'Err'],
                    ['*',  'F', 'Err', 'Err'],
                    ['?',  'F', 'Err', 'Err'],
                    ['+',  'F', 'Err', 'Err'],
                    ['\\', 'F', 'Err', 'Err'],
                    ['(',  'F', 'Err', 'Err'],
                    [')',  'F', 'Err', 'Err'],
                    ['[',  'F', 'Err', 'Err'],
                    [']',  'F', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Implicit Concatenation Characters',
            'valid': True,
            'expressions': {
                'permutation1': 'ab',
                'permutation2': 'a(b)',
                'permutation3': '(a)b',
                'permutation4': '(a)(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',   'A',   'B',   'Err'],
                    ['a', 'A',   'Err', 'Err', 'Err'],
                    ['b', 'Err', 'B',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation Star Operator',
            'valid': True,
            'expressions': {
                'permutation1': 'a*b',
                'permutation2': 'a*(b)',
                'permutation3': '(a)*b',
                'permutation4': '(a)*(b)'
            },
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'A', 'B',   'Err'],
                    ['a', 'A', 'Err', 'Err'],
                    ['b', 'B', 'Err', 'Err']
                ],
                'S': 'A',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation Plus Operator',
            'valid': True,
            'expressions': {
                'permutation1': 'a+b',
                'permutation2': 'a+(b)',
                'permutation3': '(a)+b',
                'permutation4': '(a)+(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S',   'A', 'B',   'Err'],
                    ['a', 'A',   'A', 'Err', 'Err'],
                    ['b', 'Err', 'B', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation Question Operator',
            'valid': True,
            'expressions': {
                'permutation1': 'a?b',
                'permutation2': 'a?(b)',
                'permutation3': '(a)?b',
                'permutation4': '(a)?(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'S', 'A',   'B',   'Err'],
                    ['a', 'A', 'Err', 'Err', 'Err'],
                    ['b', 'B', 'B',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 10 - Mixed',
            'valid': True,
            'expressions': {
                'concat': 'a.bc.de'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'C', 'D', 'E', 'Err']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S',   'A',   'B',   'C',   'D',   'E',   'Err'],
                    ['a', 'A',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['b', 'Err', 'B',   'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['c', 'Err', 'Err', 'C',   'Err', 'Err', 'Err', 'Err'],
                    ['d', 'Err', 'Err', 'Err', 'D',   'Err', 'Err', 'Err'],
                    ['e', 'Err', 'Err', 'Err', 'Err', 'E',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['E'])
            }
        },
        {
            'name': 'Randomness 1',
            'valid': True,
            'expressions': {
                'random': 'a*(b|cd)*'
            },
            'DFA': {
                'Q': set(['AC', 'B', 'DE', 'Err']),
                'V': set('abcd'),
                'T': [
                    [' ', 'AC',  'B',   'DE',  'Err'],
                    ['a', 'AC',  'Err', 'Err', 'Err'],
                    ['b', 'DE',  'Err', 'DE',  'Err'],
                    ['c', 'B',   'Err', 'B',   'Err'],
                    ['d', 'Err', 'DE',  'Err', 'Err']
                ],
                'S': 'AC',
                'F': set(['AC', 'DE']),
            }
        },
        {
            'name': 'Randomness 2',
            'valid': True,
            'expressions': {
                'random': 'a?b*'
            },
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': [
                    [' ', 'A',  'B',   'Err'],
                    ['a', 'B',  'Err', 'Err'],
                    ['b', 'B',  'B',   'Err']
                ],
                'S': 'A',
                'F': set(['A', 'B'])
            }
        },
        {
            'name': 'Randomness 3',
            'valid': True,
            'expressions': {
                'random': '(a*b)|(a.bcd.e)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'A*', 'B', 'C', 'D', 'F', 'Err']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S',   'A',   'A*',  'B',   'C',   'D',   'F',   'Err'],
                    ['a', 'A',   'A*',  'A*',  'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['b', 'F',   'B',   'F',   'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['c', 'Err', 'Err', 'Err', 'C',   'Err', 'Err', 'Err', 'Err'],
                    ['d', 'Err', 'Err', 'Err', 'Err', 'D',   'Err', 'Err', 'Err'],
                    ['e', 'Err', 'Err', 'Err', 'Err', 'Err', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F', 'B'])
            }
        },
        {
            'name': 'Randomness 4',
            'valid': True,
            'expressions': {
                'random': '(foo)?(bar)+'
            },
            'DFA': {
                'Q': set(['S', 'F', 'FO', 'FOO', 'B', 'BA', 'BAR', 'Err']),
                'V': set('fobar'),
                'T': [
                    [' ', 'S',   'F',   'FO',  'FOO', 'B',   'BA',  'BAR', 'Err'],
                    ['f', 'F',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['o', 'Err', 'FO',  'FOO', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['b', 'B',   'Err', 'Err', 'B',   'Err', 'Err', 'B',   'Err'],
                    ['a', 'Err', 'Err', 'Err', 'Err', 'BA',  'Err', 'Err', 'Err'],
                    ['r', 'Err', 'Err', 'Err', 'Err', 'Err', 'BAR', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['BAR'])
            }
        },
        {
            'name': 'Forward Character Range',
            'valid': True,
            'expressions': {
                'range': '[a-c]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err'],
                    ['b', 'F',   'Err', 'Err'],
                    ['c', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Backward Character Range',
            'valid': True,
            'expressions': {
                'range': '[c-a]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err'],
                    ['b', 'F',   'Err', 'Err'],
                    ['c', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Literal Negation Character Range',
            'valid': True,
            'expressions': {
                'range': '[a-^]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('^_`a'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['^', 'F',   'Err', 'Err'],
                    ['_', 'F',   'Err', 'Err'],
                    ['`', 'F',   'Err', 'Err'],
                    ['a', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Negated Character Range',
            'valid': True,
            'expressions': {
                'range': '[^!-~]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': [
                    [' ',  'S'],
                    [' ',  'S'],
                    ['\t', 'S'],
                    ['\n', 'S'],
                    ['\r', 'S'],
                    ['\f', 'S'],
                    ['\v', 'S']
                ],
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Character Class',
            'valid': True,
            'expressions': {
                'class': '[abc]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err'],
                    ['b', 'F',   'Err', 'Err'],
                    ['c', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Character Class with Copies',
            'valid': True,
            'expressions': {
                'class': '[aaa]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('a'),
                'T': [
                    [' ', 'S',   'F',   'Err'],
                    ['a', 'F',   'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Character Class with Literal Right Bracket',
            'valid': True,
            'expressions': {
                'class': '[\]]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(']'),
                'T': [
                    [' ', 'S'],
                    [']', 'S']
                ],
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Negated Character Class',
            'valid': True,
            'expressions': {
                'class': '[^^!"#$%&\'()*+,./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\\]_`abcdefghijklmnopqrstuvwxyz{|}~-]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': [
                    [' ',  'S'],
                    [' ',  'S'],
                    ['\t', 'S'],
                    ['\n', 'S'],
                    ['\r', 'S'],
                    ['\f', 'S'],
                    ['\v', 'S']
                ],
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Character Class Range Combo',
            'valid': True,
            'expressions': {
                'class': '[abc-e]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S'],
                    ['a', 'S'],
                    ['b', 'S'],
                    ['c', 'S'],
                    ['d', 'S'],
                    ['e', 'S']
                ],
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Character Range Class Combo',
            'valid': True,
            'expressions': {
                'class': '[a-cde]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set('abcde'),
                'T': [
                    [' ', 'S'],
                    ['a', 'S'],
                    ['b', 'S'],
                    ['c', 'S'],
                    ['d', 'S'],
                    ['e', 'S']
                ],
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Integer',
            'valid': True,
            'expressions': {
                'int': "0|([-+]?[1-9][0-9]*)",
            },
            'DFA': {
                'Q': set(['S', 'Zero', 'Sign', 'Int', 'Err']),
                'V': set('+-0123456789'),
                'T': [
                    [' ', 'S',    'Zero', 'Sign', 'Int', 'Err'],
                    ['+', 'Sign', 'Err',  'Err',  'Err', 'Err'],
                    ['-', 'Sign', 'Err',  'Err',  'Err', 'Err'],
                    ['0', 'Zero', 'Err',  'Err',  'Int', 'Err'],
                    ['1', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['2', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['3', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['4', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['5', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['6', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['7', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['8', 'Int',  'Err',  'Int',  'Int', 'Err'],
                    ['9', 'Int',  'Err',  'Int',  'Int', 'Err']
                ],
                'S': 'S',
                'F': set(['Zero', 'Int'])
            }
        },
        {
            'name': 'Float',
            'valid': True,
            'expressions': {
                'float': '[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?',
            },
            'DFA': {
                'Q': set(['S', 'WholePart', 'ExpPart', 'FractionPart', 'eSignum', 'Sigfrac', 'Sigexp', 'Signum', 'Err']),
                'V': set('+-.0123456789eE'),
                'T': [
                    [' ', 'S',         'WholePart', 'ExpPart', 'FractionPart', 'eSignum', 'Sigfrac',      'Sigexp',  'Signum',    'Err'],
                    ['+', 'Signum',    'Err',       'Err',     'Err',          'Err',     'Err',          'eSignum', 'Err',       'Err'],
                    ['-', 'Signum',    'Err',       'Err',     'Err',          'Err',     'Err',          'eSignum', 'Err',       'Err'],
                    ['.', 'Sigfrac',   'Sigfrac',   'Err',     'Err',          'Err',     'Err',          'Err',     'Sigfrac',   'Err'],
                    ['0', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['1', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['2', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['3', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['4', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['5', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['6', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['7', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['8', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['9', 'WholePart', 'WholePart', 'ExpPart', 'FractionPart', 'ExpPart', 'FractionPart', 'ExpPart', 'WholePart', 'Err'],
                    ['E', 'Err',       'Sigexp',    'Err',     'Sigexp',       'Err',     'Err',          'Err',     'Err',       'Err'],
                    ['e', 'Err',       'Sigexp',    'Err',     'Sigexp',       'Err',     'Err',          'Err',     'Err',       'Err']
                ],
                'S': 'S',
                'F': set(['WholePart', 'ExpPart', 'FractionPart'])
            }
        },
        {
            'name': 'White Space',
            'valid': True,
            'expressions': {
                'white': '( |\t|\n|\r|\f|\v)*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': [
                    [' ',  'S'],
                    [' ',  'S'],
                    ['\t', 'S'],
                    ['\n', 'S'],
                    ['\r', 'S'],
                    ['\f', 'S'],
                    ['\v', 'S']
                ],
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Boolean',
            'valid': True,
            'expressions': {
                'bool': '(true)|(false)',
            },
            'DFA': {
                'Q': set(['S', 'T', 'R', 'F', 'A', 'L', 'US', 'E', 'Err']),
                'V': set('truefals'),
                'T': [
                    [' ', 'S',   'T',   'R',   'F',   'A',   'L',   'US',  'E',   'Err'],
                    ['t', 'T',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['r', 'Err', 'R',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['u', 'Err', 'Err', 'US',  'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['e', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'E',   'Err', 'Err'],
                    ['f', 'F',   'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['a', 'Err', 'Err', 'Err', 'A',   'Err', 'Err', 'Err', 'Err', 'Err'],
                    ['l', 'Err', 'Err', 'Err', 'Err', 'L',   'Err', 'Err', 'Err', 'Err'],
                    ['s', 'Err', 'Err', 'Err', 'Err', 'Err', 'US',  'Err', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['E'])
            }
        },
        {
            'name': 'Line Comment',
            'valid': True,
            'expressions': {
                'comment': '(#|;)[^\n]*\n',
            },
            'DFA': {
                'Q': set(['S', '_', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'S',   '_', 'F',   'Err'],
                    ['#',  '_',   '_', 'Err', 'Err'],
                    [';',  '_',   '_', 'Err', 'Err'],
                    ['\n', 'Err', 'F', 'Err', 'Err'],
                    ['0',  'Err', '_', 'Err', 'Err'],
                    ['1',  'Err', '_', 'Err', 'Err'],
                    ['2',  'Err', '_', 'Err', 'Err'],
                    ['3',  'Err', '_', 'Err', 'Err'],
                    ['4',  'Err', '_', 'Err', 'Err'],
                    ['5',  'Err', '_', 'Err', 'Err'],
                    ['6',  'Err', '_', 'Err', 'Err'],
                    ['7',  'Err', '_', 'Err', 'Err'],
                    ['8',  'Err', '_', 'Err', 'Err'],
                    ['9',  'Err', '_', 'Err', 'Err'],
                    [' ',  'Err', '_', 'Err', 'Err'],
                    ['\t', 'Err', '_', 'Err', 'Err'],
                    ['\v', 'Err', '_', 'Err', 'Err'],
                    ['\f', 'Err', '_', 'Err', 'Err'],
                    ['\r', 'Err', '_', 'Err', 'Err'],
                    ['a',  'Err', '_', 'Err', 'Err'],
                    ['b',  'Err', '_', 'Err', 'Err'],
                    ['c',  'Err', '_', 'Err', 'Err'],
                    ['d',  'Err', '_', 'Err', 'Err'],
                    ['e',  'Err', '_', 'Err', 'Err'],
                    ['f',  'Err', '_', 'Err', 'Err'],
                    ['g',  'Err', '_', 'Err', 'Err'],
                    ['h',  'Err', '_', 'Err', 'Err'],
                    ['i',  'Err', '_', 'Err', 'Err'],
                    ['j',  'Err', '_', 'Err', 'Err'],
                    ['k',  'Err', '_', 'Err', 'Err'],
                    ['l',  'Err', '_', 'Err', 'Err'],
                    ['m',  'Err', '_', 'Err', 'Err'],
                    ['n',  'Err', '_', 'Err', 'Err'],
                    ['o',  'Err', '_', 'Err', 'Err'],
                    ['p',  'Err', '_', 'Err', 'Err'],
                    ['q',  'Err', '_', 'Err', 'Err'],
                    ['r',  'Err', '_', 'Err', 'Err'],
                    ['s',  'Err', '_', 'Err', 'Err'],
                    ['t',  'Err', '_', 'Err', 'Err'],
                    ['u',  'Err', '_', 'Err', 'Err'],
                    ['v',  'Err', '_', 'Err', 'Err'],
                    ['w',  'Err', '_', 'Err', 'Err'],
                    ['x',  'Err', '_', 'Err', 'Err'],
                    ['y',  'Err', '_', 'Err', 'Err'],
                    ['z',  'Err', '_', 'Err', 'Err'],
                    ['A',  'Err', '_', 'Err', 'Err'],
                    ['B',  'Err', '_', 'Err', 'Err'],
                    ['C',  'Err', '_', 'Err', 'Err'],
                    ['D',  'Err', '_', 'Err', 'Err'],
                    ['E',  'Err', '_', 'Err', 'Err'],
                    ['F',  'Err', '_', 'Err', 'Err'],
                    ['G',  'Err', '_', 'Err', 'Err'],
                    ['H',  'Err', '_', 'Err', 'Err'],
                    ['I',  'Err', '_', 'Err', 'Err'],
                    ['J',  'Err', '_', 'Err', 'Err'],
                    ['K',  'Err', '_', 'Err', 'Err'],
                    ['L',  'Err', '_', 'Err', 'Err'],
                    ['M',  'Err', '_', 'Err', 'Err'],
                    ['N',  'Err', '_', 'Err', 'Err'],
                    ['O',  'Err', '_', 'Err', 'Err'],
                    ['P',  'Err', '_', 'Err', 'Err'],
                    ['Q',  'Err', '_', 'Err', 'Err'],
                    ['R',  'Err', '_', 'Err', 'Err'],
                    ['S',  'Err', '_', 'Err', 'Err'],
                    ['T',  'Err', '_', 'Err', 'Err'],
                    ['U',  'Err', '_', 'Err', 'Err'],
                    ['V',  'Err', '_', 'Err', 'Err'],
                    ['W',  'Err', '_', 'Err', 'Err'],
                    ['X',  'Err', '_', 'Err', 'Err'],
                    ['Y',  'Err', '_', 'Err', 'Err'],
                    ['Z',  'Err', '_', 'Err', 'Err'],
                    ['!',  'Err', '_', 'Err', 'Err'],
                    ['"',  'Err', '_', 'Err', 'Err'],
                    ['$',  'Err', '_', 'Err', 'Err'],
                    ['%',  'Err', '_', 'Err', 'Err'],
                    ['&',  'Err', '_', 'Err', 'Err'],
                    ['\'', 'Err', '_', 'Err', 'Err'],
                    ['(',  'Err', '_', 'Err', 'Err'],
                    [')',  'Err', '_', 'Err', 'Err'],
                    ['*',  'Err', '_', 'Err', 'Err'],
                    ['+',  'Err', '_', 'Err', 'Err'],
                    [',',  'Err', '_', 'Err', 'Err'],
                    ['-',  'Err', '_', 'Err', 'Err'],
                    ['.',  'Err', '_', 'Err', 'Err'],
                    ['/',  'Err', '_', 'Err', 'Err'],
                    [':',  'Err', '_', 'Err', 'Err'],
                    ['<',  'Err', '_', 'Err', 'Err'],
                    ['=',  'Err', '_', 'Err', 'Err'],
                    ['>',  'Err', '_', 'Err', 'Err'],
                    ['?',  'Err', '_', 'Err', 'Err'],
                    ['@',  'Err', '_', 'Err', 'Err'],
                    ['[',  'Err', '_', 'Err', 'Err'],
                    ['\\', 'Err', '_', 'Err', 'Err'],
                    [']',  'Err', '_', 'Err', 'Err'],
                    ['^',  'Err', '_', 'Err', 'Err'],
                    ['_',  'Err', '_', 'Err', 'Err'],
                    ['`',  'Err', '_', 'Err', 'Err'],
                    ['{',  'Err', '_', 'Err', 'Err'],
                    ['|',  'Err', '_', 'Err', 'Err'],
                    ['}',  'Err', '_', 'Err', 'Err'],
                    ['~',  'Err', '_', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Block Comment',
            'valid': True,
            'expressions': {
                'comment': '/[*][^]*[*]/',
            },
            'DFA': {
                'Q': set(['BEGIN', 'SINK', 'FSLASH', 'SIGEND', 'END', 'ERR']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'BEGIN',  'SINK',   'FSLASH', 'SIGEND', 'END',    'ERR'],
                    ['/',  'FSLASH', 'SINK',   'ERR',    'END',    'SINK',   'ERR'],
                    ['*',  'ERR',    'SIGEND', 'SINK',   'SIGEND', 'SIGEND', 'ERR'],
                    ['#',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [';',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\n', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['0',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['1',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['2',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['3',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['4',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['5',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['6',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['7',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['8',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['9',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [' ',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\t', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\v', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\f', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\r', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['a',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['b',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['c',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['d',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['e',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['f',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['g',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['h',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['i',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['j',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['k',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['l',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['m',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['n',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['o',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['p',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['q',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['r',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['s',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['t',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['u',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['v',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['w',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['x',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['y',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['z',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['A',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['B',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['C',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['D',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['E',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['F',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['G',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['H',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['I',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['J',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['K',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['L',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['M',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['N',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['O',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['P',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['Q',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['R',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['S',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['T',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['U',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['V',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['W',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['X',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['Y',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['Z',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['!',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['"',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['$',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['%',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['&',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\'', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['(',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [')',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['+',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [',',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['-',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['.',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [':',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['<',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['=',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['>',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['?',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['@',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['[',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['\\', 'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    [']',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['^',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['_',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['`',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['{',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['|',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['}',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR'],
                    ['~',  'ERR',    'SINK',   'ERR',    'SINK',   'SINK',   'ERR']
                ],
                'S': 'BEGIN',
                'F': set(['END'])
            }
        },
        {
            'name': 'Character',
            'valid': True,
            'expressions': {
                'char': "'[^]'",
            },
            'DFA': {
                'Q': set(['S', '_1', '_2', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'S',   '_1', '_2',  'F',   'Err'],
                    ['#',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [';',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\n', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['0',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['1',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['2',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['3',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['4',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['5',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['6',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['7',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['8',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['9',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [' ',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\t', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\v', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\f', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\r', 'Err', '_2', 'Err', 'Err', 'Err'],
                    ['a',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['b',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['c',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['d',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['e',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['f',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['g',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['h',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['i',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['j',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['k',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['l',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['m',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['n',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['o',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['p',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['q',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['r',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['s',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['t',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['u',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['v',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['w',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['x',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['y',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['z',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['A',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['B',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['C',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['D',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['E',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['F',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['G',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['H',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['I',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['J',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['K',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['L',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['M',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['N',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['O',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['P',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['Q',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['R',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['S',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['T',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['U',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['V',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['W',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['X',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['Y',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['Z',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['!',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['"',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['$',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['%',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['&',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\'', '_1',  '_2', 'F',   'Err', 'Err'],
                    ['(',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [')',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['*',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['+',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [',',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['-',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['.',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['/',  'Err', '_2', 'Err', 'Err', 'Err'],
                    [':',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['<',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['=',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['>',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['?',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['@',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['[',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['\\', 'Err', '_2', 'Err', 'Err', 'Err'],
                    [']',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['^',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['_',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['`',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['{',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['|',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['}',  'Err', '_2', 'Err', 'Err', 'Err'],
                    ['~',  'Err', '_2', 'Err', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'String',
            'valid': True,
            'expressions': {
                'str': '"[^"]*"',
            },
            'DFA': {
                'Q': set(['S', '_', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'),
                'T': [
                    [' ',  'S',   '_', 'F',   'Err'],
                    ['#',  'Err', '_', 'Err', 'Err'],
                    [';',  'Err', '_', 'Err', 'Err'],
                    ['\n', 'Err', '_', 'Err', 'Err'],
                    ['0',  'Err', '_', 'Err', 'Err'],
                    ['1',  'Err', '_', 'Err', 'Err'],
                    ['2',  'Err', '_', 'Err', 'Err'],
                    ['3',  'Err', '_', 'Err', 'Err'],
                    ['4',  'Err', '_', 'Err', 'Err'],
                    ['5',  'Err', '_', 'Err', 'Err'],
                    ['6',  'Err', '_', 'Err', 'Err'],
                    ['7',  'Err', '_', 'Err', 'Err'],
                    ['8',  'Err', '_', 'Err', 'Err'],
                    ['9',  'Err', '_', 'Err', 'Err'],
                    [' ',  'Err', '_', 'Err', 'Err'],
                    ['\t', 'Err', '_', 'Err', 'Err'],
                    ['\v', 'Err', '_', 'Err', 'Err'],
                    ['\f', 'Err', '_', 'Err', 'Err'],
                    ['\r', 'Err', '_', 'Err', 'Err'],
                    ['a',  'Err', '_', 'Err', 'Err'],
                    ['b',  'Err', '_', 'Err', 'Err'],
                    ['c',  'Err', '_', 'Err', 'Err'],
                    ['d',  'Err', '_', 'Err', 'Err'],
                    ['e',  'Err', '_', 'Err', 'Err'],
                    ['f',  'Err', '_', 'Err', 'Err'],
                    ['g',  'Err', '_', 'Err', 'Err'],
                    ['h',  'Err', '_', 'Err', 'Err'],
                    ['i',  'Err', '_', 'Err', 'Err'],
                    ['j',  'Err', '_', 'Err', 'Err'],
                    ['k',  'Err', '_', 'Err', 'Err'],
                    ['l',  'Err', '_', 'Err', 'Err'],
                    ['m',  'Err', '_', 'Err', 'Err'],
                    ['n',  'Err', '_', 'Err', 'Err'],
                    ['o',  'Err', '_', 'Err', 'Err'],
                    ['p',  'Err', '_', 'Err', 'Err'],
                    ['q',  'Err', '_', 'Err', 'Err'],
                    ['r',  'Err', '_', 'Err', 'Err'],
                    ['s',  'Err', '_', 'Err', 'Err'],
                    ['t',  'Err', '_', 'Err', 'Err'],
                    ['u',  'Err', '_', 'Err', 'Err'],
                    ['v',  'Err', '_', 'Err', 'Err'],
                    ['w',  'Err', '_', 'Err', 'Err'],
                    ['x',  'Err', '_', 'Err', 'Err'],
                    ['y',  'Err', '_', 'Err', 'Err'],
                    ['z',  'Err', '_', 'Err', 'Err'],
                    ['A',  'Err', '_', 'Err', 'Err'],
                    ['B',  'Err', '_', 'Err', 'Err'],
                    ['C',  'Err', '_', 'Err', 'Err'],
                    ['D',  'Err', '_', 'Err', 'Err'],
                    ['E',  'Err', '_', 'Err', 'Err'],
                    ['F',  'Err', '_', 'Err', 'Err'],
                    ['G',  'Err', '_', 'Err', 'Err'],
                    ['H',  'Err', '_', 'Err', 'Err'],
                    ['I',  'Err', '_', 'Err', 'Err'],
                    ['J',  'Err', '_', 'Err', 'Err'],
                    ['K',  'Err', '_', 'Err', 'Err'],
                    ['L',  'Err', '_', 'Err', 'Err'],
                    ['M',  'Err', '_', 'Err', 'Err'],
                    ['N',  'Err', '_', 'Err', 'Err'],
                    ['O',  'Err', '_', 'Err', 'Err'],
                    ['P',  'Err', '_', 'Err', 'Err'],
                    ['Q',  'Err', '_', 'Err', 'Err'],
                    ['R',  'Err', '_', 'Err', 'Err'],
                    ['S',  'Err', '_', 'Err', 'Err'],
                    ['T',  'Err', '_', 'Err', 'Err'],
                    ['U',  'Err', '_', 'Err', 'Err'],
                    ['V',  'Err', '_', 'Err', 'Err'],
                    ['W',  'Err', '_', 'Err', 'Err'],
                    ['X',  'Err', '_', 'Err', 'Err'],
                    ['Y',  'Err', '_', 'Err', 'Err'],
                    ['Z',  'Err', '_', 'Err', 'Err'],
                    ['!',  'Err', '_', 'Err', 'Err'],
                    ['"',  '_',   'F', 'Err', 'Err'],
                    ['$',  'Err', '_', 'Err', 'Err'],
                    ['%',  'Err', '_', 'Err', 'Err'],
                    ['&',  'Err', '_', 'Err', 'Err'],
                    ['\'', 'Err', '_', 'Err', 'Err'],
                    ['(',  'Err', '_', 'Err', 'Err'],
                    [')',  'Err', '_', 'Err', 'Err'],
                    ['*',  'Err', '_', 'Err', 'Err'],
                    ['+',  'Err', '_', 'Err', 'Err'],
                    [',',  'Err', '_', 'Err', 'Err'],
                    ['-',  'Err', '_', 'Err', 'Err'],
                    ['.',  'Err', '_', 'Err', 'Err'],
                    ['/',  'Err', '_', 'Err', 'Err'],
                    [':',  'Err', '_', 'Err', 'Err'],
                    ['<',  'Err', '_', 'Err', 'Err'],
                    ['=',  'Err', '_', 'Err', 'Err'],
                    ['>',  'Err', '_', 'Err', 'Err'],
                    ['?',  'Err', '_', 'Err', 'Err'],
                    ['@',  'Err', '_', 'Err', 'Err'],
                    ['[',  'Err', '_', 'Err', 'Err'],
                    ['\\', 'Err', '_', 'Err', 'Err'],
                    [']',  'Err', '_', 'Err', 'Err'],
                    ['^',  'Err', '_', 'Err', 'Err'],
                    ['_',  'Err', '_', 'Err', 'Err'],
                    ['`',  'Err', '_', 'Err', 'Err'],
                    ['{',  'Err', '_', 'Err', 'Err'],
                    ['|',  'Err', '_', 'Err', 'Err'],
                    ['}',  'Err', '_', 'Err', 'Err'],
                    ['~',  'Err', '_', 'Err', 'Err']
                ],
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Identifiers',
            'valid': True,
            'expressions': {
                'id': '[_a-zA-Z][_a-zA-Z0-9]*',
            },
            'DFA': {
                'Q': set(['Char', 'DigitOrChar', 'Err']),
                'V': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
                'T': [
                    [' ',  'Char',        'DigitOrChar', 'Err'],
                    ['a',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['b',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['c',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['d',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['e',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['f',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['g',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['h',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['i',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['j',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['k',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['l',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['m',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['n',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['o',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['p',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['q',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['r',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['s',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['t',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['u',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['v',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['w',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['x',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['y',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['z',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['A',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['B',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['C',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['D',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['E',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['F',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['G',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['H',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['I',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['J',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['K',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['L',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['M',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['N',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['O',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['P',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['Q',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['R',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['S',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['T',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['U',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['V',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['W',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['X',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['Y',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['Z',  'DigitOrChar', 'DigitOrChar', 'Err'],
                    ['0',  'Err',         'DigitOrChar', 'Err'],
                    ['1',  'Err',         'DigitOrChar', 'Err'],
                    ['2',  'Err',         'DigitOrChar', 'Err'],
                    ['3',  'Err',         'DigitOrChar', 'Err'],
                    ['4',  'Err',         'DigitOrChar', 'Err'],
                    ['5',  'Err',         'DigitOrChar', 'Err'],
                    ['6',  'Err',         'DigitOrChar', 'Err'],
                    ['7',  'Err',         'DigitOrChar', 'Err'],
                    ['8',  'Err',         'DigitOrChar', 'Err'],
                    ['9',  'Err',         'DigitOrChar', 'Err'],
                    ['_',  'DigitOrChar', 'DigitOrChar', 'Err']
                ],
                'S': 'Char',
                'F': set(['DigitOrChar'])
            }
        },
        {
            'name': 'Unbalanced Left Paren',
            'valid': False,
            'expressions': {
                'invalid': '(foo|bar',
            },
            'DFA': {}
        },
        {
            'name': 'Unbalanced Right Paren',
            'valid': False,
            'expressions': {
                'invalid': 'foo|bar)',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Escape Sequence',
            'valid': False,
            'expressions': {
                'invalid': '\j',
            },
            'DFA': {}
        },
        {
            'name': 'Empty Escape Sequence',
            'valid': False,
            'expressions': {
                'invalid': '\\',
            },
            'DFA': {}
        },
        {
            'name': 'Empty Expression',
            'valid': False,
            'expressions': {
                'invalid': '',
            },
            'DFA': {}
        },
        {
            'name': 'Empty Character Range/Class',
            'valid': False,
            'expressions': {
                'class/range': '[]',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Character',
            'valid': False,
            'expressions': {
                'invalid': '\x99',
            },
            'DFA': {}
        },
        {
            'name': ['Invalid Scanner Name'],
            'valid': False,
            'expressions': {
                'invalid': 'foo',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Scanner Tokens',
            'valid': False,
            'expressions': ["invalid"],
            'DFA': {}
        },
        {
            'name': 'Invalid Scanner Token Key',
            'valid': False,
            'expressions': {
                True: 'invalid',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Scanner Token Value',
            'valid': False,
            'expressions': {
                'invalid': True,
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Expression * Arity',
            'valid': False,
            'expressions': {
                'invalid': '*',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Expression + Arity',
            'valid': False,
            'expressions': {
                'invalid': '+',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Expression ? Arity',
            'valid': False,
            'expressions': {
                'invalid': '?',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Expression | Arity',
            'valid': False,
            'expressions': {
                'invalid': 'a|',
            },
            'DFA': {}
        },
        {
            'name': 'Invalid Expression . Arity',
            'valid': False,
            'expressions': {
                'invalid': 'a.',
            },
            'DFA': {}
        },
    ]

    from itertools import permutations

    for test in TESTS:
        try:
            grammar = RegularGrammar(test['name'], test['expressions'])
        except ValueError as e:
            if test['valid']:  # test type (input output)
                raise e        # Unexpected Failure (+-)
            continue           # Expected Failure   (--)

        if not test['valid']:  # Unexpected Pass    (-+)
            raise ValueError('Panic: Negative test passed without error')

        # Failure checking for:  Expected Pass      (++)

        if grammar.name() != test['name']:
            raise ValueError('Error: Incorrect DFA name returned')

        expressions = grammar.expressions()

        if len(expressions) != len(test['expressions']):
            raise ValueError('Error: Incorrect expression count in grammar')

        for name, pattern in test['expressions'].items():
            _pattern = expressions.get(name, None)
            if _pattern is None or _pattern != pattern:
                raise ValueError('Error: Incorrect token name/pattern created')

        _DFA = test['DFA']

        V = grammar.alphabet()
        if V != _DFA['V']:
            raise ValueError('Error: Incorrect alphabet produced')

        Q = grammar.states()
        if len(Q) != len(_DFA['Q']):
            raise ValueError('Error: Incorrect number of states produced')

        F = grammar.accepting()
        if len(F) != len(_DFA['F']):
            raise ValueError('Error: Incorrect number of finish states')

        state, symbol, T = grammar.transitions()
        if len(T) != len(_DFA['T'])-1 or \
           (T and len(T[0]) != len(_DFA['T'][0])-1):
            raise ValueError('Error: Incorrect number of transitions produced')

        # Check if DFA's are isomorphic by attempting to find a bijection
        # between them since they both already look very 'similar'.
        _Q = _DFA['Q']
        S = grammar.start()

        _state, _symbol, _T = dict(), dict(), list()
        if T:
            _state = {s:idx for idx,s in enumerate(_DFA['T'].pop(0)[1:])}
            _symbol = {s:idx for idx,s in enumerate([row.pop(0) for row in _DFA['T']])}
            _T = _DFA['T']

        found = False
        for _map in (dict(zip(Q, perm)) for perm in permutations(_Q, len(_Q))):
            if _map[S] == _DFA['S'] and \
               all(map(lambda f: _map[f] in _DFA['F'], F)) and \
               all(map(lambda v: all(map(lambda q: _map[T[symbol[v]][state[q]]] == _T[_symbol[v]][_state[_map[q]]], Q)) , V)):
                found = True
                break

        if not found:
            raise ValueError('Error: Non-isomorphic DFA produced')
