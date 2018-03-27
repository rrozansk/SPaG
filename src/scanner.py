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
        [ab]             (character class -> choice -> any specified char)
        [a..c] or [c..a] (character range -> choice -> any char between the two)
        [^ab] or [^a..c] (character negation -> choice -> all but the specified)
          NOTE: '^' is required to come first after the bracket for negation.
                If alone ([^]) it is translated as a simple class (just '^').
                It is still legal for character ranges as well ([^..b] and
                negated as [^^..b]). Also note that classes and ranges can
                be combined between the same set of brackets ([abc..z]), even
                multiple times if need be. Finally, for literal right brackets
                an escape is needed if mentioned ([\]]), but for all other
                characters no escapes are needed as everything is treated as a
                literal except possibly a '^' or '..' sequence. [^\e] is entire
                alphabet.
    - concat can be either implicit or explicit
    - grouping/disambiguation is allowed using parenthesis ()
    - supported escape sequences:
        operator literals -> \?, \*, \., \+, \|
        grouping literals -> \(, \), \[, \]
        epsilon           -> \e

 Testing is implemented in a table driven fashion using the black box method.
 The test may be run at the command line with the following invocation:

   $ python scanner.py

 If all tests passed no output will be produced. In the event of a failure a
 ValueError is thrown with the appropriate error/failure message. Both positive
 and negative tests cases are extensively tested.
"""
from uuid import uuid4


class RegularGrammar(object):
    """
    RegularGrammar represents a collection of formal regular expressions which
    can be programatically transformed/compiled into a minmal DFA.
    """

    _digits = set('0123456789')
    _spaces = set(' \t\v\f\r\n')
    _uppers = set('abcdefghijklmnopqrstuvwxyz')
    _lowers = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    _punctuation = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')

    _characters = _digits | _spaces | _uppers | _lowers | _punctuation

    _Star = 0
    _Union = 1
    _Concat = 2
    _Plus = 3
    _Question = 4
    _Epsilon = 5
    _Left_Paren = 6
    _Right_Paren = 7
    _Left_Bracket = 8
    _Right_Bracket = 9

    _operators = {
        '*': _Star,
        '|': _Union,
        '+': _Plus,
        '?': _Question,
        '(': _Left_Paren,
        ')': _Right_Paren,
        '[': _Left_Bracket,
        ']': _Right_Bracket,
        '.': _Concat
    }

    _literals = {
        _Star: '*',
        _Union: '|',
        _Plus: '+',
        _Question: '?',
        _Left_Paren: '(',
        _Right_Paren: ')',
        _Left_Bracket: '[',
        _Right_Bracket: ']',
        _Concat: '.'
    }

    _escapable = {
        's': ' ',
        't': '\t',
        'r': '\r',
        'v': '\v',
        'f': '\f',
        'n': '\n',
        '*': '*',
        '|': '|',
        '+': '+',
        '?': '?',
        '(': '(',
        ')': ')',
        '[': '[',
        ']': ']',
        '.': '.',
        '\\': '\\',
        'e': _Epsilon
    }

    _postfix = set([_Right_Paren, _Star, _Plus, _Question]) | _characters
    _prefix = set([_Left_Paren]) | _characters

    _precedence = {  # higher is better
        _Left_Paren:     (3, None),
        _Right_Paren:    (3, None),
        _Star:     (2, False),  # right-associative
        _Plus:     (2, False),  # right-associative
        _Question: (2, False),  # right-associative
        _Concat:   (1, True),   # left-associative
        _Union:    (0, True),   # left-associative
    }

    _name = None
    _expressions = None

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
        self._expressions = dict()

        for name, pattern in expressions.items():
            if type(name) is not str:
                raise ValueError('Invalid Input: name must be a string')

            if type(pattern) is not str:
                raise ValueError('Invalid Input: pattern must be a string')

            self._expressions[name] = pattern
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

        Runtime: O(1) - constant
        Type: None -> string
        """
        return self._name

    def expressions(self):
        """
        Get the patterns recognized by the Regular Grammar.

        Runtime: O(n) - linear to the number of expressions.
        Type: None -> dict[string]string
        """
        return self._expressions.copy()

    def states(self):
        """
        Get the states in the grammars equivalent minimal DFA.

        Runtime: O(n) - linear to the number of states.
        Type: None -> set
        """
        return self._states.copy()

    def alphabet(self):
        """
        Get the alphabet of characters recognized by the grammars DFA.

        Runtime: O(n) - linear to the number of alphabet characters.
        Type: None -> set
        """
        return self._alphas.copy()

    def transitions(self):
        """
        Get the state transitions defining the grammars DFA.

        Runtime: O(n) - linear to the number of state transitions.
        Type: None -> set
        """
        return self._deltas.copy()

    def start(self):
        """
        Get the start state of the grammars DFA.

        Runtime: O(1) - constant
        Type: None -> string
        """
        return self._start

    def accepting(self):
        """
        Get all accepting states of the grammars DFA.

        Runtime: O(n) - linear to the number of final states.
        Type: None -> set
        """
        return self._finals.copy()

    def _scan(self, expr):
        """
        Convert an external representation of a token (regular expression) to
        an internal one. Ensures all characters and escape sequences are valid.

        Character conversions:
          meta -> internal representation (integer enum)
          escaped meta -> character
          escaped escape -> character
          escape sequence -> internal representation

        Runtime: O(n) - linear to size of the input expr
        Type: string -> list | raise ValueError
        """
        output = []
        escape = False
        for char in expr:
            if escape:
                if char in self._escapable:
                    escape = False
                    output.append(self._escapable[char])
                else:
                    raise ValueError('Error: invalid escape seq: \\' + char)
            else:
                if char == '\\':
                    escape = True
                elif char in self._operators:
                    output.append(self._operators[char])
                elif char in self._characters:
                    output.append(char)
                else:
                    raise ValueError('Error: unrecognized character: ' + char)
        if escape:
            raise ValueError('Error: empty escape sequence')
        return output

    def _expand_char_class_range(self, expr):
        """
        Expand the internal representation of the expression so that
        character classes and ranges are eliminated.

        Runtime: O(n) - linear to input expr
        Type: list -> list
        """
        output = []
        literal = False
        literals = set()
        negation = False
        i, j = 0, len(expr)
        while i < j:
            char = expr[i]
            if literal:
                # test character class/range ending
                if char == self._Right_Bracket:
                    if len(literals) > 0:
                        if negation:
                            literals = self._characters - literals
                            negation = False
                        chars = [self._Left_Paren]
                        for char in literals:
                            chars.append(char)
                            chars.append(self._Union)
                        chars[-1] = self._Right_Paren
                        output.extend(chars)
                    literal = False
                    literals = set()
                # test for possible range since '^' may complicate things
                elif i+1 < j and self._literals.get(expr[i+1], expr[i+1]) == '.' and \
                     i+2 < j and self._literals.get(expr[i+2], expr[i+2]) == '.':
                    if i+3 > j or expr[i+3] == self._Right_Bracket:
                        raise ValueError('Error: Invalid character range')
                    boundry1 = self._literals.get(expr[i], expr[i])
                    boundry2 = self._literals.get(expr[i+3], expr[i+3])
                    if boundry1 < boundry2:
                        literals.update(map(chr, range(ord(boundry1), ord(boundry2)+1)))
                    else:  # boundry1 >= boundry2
                        literals.update(map(chr, range(ord(boundry2), ord(boundry1)+1)))
                    i += 3
                # test for possible negation (requirements):
                #   1. '^' occurs as the first character
                #   2. followed by character class or range
                elif char == '^' and len(literals) == 0 and \
                     i+1 < j and expr[i+1] != self._Right_Bracket:
                    negation = True
                # default to character class
                else:
                    literals.add(self._literals.get(expr[i], expr[i]))
            elif char == self._Left_Bracket:
                literal = True
            else:
                output.append(char)
            i += 1
        if literal:
            raise ValueError('Error: character class/range end not specified')
        return output

    def _expand_concat(self, expr):
        """
        Expand the internal representation of the expression so that
        concatentation is explicit throughout.

        Runtime: O(n) - linear to input expr
        Type: list -> list
        """
        if len(expr) == 0:
            return expr

        output = []
        for idx in range(1, len(expr)):
            output.append(expr[idx-1])
            if expr[idx-1] in self._postfix and \
               expr[idx] in self._prefix:
                output.append(self._Concat)
        output.append(expr[-1])
        return output

    def _shunt(self, expr):
        """
        Convert the input expression to be entirely in postfix notation (RPN;
        Reverse Polish Notation) allowing all parenthesis to be dropped.
        Adapted from Dijkstra's Shunting yard algorithm which can be viewed
        @https://en.wikipedia.org/wiki/Shunting-yard_algorithm.

        Runtime: O(n) - linear to input expression
        Type: list -> list | raise ValueError
        """
        stack, queue = [], []  # operators, output expression

        for token in expr:
            if token in self._characters:
                queue.append(token)
            elif token is self._Epsilon:
                queue.append(token)
            elif token == self._Left_Paren:
                stack.append(self._Left_Paren)
            elif token == self._Right_Paren:
                while len(stack) > 0 and stack[-1] != self._Left_Paren:
                    queue.append(stack.pop())
                if len(stack) == 0:
                    raise ValueError('Error: unbalanced parenthesis')
                stack.pop()
            elif token in self._precedence:
                while len(stack) > 0 and stack[-1] != self._Left_Paren and\
                      self._precedence[token][0] <= \
                      self._precedence[stack[-1]][0]\
                      and self._precedence[token][1]:  # left-associative?
                    queue.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError('Error: invalid input')

        while len(stack) > 0:
            token = stack.pop()
            if token == self._Left_Paren or token == self._Right_Paren:
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
        concatenation ., epsilon \e, literals, and syntax extensions kleene
        plus + and choice ?. Adapted to a iterative stacked based evaluation
        algorithm (standard RPN evaluation algorithm) from thompson
        construction as described in section 4.1 in 'A taxonomy of finite
        automata construction algorithms' by Bruce Watson,
        located @http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf

        Runtime: O(n) - linear to input expression
        Type: list -> set x set x set x dict x string x string
        """
        Q = set()   # states
        V = set()   # input symbols (alphabet)
        T = set()   # transition relation: T in P(Q x V x Q)
        E = dict()  # e-transition relation: E in P(Q x Q)
        S = None    # start state S in Q
        F = None    # accepting state F in Q

        def e_update(s, f):
            transitions = E[s] = E.get(s, set())
            transitions.add(f)

        stk = []  # NFA machine stk
        for token in expr:
            if token in self._precedence:
                if token == self._Concat:
                    if len(stk) < 2:
                        raise ValueError('Error: not enough args to op .')
                    p, F = stk.pop()
                    S, q = stk.pop()
                    e_update(q, p)
                elif token == self._Union:
                    if len(stk) < 2:
                        raise ValueError('Error: not enough args to op |')
                    p, q = stk.pop()
                    r, t = stk.pop()
                    S, F = self._state(), self._state()
                    e_update(S, p)
                    e_update(S, r)
                    e_update(q, F)
                    e_update(t, F)
                elif token == self._Star:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op *')
                    p, q = stk.pop()
                    S, F = self._state(), self._state()
                    e_update(S, p)
                    e_update(q, p)
                    e_update(q, F)
                    e_update(S, F)
                elif token == self._Plus:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op +')
                    p, q = stk.pop()
                    S, F = self._state(), self._state()
                    e_update(S, p)
                    e_update(q, p)
                    e_update(q, F)
                elif token == self._Question:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op ?')
                    p, q = stk.pop()
                    S, F = self._state(), self._state()
                    e_update(S, p)
                    e_update(S, F)
                    e_update(q, F)
                else:
                    raise ValueError('Error: operator not implemented')
            elif token in self._characters:
                S, F = self._state(), self._state()
                V.add(token)
                T.add((S, token, F))
            elif token == self._Epsilon:
                S, F = self._state(), self._state()
                e_update(S, F)
            else:
                raise ValueError('Error: invalid input')
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
        while len(explore) > 0:
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
        while len(explore) > 0:
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

        return frozenset(Qp), V, frozenset(Tp), Sp, frozenset(Fp)

    def _total(self, dfa):
        """
        Make the DFA's delta function total, if not already, by adding a
        sink/error state. All unspecified state transitions are then specified
        by adding a transition to the new sink/error state.

        Runtime: O(n) - linear in the number of states and transitions
        Type: set x set x set x string x set -> set x set x set x string x set
        """
        Q, V, T, S, F = dfa

        if len(T) != len(Q) * len(V):
            q_err = self._state()
            Q = Q | frozenset([q_err])

            M = {q: {} for q in Q}
            for t in T:
                M[t[0]][t[1]] = t[2]

            Tp = set()
            for q in Q:
                for c in V:
                    if M[q].get(c, None) is None:
                        Tp.add((q, c, q_err))
            T |= frozenset(Tp)

        return Q, V, T, S, F

    def _Hopcroft(self, dfa):
        """
        Minimize the DFA with reguard to nondistinguishable states using
        hopcrafts algorithm, which merges states together based on partition
        refinement.

        Runtime: O(ns log n) - linear log (n=number states; s=alphabet size)
        Type: set x set x set x set x set -> set x set x set x set x set
        """
        Q, V, T, S, F = dfa

        P = set([F, Q - F]) - set([frozenset()])  # if Q - F was empty
        W = set([F])
        while len(W) > 0:
            A = W.pop()
            for c in V:
                X = frozenset({t[0] for t in T if t[1] == c and t[2] in A})
                updates = []
                for Y in P:
                    s1 = X & Y
                    s2 = Y - X
                    if len(s1) > 0 and len(s2) > 0:
                        updates.append((Y, [s1, s2]))  # split partition Y
                        if Y in W:
                            W.remove(Y)
                            W.update([s1, s2])
                        else:
                            if len(s1) <= len(s2):
                                W.update([s1])
                            else:
                                W.update([s2])

                for (Y, [s1, s2]) in updates:
                    P.remove(Y)
                    P.update([s1, s2])

        Tp = set()
        for t in T:
            s1, s2 = None, None
            for part in P:
                if t[0] in part:
                    s1 = part
                if t[2] in part:
                    s2 = part
            Tp.add((s1, t[1], s2))

        Sp = None
        for part in P:
            if S in part:
                Sp = part
                break

        Fp = frozenset({part for part in P if len(part & F) > 0})

        return frozenset(P), V, frozenset(Tp), Sp, Fp

    def _alpha(self, dfa):
        """
        Perform an alpha rename on all DFA states to simplify the
        representation which the end user will consume.

        Runtime: O(n) - linear in the number of states and transitions
        Type: set x set x set x string x set -> set x set x set x string x set
        """
        Q, V, T, S, F = dfa
        rename = {q: self._state() for q in Q}
        Qp = set(rename.values())
        Fp = {rename[f] for f in F}
        Sp = rename[S]
        Tp = {(rename[t[0]], t[1], rename[t[2]]) for t in T}

        return Qp, V, Tp, Sp, Fp


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
                'T': set([
                    ('S', 'a', 'A'),
                    ('A', 'a', 'Err'),
                    ('Err', 'a', 'Err')
                ]),
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
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
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
                'T': set([
                    ('S', 'a', 'AB'),
                    ('S', 'b', 'AB'),
                    ('AB', 'a', 'Err'),
                    ('AB', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
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
                'T': set([('A', 'a', 'A')]),
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
                'T': set([
                    ('S', 'a', 'A'),
                    ('A', 'a', 'A')
                ]),
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
                'T': set([
                    ('S', 'a', 'A'),
                    ('A', 'a', 'Err'),
                    ('Err', 'a', 'Err')
                ]),
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
                'T': set([
                    ('AB*', 'a', 'AB*'),
                    ('AB*', 'b', 'AB*')
                ]),
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
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'B'),
                    ('B', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('A', 'a', 'Err'),
                    ('A', 'b', 'Err')
                ]),
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
                'T': set([
                    ('S', '.', 'F'),
                    ('F', '.', 'Err'),
                    ('Err', '.', 'Err'),
                    ('S', '|', 'F'),
                    ('F', '|', 'Err'),
                    ('Err', '|', 'Err'),
                    ('S', '*', 'F'),
                    ('F', '*', 'Err'),
                    ('Err', '*', 'Err'),
                    ('S', '?', 'F'),
                    ('F', '?', 'Err'),
                    ('Err', '?', 'Err'),
                    ('S', '+', 'F'),
                    ('F', '+', 'Err'),
                    ('Err', '+', 'Err'),
                    ('S', '\\', 'F'),
                    ('F', '\\', 'Err'),
                    ('Err', '\\', 'Err'),
                    ('S', '(', 'F'),
                    ('F', '(', 'Err'),
                    ('Err', '(', 'Err'),
                    ('S', ')', 'F'),
                    ('F', ')', 'Err'),
                    ('Err', ')', 'Err'),
                    ('S', '[', 'F'),
                    ('F', '[', 'Err'),
                    ('Err', '[', 'Err'),
                    ('S', ']', 'F'),
                    ('F', ']', 'Err'),
                    ('Err', ']', 'Err')
                ]),
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Epsilon',
            'valid': True,
            'expressions': {
                'epsilon': '\e'
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(),
                'T': set(),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Implicit Concatenation 1',
            'valid': True,
            'expressions': {
                'concat': 'ab'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 2',
            'valid': True,
            'expressions': {
                'concat': 'a(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 3',
            'valid': True,
            'expressions': {
                'concat': '(a)(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 4',
            'valid': True,
            'expressions': {
                'concat': 'a*(b)'
            },
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('A', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'A',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 5',
            'valid': True,
            'expressions': {
                'concat': 'a+(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('A', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 6',
            'valid': True,
            'expressions': {
                'concat': 'a?(b)'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'B'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 7',
            'valid': True,
            'expressions': {
                'concat': 'a*b'
            },
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('A', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'A',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 8',
            'valid': True,
            'expressions': {
                'concat': 'a+b'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('A', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': set(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 9',
            'valid': True,
            'expressions': {
                'concat': 'a?b'
            },
            'DFA': {
                'Q': set(['S', 'A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('S', 'b', 'B'),
                    ('S', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
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
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'Err'),
                    ('S', 'c', 'Err'),
                    ('S', 'd', 'Err'),
                    ('S', 'e', 'Err'),
                    ('A', 'b', 'B'),
                    ('A', 'a', 'Err'),
                    ('A', 'c', 'Err'),
                    ('A', 'd', 'Err'),
                    ('A', 'e', 'Err'),
                    ('B', 'c', 'C'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('B', 'd', 'Err'),
                    ('B', 'e', 'Err'),
                    ('C', 'd', 'D'),
                    ('C', 'a', 'Err'),
                    ('C', 'b', 'Err'),
                    ('C', 'c', 'Err'),
                    ('C', 'e', 'Err'),
                    ('D', 'e', 'E'),
                    ('D', 'a', 'Err'),
                    ('D', 'b', 'Err'),
                    ('D', 'c', 'Err'),
                    ('D', 'd', 'Err'),
                    ('E', 'a', 'Err'),
                    ('E', 'b', 'Err'),
                    ('E', 'c', 'Err'),
                    ('E', 'd', 'Err'),
                    ('E', 'e', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err'),
                    ('Err', 'd', 'Err'),
                    ('Err', 'e', 'Err')
                ]),
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
                'T': set([
                    ('AC', 'a', 'AC'),
                    ('AC', 'b', 'DE'),
                    ('AC', 'c', 'B'),
                    ('AC', 'd', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('B', 'c', 'Err'),
                    ('B', 'd', 'DE'),
                    ('DE', 'a', 'Err'),
                    ('DE', 'b', 'DE'),
                    ('DE', 'c', 'B'),
                    ('DE', 'd', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err'),
                    ('Err', 'd', 'Err')
                ]),
                'S': 'AC',
                'F': set(['AC', 'DE']),
            }
        },
        {
            'name': 'Randomness 2',
            'valid': True,
            'expressions': {
                'random': '(a|\e)b*'
            },
            'DFA': {
                'Q': set(['A', 'B', 'Err']),
                'V': set('ab'),
                'T': set([
                    ('A', 'a', 'B'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'B'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
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
                'T': set([
                    ('S', 'a', 'A'),
                    ('S', 'b', 'F'),
                    ('S', 'c', 'Err'),
                    ('S', 'd', 'Err'),
                    ('S', 'e', 'Err'),
                    ('A', 'a', 'A*'),
                    ('A', 'b', 'B'),
                    ('A', 'c', 'Err'),
                    ('A', 'd', 'Err'),
                    ('A', 'e', 'Err'),
                    ('A*', 'a', 'A*'),
                    ('A*', 'b', 'F'),
                    ('A*', 'c', 'Err'),
                    ('A*', 'd', 'Err'),
                    ('A*', 'e', 'Err'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('B', 'c', 'C'),
                    ('B', 'd', 'Err'),
                    ('B', 'e', 'Err'),
                    ('C', 'a', 'Err'),
                    ('C', 'b', 'Err'),
                    ('C', 'c', 'Err'),
                    ('C', 'd', 'D'),
                    ('C', 'e', 'Err'),
                    ('D', 'a', 'Err'),
                    ('D', 'b', 'Err'),
                    ('D', 'c', 'Err'),
                    ('D', 'd', 'Err'),
                    ('D', 'e', 'F'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('F', 'd', 'Err'),
                    ('F', 'e', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err'),
                    ('Err', 'd', 'Err'),
                    ('Err', 'e', 'Err')
                ]),
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
                'T': set([
                    ('S', 'f', 'F'),
                    ('S', 'o', 'Err'),
                    ('S', 'b', 'B'),
                    ('S', 'a', 'Err'),
                    ('S', 'r', 'Err'),
                    ('F', 'f', 'Err'),
                    ('F', 'o', 'FO'),
                    ('F', 'b', 'Err'),
                    ('F', 'a', 'Err'),
                    ('F', 'r', 'Err'),
                    ('FO', 'f', 'Err'),
                    ('FO', 'o', 'FOO'),
                    ('FO', 'b', 'Err'),
                    ('FO', 'a', 'Err'),
                    ('FO', 'r', 'Err'),
                    ('FOO', 'f', 'Err'),
                    ('FOO', 'o', 'Err'),
                    ('FOO', 'b', 'B'),
                    ('FOO', 'a', 'Err'),
                    ('FOO', 'r', 'Err'),
                    ('B', 'f', 'Err'),
                    ('B', 'o', 'Err'),
                    ('B', 'b', 'Err'),
                    ('B', 'a', 'BA'),
                    ('B', 'r', 'Err'),
                    ('BA', 'f', 'Err'),
                    ('BA', 'o', 'Err'),
                    ('BA', 'b', 'Err'),
                    ('BA', 'a', 'Err'),
                    ('BA', 'r', 'BAR'),
                    ('BAR', 'f', 'Err'),
                    ('BAR', 'o', 'Err'),
                    ('BAR', 'b', 'B'),
                    ('BAR', 'a', 'Err'),
                    ('BAR', 'r', 'Err'),
                    ('Err', 'f', 'Err'),
                    ('Err', 'o', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'r', 'Err')
                ]),
                'S': 'S',
                'F': set(['BAR'])
            }
        },
        {
            'name': 'Forward Character Range',
            'valid': True,
            'expressions': {
                'range': '[a..c]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': set([
                    ('S', 'a', 'F'),
                    ('S', 'b', 'F'),
                    ('S', 'c', 'F'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err')
                ]),
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Backward Character Range',
            'valid': True,
            'expressions': {
                'range': '[c..a]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('abc'),
                'T': set([
                    ('S', 'a', 'F'),
                    ('S', 'b', 'F'),
                    ('S', 'c', 'F'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err')
                ]),
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Literal Negation Character Range',
            'valid': True,
            'expressions': {
                'range': '[^..a]',
            },
            'DFA': {
                'Q': set(['S', 'F', 'Err']),
                'V': set('^_`a'),
                'T': set([
                    ('S', '^', 'F'),
                    ('S', '_', 'F'),
                    ('S', '`', 'F'),
                    ('S', 'a', 'F'),
                    ('F', '^', 'Err'),
                    ('F', '_', 'Err'),
                    ('F', '`', 'Err'),
                    ('F', 'a', 'Err'),
                    ('Err', '^', 'Err'),
                    ('Err', '_', 'Err'),
                    ('Err', '`', 'Err'),
                    ('Err', 'a', 'Err')
                ]),
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Negated Character Range',
            'valid': True,
            'expressions': {
                'range': '[^!..~]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': set([
                    ('S', ' ', 'S'),
                    ('S', '\t', 'S'),
                    ('S', '\n', 'S'),
                    ('S', '\r', 'S'),
                    ('S', '\f', 'S'),
                    ('S', '\v', 'S')
                ]),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Empty Character Range/Class',
            'valid': True,
            'expressions': {
                'class/range': '[]\e',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(),
                'T': set(),
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
                'T': set([
                    ('S', 'a', 'F'),
                    ('S', 'b', 'F'),
                    ('S', 'c', 'F'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err')
                ]),
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
                'T': set([
                    ('S', 'a', 'F'),
                    ('F', 'a', 'Err'),
                    ('Err', 'a', 'Err')
                ]),
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
                'T': set([
                    ('S', ']', 'S')
                ]),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Literal Negation Character Class',
            'valid': True,
            'expressions': {
                'class': '[^]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set('^'),
                'T': set([
                    ('S', '^', 'S')
                ]),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Negated Character Class',
            'valid': True,
            'expressions': {
                'class': '[^!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set(' \t\n\r\f\v'),
                'T': set([
                    ('S', ' ', 'S'),
                    ('S', '\t', 'S'),
                    ('S', '\n', 'S'),
                    ('S', '\r', 'S'),
                    ('S', '\f', 'S'),
                    ('S', '\v', 'S')
                ]),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Character Class Range Combo',
            'valid': True,
            'expressions': {
                'class': '[abc..e]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set('abcde'),
                'T': set([
                    ('S', 'a', 'S'),
                    ('S', 'b', 'S'),
                    ('S', 'c', 'S'),
                    ('S', 'd', 'S'),
                    ('S', 'e', 'S')
                ]),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Character Range Class Combo',
            'valid': True,
            'expressions': {
                'class': '[a..cde]*',
            },
            'DFA': {
                'Q': set(['S']),
                'V': set('abcde'),
                'T': set([
                    ('S', 'a', 'S'),
                    ('S', 'b', 'S'),
                    ('S', 'c', 'S'),
                    ('S', 'd', 'S'),
                    ('S', 'e', 'S')
                ]),
                'S': 'S',
                'F': set(['S'])
            }
        },
        {
            'name': 'Integer',
            'valid': True,
            'expressions': {
                'int': "0|([-+]?[1..9][0..9]*)",
            },
            'DFA': {
                'Q': set(['S', 'Zero', 'Sign', 'Int', 'Err']),
                'V': set('+-0123456789'),
                'T': set([
                    ('S', '+', 'Sign'),
                    ('S', '-', 'Sign'),
                    ('S', '0', 'Zero'),
                    ('S', '1', 'Int'),
                    ('S', '2', 'Int'),
                    ('S', '3', 'Int'),
                    ('S', '4', 'Int'),
                    ('S', '5', 'Int'),
                    ('S', '6', 'Int'),
                    ('S', '7', 'Int'),
                    ('S', '8', 'Int'),
                    ('S', '9', 'Int'),
                    ('Zero', '+', 'Err'),
                    ('Zero', '-', 'Err'),
                    ('Zero', '0', 'Err'),
                    ('Zero', '1', 'Err'),
                    ('Zero', '2', 'Err'),
                    ('Zero', '3', 'Err'),
                    ('Zero', '4', 'Err'),
                    ('Zero', '5', 'Err'),
                    ('Zero', '6', 'Err'),
                    ('Zero', '7', 'Err'),
                    ('Zero', '8', 'Err'),
                    ('Zero', '9', 'Err'),
                    ('Sign', '+', 'Err'),
                    ('Sign', '-', 'Err'),
                    ('Sign', '0', 'Err'),
                    ('Sign', '1', 'Int'),
                    ('Sign', '2', 'Int'),
                    ('Sign', '3', 'Int'),
                    ('Sign', '4', 'Int'),
                    ('Sign', '5', 'Int'),
                    ('Sign', '6', 'Int'),
                    ('Sign', '7', 'Int'),
                    ('Sign', '8', 'Int'),
                    ('Sign', '9', 'Int'),
                    ('Int', '+', 'Err'),
                    ('Int', '-', 'Err'),
                    ('Int', '0', 'Int'),
                    ('Int', '1', 'Int'),
                    ('Int', '2', 'Int'),
                    ('Int', '3', 'Int'),
                    ('Int', '4', 'Int'),
                    ('Int', '5', 'Int'),
                    ('Int', '6', 'Int'),
                    ('Int', '7', 'Int'),
                    ('Int', '8', 'Int'),
                    ('Int', '9', 'Int'),
                    ('Err', '+', 'Err'),
                    ('Err', '-', 'Err'),
                    ('Err', '0', 'Err'),
                    ('Err', '1', 'Err'),
                    ('Err', '2', 'Err'),
                    ('Err', '3', 'Err'),
                    ('Err', '4', 'Err'),
                    ('Err', '5', 'Err'),
                    ('Err', '6', 'Err'),
                    ('Err', '7', 'Err'),
                    ('Err', '8', 'Err'),
                    ('Err', '9', 'Err')
                ]),
                'S': 'S',
                'F': set(['Zero', 'Int'])
            }
        },
        {
            'name': 'Float',
            'valid': True,
            'expressions': {
                'float': '[-+]?[0..9]*\.?[0..9]+([eE][-+]?[0..9]+)?',
            },
            'DFA': {
                'Q': set(['S', 'WholePart', 'ExpPart', 'FractionPart',
                          'eSignum', 'Sigfrac', 'Sigexp', 'Signum', 'Err']),
                'V': set('+-.0123456789eE'),
                'T': set([
                      ('WholePart', '2', 'WholePart'),
                      ('FractionPart', '5', 'FractionPart'),
                      ('eSignum', '0', 'ExpPart'),
                      ('S', 'E', 'Err'),
                      ('Sigfrac', '2', 'FractionPart'),
                      ('ExpPart', '9', 'ExpPart'),
                      ('Sigexp', '3', 'ExpPart'),
                      ('Signum', '1', 'WholePart'),
                      ('WholePart', '+', 'Err'),
                      ('eSignum', 'e', 'Err'),
                      ('S', '3', 'WholePart'),
                      ('eSignum', '-', 'Err'),
                      ('Sigfrac', 'e', 'Err'),
                      ('WholePart', '0', 'WholePart'),
                      ('FractionPart', '9', 'FractionPart'),
                      ('Err', '5', 'Err'),
                      ('ExpPart', '-', 'Err'),
                      ('Err', '4', 'Err'),
                      ('Signum', '2', 'WholePart'),
                      ('Signum', 'e', 'Err'),
                      ('Err', '.', 'Err'),
                      ('Err', '3', 'Err'),
                      ('Signum', '3', 'WholePart'),
                      ('Signum', '-', 'Err'),
                      ('ExpPart', '6', 'ExpPart'),
                      ('FractionPart', '-', 'Err'),
                      ('Err', '2', 'Err'),
                      ('FractionPart', '8', 'FractionPart'),
                      ('WholePart', '.', 'Sigfrac'),
                      ('ExpPart', 'E', 'Err'),
                      ('Sigfrac', '0', 'FractionPart'),
                      ('S', 'e', 'Err'),
                      ('eSignum', '5', 'ExpPart'),
                      ('Signum', '4', 'WholePart'),
                      ('ExpPart', '8', 'ExpPart'),
                      ('ExpPart', '.', 'Err'),
                      ('Sigexp', '-', 'eSignum'),
                      ('Err', 'E', 'Err'),
                      ('S', '6', 'WholePart'),
                      ('S', '+', 'Signum'),
                      ('WholePart', '5', 'WholePart'),
                      ('Err', '-', 'Err'),
                      ('Sigfrac', 'E', 'Err'),
                      ('WholePart', '7', 'WholePart'),
                      ('Sigexp', '9', 'ExpPart'),
                      ('Sigexp', '8', 'ExpPart'),
                      ('Err', '1', 'Err'),
                      ('Err', '+', 'Err'),
                      ('Err', '0', 'Err'),
                      ('Sigfrac', '.', 'Err'),
                      ('Sigfrac', '6', 'FractionPart'),
                      ('S', '0', 'WholePart'),
                      ('Signum', '5', 'WholePart'),
                      ('WholePart', '3', 'WholePart'),
                      ('eSignum', '3', 'ExpPart'),
                      ('ExpPart', '7', 'ExpPart'),
                      ('Sigfrac', '9', 'FractionPart'),
                      ('ExpPart', 'e', 'Err'),
                      ('Signum', '.', 'Sigfrac'),
                      ('Sigexp', '+', 'eSignum'),
                      ('eSignum', '8', 'ExpPart'),
                      ('eSignum', '1', 'ExpPart'),
                      ('ExpPart', '4', 'ExpPart'),
                      ('Signum', '6', 'WholePart'),
                      ('FractionPart', 'E', 'Sigexp'),
                      ('Signum', 'E', 'Err'),
                      ('Signum', '7', 'WholePart'),
                      ('WholePart', '8', 'WholePart'),
                      ('Sigexp', '4', 'ExpPart'),
                      ('eSignum', '+', 'Err'),
                      ('Sigfrac', '4', 'FractionPart'),
                      ('Signum', '+', 'Err'),
                      ('eSignum', 'E', 'Err'),
                      ('Err', 'e', 'Err'),
                      ('ExpPart', '5', 'ExpPart'),
                      ('FractionPart', '3', 'FractionPart'),
                      ('Sigexp', '.', 'Err'),
                      ('S', '2', 'WholePart'),
                      ('ExpPart', '3', 'ExpPart'),
                      ('WholePart', '1', 'WholePart'),
                      ('ExpPart', '2', 'ExpPart'),
                      ('S', '9', 'WholePart'),
                      ('Sigfrac', '3', 'FractionPart'),
                      ('Sigexp', 'e', 'Err'),
                      ('ExpPart', '0', 'ExpPart'),
                      ('FractionPart', '+', 'Err'),
                      ('FractionPart', '2', 'FractionPart'),
                      ('S', '4', 'WholePart'),
                      ('Sigfrac', '+', 'Err'),
                      ('Signum', '9', 'WholePart'),
                      ('eSignum', '6', 'ExpPart'),
                      ('S', '5', 'WholePart'),
                      ('Err', '9', 'Err'),
                      ('WholePart', '6', 'WholePart'),
                      ('Sigfrac', '-', 'Err'),
                      ('Sigexp', '5', 'ExpPart'),
                      ('FractionPart', '1', 'FractionPart'),
                      ('Err', '8', 'Err'),
                      ('ExpPart', '1', 'ExpPart'),
                      ('WholePart', 'e', 'Sigexp'),
                      ('Sigexp', '6', 'ExpPart'),
                      ('FractionPart', 'e', 'Sigexp'),
                      ('ExpPart', '+', 'Err'),
                      ('Sigfrac', '1', 'FractionPart'),
                      ('S', '7', 'WholePart'),
                      ('FractionPart', '0', 'FractionPart'),
                      ('WholePart', '4', 'WholePart'),
                      ('Sigfrac', '8', 'FractionPart'),
                      ('eSignum', '9', 'ExpPart'),
                      ('S', '.', 'Sigfrac'),
                      ('WholePart', 'E', 'Sigexp'),
                      ('eSignum', '4', 'ExpPart'),
                      ('FractionPart', '.', 'Err'),
                      ('Sigfrac', '5', 'FractionPart'),
                      ('Sigexp', '7', 'ExpPart'),
                      ('FractionPart', '7', 'FractionPart'),
                      ('S', '-', 'Signum'),
                      ('eSignum', '2', 'ExpPart'),
                      ('FractionPart', '4', 'FractionPart'),
                      ('Signum', '8', 'WholePart'),
                      ('Signum', '0', 'WholePart'),
                      ('Sigexp', '1', 'ExpPart'),
                      ('Sigexp', '0', 'ExpPart'),
                      ('eSignum', '.', 'Err'),
                      ('WholePart', '-', 'Err'),
                      ('Sigfrac', '7', 'FractionPart'),
                      ('Sigexp', 'E', 'Err'),
                      ('FractionPart', '6', 'FractionPart'),
                      ('Sigexp', '2', 'ExpPart'),
                      ('Err', '7', 'Err'),
                      ('eSignum', '7', 'ExpPart'),
                      ('S', '8', 'WholePart'),
                      ('WholePart', '9', 'WholePart'),
                      ('Err', '6', 'Err'),
                      ('S', '1', 'WholePart')
                ]),
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
                'T': set([
                    ('S', ' ', 'S'),
                    ('S', '\t', 'S'),
                    ('S', '\n', 'S'),
                    ('S', '\r', 'S'),
                    ('S', '\f', 'S'),
                    ('S', '\v', 'S')
                ]),
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
                'T': set([
                    ('S', 't', 'T'),
                    ('S', 'r', 'Err'),
                    ('S', 'u', 'Err'),
                    ('S', 'e', 'Err'),
                    ('S', 'f', 'F'),
                    ('S', 'a', 'Err'),
                    ('S', 'l', 'Err'),
                    ('S', 's', 'Err'),
                    ('T', 't', 'Err'),
                    ('T', 'r', 'R'),
                    ('T', 'u', 'Err'),
                    ('T', 'e', 'Err'),
                    ('T', 'f', 'Err'),
                    ('T', 'a', 'Err'),
                    ('T', 'l', 'Err'),
                    ('T', 's', 'Err'),
                    ('R', 't', 'Err'),
                    ('R', 'r', 'Err'),
                    ('R', 'u', 'US'),
                    ('R', 'e', 'Err'),
                    ('R', 'f', 'Err'),
                    ('R', 'a', 'Err'),
                    ('R', 'l', 'Err'),
                    ('R', 's', 'Err'),
                    ('US', 't', 'Err'),
                    ('US', 'r', 'Err'),
                    ('US', 'u', 'Err'),
                    ('US', 'e', 'E'),
                    ('US', 'f', 'Err'),
                    ('US', 'a', 'Err'),
                    ('US', 'l', 'Err'),
                    ('US', 's', 'Err'),
                    ('F', 't', 'Err'),
                    ('F', 'r', 'Err'),
                    ('F', 'u', 'Err'),
                    ('F', 'e', 'Err'),
                    ('F', 'f', 'Err'),
                    ('F', 'a', 'A'),
                    ('F', 'l', 'Err'),
                    ('F', 's', 'Err'),
                    ('A', 't', 'Err'),
                    ('A', 'r', 'Err'),
                    ('A', 'u', 'Err'),
                    ('A', 'e', 'Err'),
                    ('A', 'f', 'Err'),
                    ('A', 'a', 'Err'),
                    ('A', 'l', 'L'),
                    ('A', 's', 'Err'),
                    ('L', 't', 'Err'),
                    ('L', 'r', 'Err'),
                    ('L', 'u', 'Err'),
                    ('L', 'e', 'Err'),
                    ('L', 'f', 'Err'),
                    ('L', 'a', 'Err'),
                    ('L', 'l', 'Err'),
                    ('L', 's', 'US'),
                    ('E', 't', 'Err'),
                    ('E', 'r', 'Err'),
                    ('E', 'u', 'Err'),
                    ('E', 'e', 'Err'),
                    ('E', 'f', 'Err'),
                    ('E', 'a', 'Err'),
                    ('E', 'l', 'Err'),
                    ('E', 's', 'Err'),
                    ('Err', 't', 'Err'),
                    ('Err', 'r', 'Err'),
                    ('Err', 'u', 'Err'),
                    ('Err', 'e', 'Err'),
                    ('Err', 'f', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'l', 'Err'),
                    ('Err', 's', 'Err')
                ]),
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
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\\\\]^_`{|}~'),
                'T': set([
                    ('S', '#', '_'),
                    ('S', ';', '_'),
                    ('S', '0', 'Err'),
                    ('S', '1', 'Err'),
                    ('S', '2', 'Err'),
                    ('S', '3', 'Err'),
                    ('S', '4', 'Err'),
                    ('S', '5', 'Err'),
                    ('S', '6', 'Err'),
                    ('S', '7', 'Err'),
                    ('S', '8', 'Err'),
                    ('S', '9', 'Err'),
                    ('S', ' ', 'Err'),
                    ('S', '\t', 'Err'),
                    ('S', '\v', 'Err'),
                    ('S', '\f', 'Err'),
                    ('S', '\r', 'Err'),
                    ('S', '\n', 'Err'),
                    ('S', 'a', 'Err'),
                    ('S', 'b', 'Err'),
                    ('S', 'c', 'Err'),
                    ('S', 'd', 'Err'),
                    ('S', 'e', 'Err'),
                    ('S', 'f', 'Err'),
                    ('S', 'g', 'Err'),
                    ('S', 'h', 'Err'),
                    ('S', 'i', 'Err'),
                    ('S', 'j', 'Err'),
                    ('S', 'k', 'Err'),
                    ('S', 'l', 'Err'),
                    ('S', 'm', 'Err'),
                    ('S', 'n', 'Err'),
                    ('S', 'o', 'Err'),
                    ('S', 'p', 'Err'),
                    ('S', 'q', 'Err'),
                    ('S', 'r', 'Err'),
                    ('S', 's', 'Err'),
                    ('S', 't', 'Err'),
                    ('S', 'u', 'Err'),
                    ('S', 'v', 'Err'),
                    ('S', 'w', 'Err'),
                    ('S', 'x', 'Err'),
                    ('S', 'y', 'Err'),
                    ('S', 'z', 'Err'),
                    ('S', 'A', 'Err'),
                    ('S', 'B', 'Err'),
                    ('S', 'C', 'Err'),
                    ('S', 'D', 'Err'),
                    ('S', 'E', 'Err'),
                    ('S', 'F', 'Err'),
                    ('S', 'G', 'Err'),
                    ('S', 'H', 'Err'),
                    ('S', 'I', 'Err'),
                    ('S', 'J', 'Err'),
                    ('S', 'K', 'Err'),
                    ('S', 'L', 'Err'),
                    ('S', 'M', 'Err'),
                    ('S', 'N', 'Err'),
                    ('S', 'O', 'Err'),
                    ('S', 'P', 'Err'),
                    ('S', 'Q', 'Err'),
                    ('S', 'R', 'Err'),
                    ('S', 'S', 'Err'),
                    ('S', 'T', 'Err'),
                    ('S', 'U', 'Err'),
                    ('S', 'V', 'Err'),
                    ('S', 'W', 'Err'),
                    ('S', 'X', 'Err'),
                    ('S', 'Y', 'Err'),
                    ('S', 'Z', 'Err'),
                    ('S', '!', 'Err'),
                    ('S', '"', 'Err'),
                    ('S', '$', 'Err'),
                    ('S', '%', 'Err'),
                    ('S', '&', 'Err'),
                    ('S', '\'', 'Err'),
                    ('S', '(', 'Err'),
                    ('S', ')', 'Err'),
                    ('S', '*', 'Err'),
                    ('S', '+', 'Err'),
                    ('S', ',', 'Err'),
                    ('S', '-', 'Err'),
                    ('S', '.', 'Err'),
                    ('S', '/', 'Err'),
                    ('S', ':', 'Err'),
                    ('S', '<', 'Err'),
                    ('S', '=', 'Err'),
                    ('S', '>', 'Err'),
                    ('S', '?', 'Err'),
                    ('S', '@', 'Err'),
                    ('S', '[', 'Err'),
                    ('S', '\\', 'Err'),
                    ('S', ']', 'Err'),
                    ('S', '^', 'Err'),
                    ('S', '_', 'Err'),
                    ('S', '`', 'Err'),
                    ('S', '{', 'Err'),
                    ('S', '|', 'Err'),
                    ('S', '}', 'Err'),
                    ('S', '~', 'Err'),
                    ('_', '\n', 'F'),
                    ('_', '#', '_'),
                    ('_', ';', '_'),
                    ('_', '0', '_'),
                    ('_', '1', '_'),
                    ('_', '2', '_'),
                    ('_', '3', '_'),
                    ('_', '4', '_'),
                    ('_', '5', '_'),
                    ('_', '6', '_'),
                    ('_', '7', '_'),
                    ('_', '8', '_'),
                    ('_', '9', '_'),
                    ('_', ' ', '_'),
                    ('_', '\t', '_'),
                    ('_', '\v', '_'),
                    ('_', '\f', '_'),
                    ('_', '\r', '_'),
                    ('_', 'a', '_'),
                    ('_', 'b', '_'),
                    ('_', 'c', '_'),
                    ('_', 'd', '_'),
                    ('_', 'e', '_'),
                    ('_', 'f', '_'),
                    ('_', 'g', '_'),
                    ('_', 'h', '_'),
                    ('_', 'i', '_'),
                    ('_', 'j', '_'),
                    ('_', 'k', '_'),
                    ('_', 'l', '_'),
                    ('_', 'm', '_'),
                    ('_', 'n', '_'),
                    ('_', 'o', '_'),
                    ('_', 'p', '_'),
                    ('_', 'q', '_'),
                    ('_', 'r', '_'),
                    ('_', 's', '_'),
                    ('_', 't', '_'),
                    ('_', 'u', '_'),
                    ('_', 'v', '_'),
                    ('_', 'w', '_'),
                    ('_', 'x', '_'),
                    ('_', 'y', '_'),
                    ('_', 'z', '_'),
                    ('_', 'A', '_'),
                    ('_', 'B', '_'),
                    ('_', 'C', '_'),
                    ('_', 'D', '_'),
                    ('_', 'E', '_'),
                    ('_', 'F', '_'),
                    ('_', 'G', '_'),
                    ('_', 'H', '_'),
                    ('_', 'I', '_'),
                    ('_', 'J', '_'),
                    ('_', 'K', '_'),
                    ('_', 'L', '_'),
                    ('_', 'M', '_'),
                    ('_', 'N', '_'),
                    ('_', 'O', '_'),
                    ('_', 'P', '_'),
                    ('_', 'Q', '_'),
                    ('_', 'R', '_'),
                    ('_', 'S', '_'),
                    ('_', 'T', '_'),
                    ('_', 'U', '_'),
                    ('_', 'V', '_'),
                    ('_', 'W', '_'),
                    ('_', 'X', '_'),
                    ('_', 'Y', '_'),
                    ('_', 'Z', '_'),
                    ('_', '!', '_'),
                    ('_', '"', '_'),
                    ('_', '$', '_'),
                    ('_', '%', '_'),
                    ('_', '&', '_'),
                    ('_', '\'', '_'),
                    ('_', '(', '_'),
                    ('_', ')', '_'),
                    ('_', '*', '_'),
                    ('_', '+', '_'),
                    ('_', ',', '_'),
                    ('_', '-', '_'),
                    ('_', '.', '_'),
                    ('_', '/', '_'),
                    ('_', ':', '_'),
                    ('_', '<', '_'),
                    ('_', '=', '_'),
                    ('_', '>', '_'),
                    ('_', '?', '_'),
                    ('_', '@', '_'),
                    ('_', '[', '_'),
                    ('_', '\\', '_'),
                    ('_', ']', '_'),
                    ('_', '^', '_'),
                    ('_', '_', '_'),
                    ('_', '`', '_'),
                    ('_', '{', '_'),
                    ('_', '|', '_'),
                    ('_', '}', '_'),
                    ('_', '~', '_'),
                    ('F', '\n', 'Err'),
                    ('F', '#', 'Err'),
                    ('F', ';', 'Err'),
                    ('F', '0', 'Err'),
                    ('F', '1', 'Err'),
                    ('F', '2', 'Err'),
                    ('F', '3', 'Err'),
                    ('F', '4', 'Err'),
                    ('F', '5', 'Err'),
                    ('F', '6', 'Err'),
                    ('F', '7', 'Err'),
                    ('F', '8', 'Err'),
                    ('F', '9', 'Err'),
                    ('F', ' ', 'Err'),
                    ('F', '\t', 'Err'),
                    ('F', '\v', 'Err'),
                    ('F', '\f', 'Err'),
                    ('F', '\r', 'Err'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('F', 'd', 'Err'),
                    ('F', 'e', 'Err'),
                    ('F', 'f', 'Err'),
                    ('F', 'g', 'Err'),
                    ('F', 'h', 'Err'),
                    ('F', 'i', 'Err'),
                    ('F', 'j', 'Err'),
                    ('F', 'k', 'Err'),
                    ('F', 'l', 'Err'),
                    ('F', 'm', 'Err'),
                    ('F', 'n', 'Err'),
                    ('F', 'o', 'Err'),
                    ('F', 'p', 'Err'),
                    ('F', 'q', 'Err'),
                    ('F', 'r', 'Err'),
                    ('F', 's', 'Err'),
                    ('F', 't', 'Err'),
                    ('F', 'u', 'Err'),
                    ('F', 'v', 'Err'),
                    ('F', 'w', 'Err'),
                    ('F', 'x', 'Err'),
                    ('F', 'y', 'Err'),
                    ('F', 'z', 'Err'),
                    ('F', 'A', 'Err'),
                    ('F', 'B', 'Err'),
                    ('F', 'C', 'Err'),
                    ('F', 'D', 'Err'),
                    ('F', 'E', 'Err'),
                    ('F', 'F', 'Err'),
                    ('F', 'G', 'Err'),
                    ('F', 'H', 'Err'),
                    ('F', 'I', 'Err'),
                    ('F', 'J', 'Err'),
                    ('F', 'K', 'Err'),
                    ('F', 'L', 'Err'),
                    ('F', 'M', 'Err'),
                    ('F', 'N', 'Err'),
                    ('F', 'O', 'Err'),
                    ('F', 'P', 'Err'),
                    ('F', 'Q', 'Err'),
                    ('F', 'R', 'Err'),
                    ('F', 'S', 'Err'),
                    ('F', 'T', 'Err'),
                    ('F', 'U', 'Err'),
                    ('F', 'V', 'Err'),
                    ('F', 'W', 'Err'),
                    ('F', 'X', 'Err'),
                    ('F', 'Y', 'Err'),
                    ('F', 'Z', 'Err'),
                    ('F', '!', 'Err'),
                    ('F', '"', 'Err'),
                    ('F', '$', 'Err'),
                    ('F', '%', 'Err'),
                    ('F', '&', 'Err'),
                    ('F', '\'', 'Err'),
                    ('F', '(', 'Err'),
                    ('F', ')', 'Err'),
                    ('F', '*', 'Err'),
                    ('F', '+', 'Err'),
                    ('F', ',', 'Err'),
                    ('F', '-', 'Err'),
                    ('F', '.', 'Err'),
                    ('F', '/', 'Err'),
                    ('F', ':', 'Err'),
                    ('F', '<', 'Err'),
                    ('F', '=', 'Err'),
                    ('F', '>', 'Err'),
                    ('F', '?', 'Err'),
                    ('F', '@', 'Err'),
                    ('F', '[', 'Err'),
                    ('F', '\\', 'Err'),
                    ('F', ']', 'Err'),
                    ('F', '^', 'Err'),
                    ('F', '_', 'Err'),
                    ('F', '`', 'Err'),
                    ('F', '{', 'Err'),
                    ('F', '|', 'Err'),
                    ('F', '}', 'Err'),
                    ('F', '~', 'Err'),
                    ('Err', '\n', 'Err'),
                    ('Err', '#', 'Err'),
                    ('Err', ';', 'Err'),
                    ('Err', '0', 'Err'),
                    ('Err', '1', 'Err'),
                    ('Err', '2', 'Err'),
                    ('Err', '3', 'Err'),
                    ('Err', '4', 'Err'),
                    ('Err', '5', 'Err'),
                    ('Err', '6', 'Err'),
                    ('Err', '7', 'Err'),
                    ('Err', '8', 'Err'),
                    ('Err', '9', 'Err'),
                    ('Err', ' ', 'Err'),
                    ('Err', '\t', 'Err'),
                    ('Err', '\v', 'Err'),
                    ('Err', '\f', 'Err'),
                    ('Err', '\r', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err'),
                    ('Err', 'd', 'Err'),
                    ('Err', 'e', 'Err'),
                    ('Err', 'f', 'Err'),
                    ('Err', 'g', 'Err'),
                    ('Err', 'h', 'Err'),
                    ('Err', 'i', 'Err'),
                    ('Err', 'j', 'Err'),
                    ('Err', 'k', 'Err'),
                    ('Err', 'l', 'Err'),
                    ('Err', 'm', 'Err'),
                    ('Err', 'n', 'Err'),
                    ('Err', 'o', 'Err'),
                    ('Err', 'p', 'Err'),
                    ('Err', 'q', 'Err'),
                    ('Err', 'r', 'Err'),
                    ('Err', 's', 'Err'),
                    ('Err', 't', 'Err'),
                    ('Err', 'u', 'Err'),
                    ('Err', 'v', 'Err'),
                    ('Err', 'w', 'Err'),
                    ('Err', 'x', 'Err'),
                    ('Err', 'y', 'Err'),
                    ('Err', 'z', 'Err'),
                    ('Err', 'A', 'Err'),
                    ('Err', 'B', 'Err'),
                    ('Err', 'C', 'Err'),
                    ('Err', 'D', 'Err'),
                    ('Err', 'E', 'Err'),
                    ('Err', 'F', 'Err'),
                    ('Err', 'G', 'Err'),
                    ('Err', 'H', 'Err'),
                    ('Err', 'I', 'Err'),
                    ('Err', 'J', 'Err'),
                    ('Err', 'K', 'Err'),
                    ('Err', 'L', 'Err'),
                    ('Err', 'M', 'Err'),
                    ('Err', 'N', 'Err'),
                    ('Err', 'O', 'Err'),
                    ('Err', 'P', 'Err'),
                    ('Err', 'Q', 'Err'),
                    ('Err', 'R', 'Err'),
                    ('Err', 'S', 'Err'),
                    ('Err', 'T', 'Err'),
                    ('Err', 'U', 'Err'),
                    ('Err', 'V', 'Err'),
                    ('Err', 'W', 'Err'),
                    ('Err', 'X', 'Err'),
                    ('Err', 'Y', 'Err'),
                    ('Err', 'Z', 'Err'),
                    ('Err', '!', 'Err'),
                    ('Err', '"', 'Err'),
                    ('Err', '$', 'Err'),
                    ('Err', '%', 'Err'),
                    ('Err', '&', 'Err'),
                    ('Err', '\'', 'Err'),
                    ('Err', '(', 'Err'),
                    ('Err', ')', 'Err'),
                    ('Err', '*', 'Err'),
                    ('Err', '+', 'Err'),
                    ('Err', ',', 'Err'),
                    ('Err', '-', 'Err'),
                    ('Err', '.', 'Err'),
                    ('Err', '/', 'Err'),
                    ('Err', ':', 'Err'),
                    ('Err', '<', 'Err'),
                    ('Err', '=', 'Err'),
                    ('Err', '>', 'Err'),
                    ('Err', '?', 'Err'),
                    ('Err', '@', 'Err'),
                    ('Err', '[', 'Err'),
                    ('Err', '\\', 'Err'),
                    ('Err', ']', 'Err'),
                    ('Err', '^', 'Err'),
                    ('Err', '_', 'Err'),
                    ('Err', '`', 'Err'),
                    ('Err', '{', 'Err'),
                    ('Err', '|', 'Err'),
                    ('Err', '}', 'Err'),
                    ('Err', '~', 'Err')
                ]),
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Block Comment',
            'valid': True,
            'expressions': {
                'comment': '/[*][^\e]*[*]/',
            },
            'DFA': {
                'Q': set(['BEGIN', 'SINK', 'FSLASH', 'SIGEND', 'END', 'ERR']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\\\\]^_`{|}~'),
                'T': set([
                    ('ERR', '7', 'ERR'),
                    ('ERR', 'S', 'ERR'),
                    ('BEGIN', 'f', 'ERR'),
                    ('SIGEND', '1', 'SINK'),
                    ('FSLASH', '9', 'ERR'),
                    ('BEGIN', 'N', 'ERR'),
                    ('BEGIN', '+', 'ERR'),
                    ('SINK', '.', 'SINK'),
                    ('ERR', '8', 'ERR'),
                    ('SINK', '\r', 'SINK'),
                    ('END', '@', 'SINK'),
                    ('SIGEND', 'p', 'SINK'),
                    ('FSLASH', 'l', 'ERR'),
                    ('BEGIN', '\r', 'ERR'),
                    ('FSLASH', 'Q', 'ERR'),
                    ('FSLASH', '~', 'ERR'),
                    ('BEGIN', '*', 'ERR'),
                    ('SINK', 'e', 'SINK'),
                    ('FSLASH', '}', 'ERR'),
                    ('BEGIN', 'p', 'ERR'),
                    ('SINK', '4', 'SINK'),
                    ('ERR', '%', 'ERR'),
                    ('BEGIN', '%', 'ERR'),
                    ('ERR', 'A', 'ERR'),
                    ('SINK', '2', 'SINK'),
                    ('END', '\x0b', 'SINK'),
                    ('SINK', '\x0c', 'SINK'),
                    ('SIGEND', 'e', 'SINK'),
                    ('ERR', 'B', 'ERR'),
                    ('END', 'E', 'SINK'),
                    ('SINK', 'i', 'SINK'),
                    ('ERR', '3', 'ERR'),
                    ('SIGEND', 'W', 'SINK'),
                    ('END', '~', 'SINK'),
                    ('BEGIN', 'J', 'ERR'),
                    ('ERR', '4', 'ERR'),
                    ('END', '\t', 'SINK'),
                    ('FSLASH', ',', 'ERR'),
                    ('SIGEND', 'c', 'SINK'),
                    ('SIGEND', '(', 'SINK'),
                    ('SINK', '-', 'SINK'),
                    ('SINK', 'f', 'SINK'),
                    ('FSLASH', ']', 'ERR'),
                    ('END', 'z', 'SINK'),
                    ('SINK', 'E', 'SINK'),
                    ('ERR', '!', 'ERR'),
                    ('FSLASH', 'i', 'ERR'),
                    ('ERR', '"', 'ERR'),
                    ('SIGEND', 't', 'SINK'),
                    ('SINK', 'I', 'SINK'),
                    ('SIGEND', '~', 'SINK'),
                    ('SINK', 'G', 'SINK'),
                    ('ERR', '\n', 'ERR'),
                    ('SINK', '8', 'SINK'),
                    ('BEGIN', 'F', 'ERR'),
                    ('SINK', 'd', 'SINK'),
                    ('BEGIN', 'u', 'ERR'),
                    ('SIGEND', 'r', 'SINK'),
                    ('SINK', 'K', 'SINK'),
                    ('END', 'A', 'SINK'),
                    ('END', '[', 'SINK'),
                    ('BEGIN', 'r', 'ERR'),
                    ('BEGIN', '$', 'ERR'),
                    ('SINK', '|', 'SINK'),
                    ('BEGIN', ']', 'ERR'),
                    ('ERR', 'Y', 'ERR'),
                    ('ERR', 'r', 'ERR'),
                    ('ERR', '`', 'ERR'),
                    ('SIGEND', 'z', 'SINK'),
                    ('END', 'N', 'SINK'),
                    ('BEGIN', ';', 'ERR'),
                    ('SINK', 'C', 'SINK'),
                    ('ERR', 'Z', 'ERR'),
                    ('END', 'M', 'SINK'),
                    ('BEGIN', '6', 'ERR'),
                    ('ERR', 'H', 'ERR'),
                    ('END', 'G', 'SINK'),
                    ('END', 'l', 'SINK'),
                    ('END', 'f', 'SINK'),
                    ('FSLASH', 'u', 'ERR'),
                    ('BEGIN', '/', 'FSLASH'),
                    ('ERR', 'g', 'ERR'),
                    ('ERR', 'O', 'ERR'),
                    ('SIGEND', 'R', 'SINK'),
                    ('BEGIN', 'q', 'ERR'),
                    ('FSLASH', 'E', 'ERR'),
                    ('SINK', '!', 'SINK'),
                    ('SINK', 'M', 'SINK'),
                    ('SIGEND', 'Y', 'SINK'),
                    ('SINK', '\\', 'SINK'),
                    ('END', '2', 'SINK'),
                    ('ERR', '9', 'ERR'),
                    ('FSLASH', 'H', 'ERR'),
                    ('BEGIN', 'Y', 'ERR'),
                    ('ERR', 'U', 'ERR'),
                    ('FSLASH', 'Z', 'ERR'),
                    ('BEGIN', 'a', 'ERR'),
                    ('FSLASH', '8', 'ERR'),
                    ('BEGIN', '7', 'ERR'),
                    ('BEGIN', 'L', 'ERR'),
                    ('SIGEND', '+', 'SINK'),
                    ('ERR', ':', 'ERR'),
                    ('SIGEND', 'P', 'SINK'),
                    ('ERR', 'V', 'ERR'),
                    ('SIGEND', '\x0c', 'SINK'),
                    ('SINK', 'h', 'SINK'),
                    ('END', 'g', 'SINK'),
                    ('SINK', '#', 'SINK'),
                    ('ERR', 'D', 'ERR'),
                    ('SIGEND', 'v', 'SINK'),
                    ('SINK', 'O', 'SINK'),
                    ('BEGIN', 'w', 'ERR'),
                    ('END', '4', 'SINK'),
                    ('FSLASH', 'D', 'ERR'),
                    ('SIGEND', 'G', 'SINK'),
                    ('FSLASH', 'W', 'ERR'),
                    ('FSLASH', 'm', 'ERR'),
                    ('SINK', 'J', 'SINK'),
                    ('SINK', '@', 'SINK'),
                    ('ERR', '/', 'ERR'),
                    ('END', '+', 'SINK'),
                    ('SIGEND', ')', 'SINK'),
                    ('SINK', 'l', 'SINK'),
                    ('FSLASH', '%', 'ERR'),
                    ('ERR', '\t', 'ERR'),
                    ('END', 'e', 'SINK'),
                    ('ERR', 'w', 'ERR'),
                    ('END', 'C', 'SINK'),
                    ('END', 'h', 'SINK'),
                    ('BEGIN', 'K', 'ERR'),
                    ('BEGIN', '<', 'ERR'),
                    ('FSLASH', 'F', 'ERR'),
                    ('ERR', 'x', 'ERR'),
                    ('BEGIN', '3', 'ERR'),
                    ('BEGIN', 'H', 'ERR'),
                    ('FSLASH', '5', 'ERR'),
                    ('SINK', '=', 'SINK'),
                    ('END', 'O', 'SINK'),
                    ('END', 'T', 'SINK'),
                    ('FSLASH', '7', 'ERR'),
                    ('BEGIN', '~', 'ERR'),
                    ('BEGIN', '0', 'ERR'),
                    ('SIGEND', ']', 'SINK'),
                    ('BEGIN', 'o', 'ERR'),
                    ('FSLASH', '!', 'ERR'),
                    ('SIGEND', 'T', 'SINK'),
                    ('FSLASH', 'j', 'ERR'),
                    ('SINK', ')', 'SINK'),
                    ('ERR', '&', 'ERR'),
                    ('END', 'c', 'SINK'),
                    ('SINK', "'", 'SINK'),
                    ('END', '>', 'SINK'),
                    ('SIGEND', 'Q', 'SINK'),
                    ('BEGIN', 'G', 'ERR'),
                    ('SIGEND', '[', 'SINK'),
                    ('BEGIN', '8', 'ERR'),
                    ('ERR', 'm', 'ERR'),
                    ('SINK', 'N', 'SINK'),
                    ('END', 'J', 'SINK'),
                    ('FSLASH', 'B', 'ERR'),
                    ('ERR', 't', 'ERR'),
                    ('FSLASH', 'g', 'ERR'),
                    ('FSLASH', '\x0c', 'ERR'),
                    ('SIGEND', '#', 'SINK'),
                    ('SINK', 'z', 'SINK'),
                    ('SIGEND', '-', 'SINK'),
                    ('SINK', 'p', 'SINK'),
                    ('END', 'o', 'SINK'),
                    ('SINK', '+', 'SINK'),
                    ('END', ':', 'SINK'),
                    ('END', 'a', 'SINK'),
                    ('BEGIN', '{', 'ERR'),
                    ('SIGEND', '_', 'SINK'),
                    ('SINK', 'R', 'SINK'),
                    ('FSLASH', '*', 'SINK'),
                    ('BEGIN', 'm', 'ERR'),
                    ('BEGIN', "'", 'ERR'),
                    ('ERR', "'", 'ERR'),
                    ('ERR', 'C', 'ERR'),
                    ('SIGEND', '\n', 'SINK'),
                    ('SIGEND', '!', 'SINK'),
                    ('BEGIN', '\t', 'ERR'),
                    ('END', 'm', 'SINK'),
                    ('BEGIN', '^', 'ERR'),
                    ('SIGEND', '>', 'SINK'),
                    ('FSLASH', 'n', 'ERR'),
                    ('ERR', '(', 'ERR'),
                    ('SINK', '}', 'SINK'),
                    ('END', 'P', 'SINK'),
                    ('FSLASH', '\x0b', 'ERR'),
                    ('SIGEND', '`', 'SINK'),
                    ('BEGIN', '4', 'ERR'),
                    ('END', 'I', 'SINK'),
                    ('FSLASH', 'N', 'ERR'),
                    ('SIGEND', '%', 'SINK'),
                    ('BEGIN', '@', 'ERR'),
                    ('SINK', '$', 'SINK'),
                    ('BEGIN', '5', 'ERR'),
                    ('SIGEND', '2', 'SINK'),
                    ('SINK', '"', 'SINK'),
                    ('SINK', '\x0b', 'SINK'),
                    ('SIGEND', '<', 'SINK'),
                    ('SINK', 'u', 'SINK'),
                    ('SINK', '<', 'SINK'),
                    ('SIGEND', 'U', 'SINK'),
                    ('ERR', 'T', 'ERR'),
                    ('END', 'U', 'SINK'),
                    ('FSLASH', ':', 'ERR'),
                    ('ERR', '#', 'ERR'),
                    ('BEGIN', '`', 'ERR'),
                    ('SIGEND', '0', 'SINK'),
                    ('FSLASH', ';', 'ERR'),
                    ('SINK', '~', 'SINK'),
                    ('BEGIN', 'Z', 'ERR'),
                    ('ERR', '\x0b', 'ERR'),
                    ('ERR', '$', 'ERR'),
                    ('END', 'k', 'SINK'),
                    ('END', '&', 'SINK'),
                    ('FSLASH', 't', 'ERR'),
                    ('SIGEND', 'S', 'SINK'),
                    ('SINK', 'V', 'SINK'),
                    ('ERR', '\x0c', 'ERR'),
                    ('ERR', 'Q', 'ERR'),
                    ('END', 'B', 'SINK'),
                    ('BEGIN', '1', 'ERR'),
                    ('END', 'i', 'SINK'),
                    ('SIGEND', 'd', 'SINK'),
                    ('SIGEND', '\r', 'SINK'),
                    ('FSLASH', '&', 'ERR'),
                    ('SIGEND', 'n', 'SINK'),
                    ('ERR', '[', 'ERR'),
                    ('SINK', '(', 'SINK'),
                    ('BEGIN', 'V', 'ERR'),
                    ('SIGEND', '6', 'SINK'),
                    ('BEGIN', 'n', 'ERR'),
                    ('SIGEND', 'x', 'SINK'),
                    ('SINK', 'T', 'SINK'),
                    ('FSLASH', '/', 'ERR'),
                    ('FSLASH', '\r', 'ERR'),
                    ('BEGIN', 'b', 'ERR'),
                    ('SIGEND', 'b', 'SINK'),
                    ('END', 'j', 'SINK'),
                    ('FSLASH', '{', 'ERR'),
                    ('ERR', 'o', 'ERR'),
                    ('SINK', ',', 'SINK'),
                    ('FSLASH', 'e', 'ERR'),
                    ('ERR', 'I', 'ERR'),
                    ('ERR', 'b', 'ERR'),
                    ('END', '%', 'SINK'),
                    ('SIGEND', '4', 'SINK'),
                    ('ERR', 'P', 'ERR'),
                    ('SINK', '\t', 'SINK'),
                    ('ERR', '6', 'ERR'),
                    ('END', '^', 'SINK'),
                    ('FSLASH', 'C', 'ERR'),
                    ('ERR', 'J', 'ERR'),
                    ('END', ']', 'SINK'),
                    ('FSLASH', '"', 'ERR'),
                    ('END', 'W', 'SINK'),
                    ('END', '|', 'SINK'),
                    ('ERR', ';', 'ERR'),
                    ('ERR', 'W', 'ERR'),
                    ('END', 'v', 'SINK'),
                    ('SIGEND', 'V', 'SINK'),
                    ('END', 'Z', 'SINK'),
                    ('END', ' ', 'SINK'),
                    ('SIGEND', 'B', 'SINK'),
                    ('FSLASH', '\t', 'ERR'),
                    ('FSLASH', 'U', 'ERR'),
                    ('SIGEND', 'I', 'SINK'),
                    ('FSLASH', '$', 'ERR'),
                    ('SIGEND', '*', 'SIGEND'),
                    ('ERR', ')', 'ERR'),
                    ('FSLASH', 'X', 'ERR'),
                    ('BEGIN', ')', 'ERR'),
                    ('SINK', '%', 'SINK'),
                    ('ERR', '0', 'ERR'),
                    ('END', '\r', 'SINK'),
                    ('END', ',', 'SINK'),
                    ('FSLASH', 'O', 'ERR'),
                    ('BEGIN', '\\', 'ERR'),
                    ('BEGIN', '!', 'ERR'),
                    ('ERR', '*', 'ERR'),
                    ('SIGEND', '@', 'SINK'),
                    ('SIGEND', '/', 'END'),
                    ('SIGEND', '|', 'SINK'),
                    ('SINK', 'X', 'SINK'),
                    ('END', 'w', 'SINK'),
                    ('FSLASH', '.', 'ERR'),
                    ('SIGEND', 'f', 'SINK'),
                    ('ERR', 'v', 'ERR'),
                    ('SIGEND', 'w', 'SINK'),
                    ('FSLASH', 'y', 'ERR'),
                    ('SINK', '0', 'SINK'),
                    ('END', '!', 'SINK'),
                    ('END', ';', 'SINK'),
                    ('BEGIN', '}', 'ERR'),
                    ('ERR', 'y', 'ERR'),
                    ('END', 'u', 'SINK'),
                    ('END', 'Y', 'SINK'),
                    ('END', 'S', 'SINK'),
                    ('END', 'x', 'SINK'),
                    ('BEGIN', '[', 'ERR'),
                    ('BEGIN', '\x0c', 'ERR'),
                    ('ERR', 'z', 'ERR'),
                    ('END', '-', 'SINK'),
                    ('FSLASH', 'V', 'ERR'),
                    ('BEGIN', 'c', 'ERR'),
                    ('ERR', 'h', 'ERR'),
                    ('END', "'", 'SINK'),
                    ('END', 'L', 'SINK'),
                    ('BEGIN', 'g', 'ERR'),
                    ('BEGIN', 'z', 'ERR'),
                    ('END', 'F', 'SINK'),
                    ('FSLASH', 'K', 'ERR'),
                    ('BEGIN', 'X', 'ERR'),
                    ('FSLASH', 'd', 'ERR'),
                    ('BEGIN', 'E', 'ERR'),
                    ('SINK', '\n', 'SINK'),
                    ('SINK', 's', 'SINK'),
                    ('SIGEND', 'F', 'SINK'),
                    ('END', '_', 'SINK'),
                    ('END', 'd', 'SINK'),
                    ('ERR', 'a', 'ERR'),
                    ('SIGEND', 'M', 'SINK'),
                    ('FSLASH', 'v', 'ERR'),
                    ('SINK', '?', 'SINK'),
                    ('SIGEND', 'y', 'SINK'),
                    ('END', '(', 'SINK'),
                    ('SIGEND', 'Z', 'SINK'),
                    ('BEGIN', ' ', 'ERR'),
                    ('BEGIN', 'y', 'ERR'),
                    ('ERR', 'u', 'ERR'),
                    ('SIGEND', 'D', 'SINK'),
                    ('BEGIN', '2', 'ERR'),
                    ('ERR', 'c', 'ERR'),
                    ('END', 's', 'SINK'),
                    ('SIGEND', 'A', 'SINK'),
                    ('BEGIN', 'W', 'ERR'),
                    ('BEGIN', 'l', 'ERR'),
                    ('SIGEND', 'K', 'SINK'),
                    ('FSLASH', '@', 'ERR'),
                    ('ERR', ']', 'ERR'),
                    ('SIGEND', '5', 'SINK'),
                    ('FSLASH', 'R', 'ERR'),
                    ('ERR', 'd', 'ERR'),
                    ('FSLASH', '+', 'ERR'),
                    ('SIGEND', 'g', 'SINK'),
                    ('FSLASH', 'w', 'ERR'),
                    ('BEGIN', 'T', 'ERR'),
                    ('END', '\n', 'SINK'),
                    ('SINK', 'j', 'SINK'),
                    ('SIGEND', 'X', 'SINK'),
                    ('ERR', '^', 'ERR'),
                    ('SINK', '`', 'SINK'),
                    ('BEGIN', 'i', 'ERR'),
                    ('ERR', 'L', 'ERR'),
                    ('FSLASH', 'k', 'ERR'),
                    ('END', 'q', 'SINK'),
                    ('BEGIN', 'x', 'ERR'),
                    ('SIGEND', 'O', 'SINK'),
                    ('SINK', 'B', 'SINK'),
                    ('SINK', '6', 'SINK'),
                    ('BEGIN', '"', 'ERR'),
                    ('END', '#', 'SINK'),
                    ('END', 'H', 'SINK'),
                    ('BEGIN', '-', 'ERR'),
                    ('ERR', 's', 'ERR'),
                    ('END', '}', 'SINK'),
                    ('FSLASH', 'f', 'ERR'),
                    ('SIGEND', '.', 'SINK'),
                    ('SINK', 'w', 'SINK'),
                    ('SINK', 'm', 'SINK'),
                    ('END', '`', 'SINK'),
                    ('BEGIN', 'S', 'ERR'),
                    ('BEGIN', 'h', 'ERR'),
                    ('ERR', '=', 'ERR'),
                    ('FSLASH', 'L', 'ERR'),
                    ('SINK', ':', 'SINK'),
                    ('FSLASH', '^', 'ERR'),
                    ('END', '/', 'SINK'),
                    ('BEGIN', 'P', 'ERR'),
                    ('SIGEND', '}', 'SINK'),
                    ('SIGEND', '"', 'SINK'),
                    ('SINK', '{', 'SINK'),
                    ('SIGEND', '^', 'SINK'),
                    ('SIGEND', ',', 'SINK'),
                    ('SINK', 'q', 'SINK'),
                    ('SIGEND', 'E', 'SINK'),
                    ('FSLASH', "'", 'ERR'),
                    ('FSLASH', '\n', 'ERR'),
                    ('SIGEND', 'q', 'SINK'),
                    ('FSLASH', 'p', 'ERR'),
                    ('SIGEND', '{', 'SINK'),
                    ('SIGEND', ' ', 'SINK'),
                    ('BEGIN', '\x0b', 'ERR'),
                    ('SINK', 'n', 'SINK'),
                    ('SIGEND', '\\', 'SINK'),
                    ('FSLASH', 'b', 'ERR'),
                    ('END', ')', 'SINK'),
                    ('ERR', '{', 'ERR'),
                    ('END', 'b', 'SINK'),
                    ('END', '{', 'SINK'),
                    ('END', '6', 'SINK'),
                    ('BEGIN', 'O', 'ERR'),
                    ('BEGIN', 'd', 'ERR'),
                    ('SIGEND', 'C', 'SINK'),
                    ('SINK', 'F', 'SINK'),
                    ('BEGIN', '\n', 'ERR'),
                    ('SIGEND', 'm', 'SINK'),
                    ('ERR', '|', 'ERR'),
                    ('SINK', 'r', 'SINK'),
                    ('SINK', 'Q', 'SINK'),
                    ('END', 'y', 'SINK'),
                    ('FSLASH', '6', 'ERR'),
                    ('SINK', '>', 'SINK'),
                    ('ERR', 'K', 'ERR'),
                    ('BEGIN', 'j', 'ERR'),
                    ('FSLASH', '=', 'ERR'),
                    ('SINK', 'S', 'SINK'),
                    ('BEGIN', '&', 'ERR'),
                    ('SIGEND', '&', 'SINK'),
                    ('BEGIN', 'D', 'ERR'),
                    ('SIGEND', '7', 'SINK'),
                    ('ERR', 'q', 'ERR'),
                    ('BEGIN', 'C', 'ERR'),
                    ('FSLASH', '(', 'ERR'),
                    ('SIGEND', 'h', 'SINK'),
                    ('SINK', 'D', 'SINK'),
                    ('ERR', '5', 'ERR'),
                    ('BEGIN', 'U', 'ERR'),
                    ('FSLASH', 'Y', 'ERR'),
                    ('BEGIN', '.', 'ERR'),
                    ('BEGIN', '9', 'ERR'),
                    ('SIGEND', 'u', 'SINK'),
                    ('BEGIN', '=', 'ERR'),
                    ('SIGEND', ':', 'SINK'),
                    ('ERR', 'R', 'ERR'),
                    ('END', '5', 'SINK'),
                    ('SIGEND', '$', 'SINK'),
                    ('ERR', '@', 'ERR'),
                    ('SINK', 'y', 'SINK'),
                    ('ERR', 'n', 'ERR'),
                    ('SINK', 'o', 'SINK'),
                    ('END', 'n', 'SINK'),
                    ('FSLASH', 'S', 'ERR'),
                    ('FSLASH', 'h', 'ERR'),
                    ('FSLASH', '2', 'ERR'),
                    ('ERR', '+', 'ERR'),
                    ('SINK', ';', 'SINK'),
                    ('ERR', 'G', 'ERR'),
                    ('ERR', '\\', 'ERR'),
                    ('SIGEND', 's', 'SINK'),
                    ('SIGEND', '8', 'SINK'),
                    ('SINK', 'v', 'SINK'),
                    ('FSLASH', 'M', 'ERR'),
                    ('ERR', ',', 'ERR'),
                    ('SINK', 'U', 'SINK'),
                    ('SINK', 'W', 'SINK'),
                    ('FSLASH', ' ', 'ERR'),
                    ('END', '0', 'SINK'),
                    ('ERR', '1', 'ERR'),
                    ('BEGIN', 'Q', 'ERR'),
                    ('FSLASH', '3', 'ERR'),
                    ('BEGIN', 'k', 'ERR'),
                    ('ERR', '2', 'ERR'),
                    ('FSLASH', 'q', 'ERR'),
                    ('SINK', 'Y', 'SINK'),
                    ('ERR', '<', 'ERR'),
                    ('END', '<', 'SINK'),
                    ('FSLASH', '_', 'ERR'),
                    ('SIGEND', '\x0b', 'SINK'),
                    ('SIGEND', 'l', 'SINK'),
                    ('SINK', 'H', 'SINK'),
                    ('FSLASH', '>', 'ERR'),
                    ('END', '*', 'SIGEND'),
                    ('SIGEND', "'", 'SINK'),
                    ('SINK', 't', 'SINK'),
                    ('BEGIN', 'e', 'ERR'),
                    ('SINK', ' ', 'SINK'),
                    ('SINK', '[', 'SINK'),
                    ('END', '1', 'SINK'),
                    ('END', 'K', 'SINK'),
                    ('SIGEND', '\t', 'SINK'),
                    ('SINK', 'L', 'SINK'),
                    ('BEGIN', 'M', 'ERR'),
                    ('ERR', 'i', 'ERR'),
                    ('ERR', 'p', 'ERR'),
                    ('BEGIN', 'v', 'ERR'),
                    ('FSLASH', 'c', 'ERR'),
                    ('BEGIN', '(', 'ERR'),
                    ('FSLASH', 'T', 'ERR'),
                    ('BEGIN', 'A', 'ERR'),
                    ('ERR', 'j', 'ERR'),
                    ('END', '=', 'SINK'),
                    ('FSLASH', 's', 'ERR'),
                    ('ERR', 'X', 'ERR'),
                    ('END', '7', 'SINK'),
                    ('END', '\\', 'SINK'),
                    ('FSLASH', '?', 'ERR'),
                    ('END', 'V', 'SINK'),
                    ('FSLASH', '[', 'ERR'),
                    ('END', 'R', 'SINK'),
                    ('SINK', 'c', 'SINK'),
                    ('BEGIN', ':', 'ERR'),
                    ('END', 't', 'SINK'),
                    ('ERR', '>', 'ERR'),
                    ('ERR', '_', 'ERR'),
                    ('FSLASH', ')', 'ERR'),
                    ('SINK', '1', 'SINK'),
                    ('SINK', ']', 'SINK'),
                    ('SINK', '/', 'SINK'),
                    ('SIGEND', 'i', 'SINK'),
                    ('END', '8', 'SINK'),
                    ('SIGEND', 'J', 'SINK'),
                    ('FSLASH', 'x', 'ERR'),
                    ('BEGIN', 'I', 'ERR'),
                    ('ERR', 'e', 'ERR'),
                    ('FSLASH', 'J', 'ERR'),
                    ('END', '\x0c', 'SINK'),
                    ('FSLASH', 'A', 'ERR'),
                    ('FSLASH', 'o', 'ERR'),
                    ('FSLASH', '4', 'ERR'),
                    ('SIGEND', ';', 'SINK'),
                    ('FSLASH', 'P', 'ERR'),
                    ('ERR', 'M', 'ERR'),
                    ('ERR', 'f', 'ERR'),
                    ('SINK', 'x', 'SINK'),
                    ('FSLASH', '-', 'ERR'),
                    ('SINK', '3', 'SINK'),
                    ('END', '"', 'SINK'),
                    ('SINK', '_', 'SINK'),
                    ('BEGIN', 's', 'ERR'),
                    ('END', '$', 'SINK'),
                    ('FSLASH', '<', 'ERR'),
                    ('FSLASH', 'G', 'ERR'),
                    ('SINK', 'Z', 'SINK'),
                    ('SIGEND', 'H', 'SINK'),
                    ('ERR', 'N', 'ERR'),
                    ('SINK', 'P', 'SINK'),
                    ('FSLASH', 'I', 'ERR'),
                    ('SINK', '*', 'SIGEND'),
                    ('ERR', '?', 'ERR'),
                    ('SIGEND', '?', 'SINK'),
                    ('FSLASH', 'a', 'ERR'),
                    ('SIGEND', '9', 'SINK'),
                    ('ERR', 'E', 'ERR'),
                    ('SINK', '&', 'SINK'),
                    ('END', '9', 'SINK'),
                    ('ERR', ' ', 'ERR'),
                    ('SIGEND', '=', 'SINK'),
                    ('END', '3', 'SINK'),
                    ('END', 'X', 'SINK'),
                    ('BEGIN', ',', 'ERR'),
                    ('BEGIN', '>', 'ERR'),
                    ('SINK', 'g', 'SINK'),
                    ('END', 'p', 'SINK'),
                    ('BEGIN', '#', 'ERR'),
                    ('FSLASH', '0', 'ERR'),
                    ('ERR', '-', 'ERR'),
                    ('FSLASH', '\\', 'ERR'),
                    ('END', '?', 'SINK'),
                    ('END', 'D', 'SINK'),
                    ('SINK', '5', 'SINK'),
                    ('ERR', '.', 'ERR'),
                    ('BEGIN', '|', 'ERR'),
                    ('SINK', 'k', 'SINK'),
                    ('ERR', '\r', 'ERR'),
                    ('SIGEND', 'N', 'SINK'),
                    ('SINK', 'a', 'SINK'),
                    ('BEGIN', 'B', 'ERR'),
                    ('END', 'Q', 'SINK'),
                    ('FSLASH', '|', 'ERR'),
                    ('BEGIN', 'R', 'ERR'),
                    ('SINK', '9', 'SINK'),
                    ('SIGEND', 'j', 'SINK'),
                    ('SINK', '7', 'SINK'),
                    ('END', '.', 'SINK'),
                    ('SIGEND', 'a', 'SINK'),
                    ('SIGEND', 'k', 'SINK'),
                    ('FSLASH', '`', 'ERR'),
                    ('ERR', '}', 'ERR'),
                    ('SINK', '^', 'SINK'),
                    ('SIGEND', 'L', 'SINK'),
                    ('FSLASH', 'r', 'ERR'),
                    ('ERR', 'k', 'ERR'),
                    ('END', 'r', 'SINK'),
                    ('BEGIN', '?', 'ERR'),
                    ('BEGIN', '_', 'ERR'),
                    ('BEGIN', 't', 'ERR'),
                    ('SIGEND', '3', 'SINK'),
                    ('ERR', '~', 'ERR'),
                    ('FSLASH', '1', 'ERR'),
                    ('ERR', 'F', 'ERR'),
                    ('ERR', 'l', 'ERR'),
                    ('FSLASH', '#', 'ERR'),
                    ('SIGEND', 'o', 'SINK'),
                    ('SINK', 'b', 'SINK'),
                    ('FSLASH', 'z', 'ERR'),
                    ('SINK', 'A', 'SINK')
                ]),
                'S': 'BEGIN',
                'F': set(['END'])
            }
        },
        {
            'name': 'Character',
            'valid': True,
            'expressions': {
                'char': "'[^\e]'",
            },
            'DFA': {
                'Q': set(['S', '_1', '_2', 'F', 'Err']),
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\\\\]^_`{|}~'),
                'T': set([
                    ('S', '#', 'Err'),
                    ('S', ';', 'Err'),
                    ('S', '0', 'Err'),
                    ('S', '1', 'Err'),
                    ('S', '2', 'Err'),
                    ('S', '3', 'Err'),
                    ('S', '4', 'Err'),
                    ('S', '5', 'Err'),
                    ('S', '6', 'Err'),
                    ('S', '7', 'Err'),
                    ('S', '8', 'Err'),
                    ('S', '9', 'Err'),
                    ('S', ' ', 'Err'),
                    ('S', '\t', 'Err'),
                    ('S', '\v', 'Err'),
                    ('S', '\f', 'Err'),
                    ('S', '\r', 'Err'),
                    ('S', '\n', 'Err'),
                    ('S', 'a', 'Err'),
                    ('S', 'b', 'Err'),
                    ('S', 'c', 'Err'),
                    ('S', 'd', 'Err'),
                    ('S', 'e', 'Err'),
                    ('S', 'f', 'Err'),
                    ('S', 'g', 'Err'),
                    ('S', 'h', 'Err'),
                    ('S', 'i', 'Err'),
                    ('S', 'j', 'Err'),
                    ('S', 'k', 'Err'),
                    ('S', 'l', 'Err'),
                    ('S', 'm', 'Err'),
                    ('S', 'n', 'Err'),
                    ('S', 'o', 'Err'),
                    ('S', 'p', 'Err'),
                    ('S', 'q', 'Err'),
                    ('S', 'r', 'Err'),
                    ('S', 's', 'Err'),
                    ('S', 't', 'Err'),
                    ('S', 'u', 'Err'),
                    ('S', 'v', 'Err'),
                    ('S', 'w', 'Err'),
                    ('S', 'x', 'Err'),
                    ('S', 'y', 'Err'),
                    ('S', 'z', 'Err'),
                    ('S', 'A', 'Err'),
                    ('S', 'B', 'Err'),
                    ('S', 'C', 'Err'),
                    ('S', 'D', 'Err'),
                    ('S', 'E', 'Err'),
                    ('S', 'F', 'Err'),
                    ('S', 'G', 'Err'),
                    ('S', 'H', 'Err'),
                    ('S', 'I', 'Err'),
                    ('S', 'J', 'Err'),
                    ('S', 'K', 'Err'),
                    ('S', 'L', 'Err'),
                    ('S', 'M', 'Err'),
                    ('S', 'N', 'Err'),
                    ('S', 'O', 'Err'),
                    ('S', 'P', 'Err'),
                    ('S', 'Q', 'Err'),
                    ('S', 'R', 'Err'),
                    ('S', 'S', 'Err'),
                    ('S', 'T', 'Err'),
                    ('S', 'U', 'Err'),
                    ('S', 'V', 'Err'),
                    ('S', 'W', 'Err'),
                    ('S', 'X', 'Err'),
                    ('S', 'Y', 'Err'),
                    ('S', 'Z', 'Err'),
                    ('S', '!', 'Err'),
                    ('S', '"', 'Err'),
                    ('S', '$', 'Err'),
                    ('S', '%', 'Err'),
                    ('S', '&', 'Err'),
                    ('S', '\'', '_1'),
                    ('S', '(', 'Err'),
                    ('S', ')', 'Err'),
                    ('S', '*', 'Err'),
                    ('S', '+', 'Err'),
                    ('S', ',', 'Err'),
                    ('S', '-', 'Err'),
                    ('S', '.', 'Err'),
                    ('S', '/', 'Err'),
                    ('S', ':', 'Err'),
                    ('S', '<', 'Err'),
                    ('S', '=', 'Err'),
                    ('S', '>', 'Err'),
                    ('S', '?', 'Err'),
                    ('S', '@', 'Err'),
                    ('S', '[', 'Err'),
                    ('S', '\\', 'Err'),
                    ('S', ']', 'Err'),
                    ('S', '^', 'Err'),
                    ('S', '_', 'Err'),
                    ('S', '`', 'Err'),
                    ('S', '{', 'Err'),
                    ('S', '|', 'Err'),
                    ('S', '}', 'Err'),
                    ('S', '~', 'Err'),
                    ('_1', '\n', '_2'),
                    ('_1', '#', '_2'),
                    ('_1', ';', '_2'),
                    ('_1', '0', '_2'),
                    ('_1', '1', '_2'),
                    ('_1', '2', '_2'),
                    ('_1', '3', '_2'),
                    ('_1', '4', '_2'),
                    ('_1', '5', '_2'),
                    ('_1', '6', '_2'),
                    ('_1', '7', '_2'),
                    ('_1', '8', '_2'),
                    ('_1', '9', '_2'),
                    ('_1', ' ', '_2'),
                    ('_1', '\t', '_2'),
                    ('_1', '\v', '_2'),
                    ('_1', '\f', '_2'),
                    ('_1', '\r', '_2'),
                    ('_1', 'a', '_2'),
                    ('_1', 'b', '_2'),
                    ('_1', 'c', '_2'),
                    ('_1', 'd', '_2'),
                    ('_1', 'e', '_2'),
                    ('_1', 'f', '_2'),
                    ('_1', 'g', '_2'),
                    ('_1', 'h', '_2'),
                    ('_1', 'i', '_2'),
                    ('_1', 'j', '_2'),
                    ('_1', 'k', '_2'),
                    ('_1', 'l', '_2'),
                    ('_1', 'm', '_2'),
                    ('_1', 'n', '_2'),
                    ('_1', 'o', '_2'),
                    ('_1', 'p', '_2'),
                    ('_1', 'q', '_2'),
                    ('_1', 'r', '_2'),
                    ('_1', 's', '_2'),
                    ('_1', 't', '_2'),
                    ('_1', 'u', '_2'),
                    ('_1', 'v', '_2'),
                    ('_1', 'w', '_2'),
                    ('_1', 'x', '_2'),
                    ('_1', 'y', '_2'),
                    ('_1', 'z', '_2'),
                    ('_1', 'A', '_2'),
                    ('_1', 'B', '_2'),
                    ('_1', 'C', '_2'),
                    ('_1', 'D', '_2'),
                    ('_1', 'E', '_2'),
                    ('_1', 'F', '_2'),
                    ('_1', 'G', '_2'),
                    ('_1', 'H', '_2'),
                    ('_1', 'I', '_2'),
                    ('_1', 'J', '_2'),
                    ('_1', 'K', '_2'),
                    ('_1', 'L', '_2'),
                    ('_1', 'M', '_2'),
                    ('_1', 'N', '_2'),
                    ('_1', 'O', '_2'),
                    ('_1', 'P', '_2'),
                    ('_1', 'Q', '_2'),
                    ('_1', 'R', '_2'),
                    ('_1', 'S', '_2'),
                    ('_1', 'T', '_2'),
                    ('_1', 'U', '_2'),
                    ('_1', 'V', '_2'),
                    ('_1', 'W', '_2'),
                    ('_1', 'X', '_2'),
                    ('_1', 'Y', '_2'),
                    ('_1', 'Z', '_2'),
                    ('_1', '!', '_2'),
                    ('_1', '"', '_2'),
                    ('_1', '$', '_2'),
                    ('_1', '%', '_2'),
                    ('_1', '&', '_2'),
                    ('_1', '\'', '_2'),
                    ('_1', '(', '_2'),
                    ('_1', ')', '_2'),
                    ('_1', '*', '_2'),
                    ('_1', '+', '_2'),
                    ('_1', ',', '_2'),
                    ('_1', '-', '_2'),
                    ('_1', '.', '_2'),
                    ('_1', '/', '_2'),
                    ('_1', ':', '_2'),
                    ('_1', '<', '_2'),
                    ('_1', '=', '_2'),
                    ('_1', '>', '_2'),
                    ('_1', '?', '_2'),
                    ('_1', '@', '_2'),
                    ('_1', '[', '_2'),
                    ('_1', '\\', '_2'),
                    ('_1', ']', '_2'),
                    ('_1', '^', '_2'),
                    ('_1', '_', '_2'),
                    ('_1', '`', '_2'),
                    ('_1', '{', '_2'),
                    ('_1', '|', '_2'),
                    ('_1', '}', '_2'),
                    ('_1', '~', '_2'),
                    ('_2', '\n', 'Err'),
                    ('_2', '#', 'Err'),
                    ('_2', ';', 'Err'),
                    ('_2', '0', 'Err'),
                    ('_2', '1', 'Err'),
                    ('_2', '2', 'Err'),
                    ('_2', '3', 'Err'),
                    ('_2', '4', 'Err'),
                    ('_2', '5', 'Err'),
                    ('_2', '6', 'Err'),
                    ('_2', '7', 'Err'),
                    ('_2', '8', 'Err'),
                    ('_2', '9', 'Err'),
                    ('_2', ' ', 'Err'),
                    ('_2', '\t', 'Err'),
                    ('_2', '\v', 'Err'),
                    ('_2', '\f', 'Err'),
                    ('_2', '\r', 'Err'),
                    ('_2', 'a', 'Err'),
                    ('_2', 'b', 'Err'),
                    ('_2', 'c', 'Err'),
                    ('_2', 'd', 'Err'),
                    ('_2', 'e', 'Err'),
                    ('_2', 'f', 'Err'),
                    ('_2', 'g', 'Err'),
                    ('_2', 'h', 'Err'),
                    ('_2', 'i', 'Err'),
                    ('_2', 'j', 'Err'),
                    ('_2', 'k', 'Err'),
                    ('_2', 'l', 'Err'),
                    ('_2', 'm', 'Err'),
                    ('_2', 'n', 'Err'),
                    ('_2', 'o', 'Err'),
                    ('_2', 'p', 'Err'),
                    ('_2', 'q', 'Err'),
                    ('_2', 'r', 'Err'),
                    ('_2', 's', 'Err'),
                    ('_2', 't', 'Err'),
                    ('_2', 'u', 'Err'),
                    ('_2', 'v', 'Err'),
                    ('_2', 'w', 'Err'),
                    ('_2', 'x', 'Err'),
                    ('_2', 'y', 'Err'),
                    ('_2', 'z', 'Err'),
                    ('_2', 'A', 'Err'),
                    ('_2', 'B', 'Err'),
                    ('_2', 'C', 'Err'),
                    ('_2', 'D', 'Err'),
                    ('_2', 'E', 'Err'),
                    ('_2', 'F', 'Err'),
                    ('_2', 'G', 'Err'),
                    ('_2', 'H', 'Err'),
                    ('_2', 'I', 'Err'),
                    ('_2', 'J', 'Err'),
                    ('_2', 'K', 'Err'),
                    ('_2', 'L', 'Err'),
                    ('_2', 'M', 'Err'),
                    ('_2', 'N', 'Err'),
                    ('_2', 'O', 'Err'),
                    ('_2', 'P', 'Err'),
                    ('_2', 'Q', 'Err'),
                    ('_2', 'R', 'Err'),
                    ('_2', 'S', 'Err'),
                    ('_2', 'T', 'Err'),
                    ('_2', 'U', 'Err'),
                    ('_2', 'V', 'Err'),
                    ('_2', 'W', 'Err'),
                    ('_2', 'X', 'Err'),
                    ('_2', 'Y', 'Err'),
                    ('_2', 'Z', 'Err'),
                    ('_2', '!', 'Err'),
                    ('_2', '"', 'Err'),
                    ('_2', '$', 'Err'),
                    ('_2', '%', 'Err'),
                    ('_2', '&', 'Err'),
                    ('_2', '\'', 'F'),
                    ('_2', '(', 'Err'),
                    ('_2', ')', 'Err'),
                    ('_2', '*', 'Err'),
                    ('_2', '+', 'Err'),
                    ('_2', ',', 'Err'),
                    ('_2', '-', 'Err'),
                    ('_2', '.', 'Err'),
                    ('_2', '/', 'Err'),
                    ('_2', ':', 'Err'),
                    ('_2', '<', 'Err'),
                    ('_2', '=', 'Err'),
                    ('_2', '>', 'Err'),
                    ('_2', '?', 'Err'),
                    ('_2', '@', 'Err'),
                    ('_2', '[', 'Err'),
                    ('_2', '\\', 'Err'),
                    ('_2', ']', 'Err'),
                    ('_2', '^', 'Err'),
                    ('_2', '_', 'Err'),
                    ('_2', '`', 'Err'),
                    ('_2', '{', 'Err'),
                    ('_2', '|', 'Err'),
                    ('_2', '}', 'Err'),
                    ('_2', '~', 'Err'),
                    ('F', '\n', 'Err'),
                    ('F', '#', 'Err'),
                    ('F', ';', 'Err'),
                    ('F', '0', 'Err'),
                    ('F', '1', 'Err'),
                    ('F', '2', 'Err'),
                    ('F', '3', 'Err'),
                    ('F', '4', 'Err'),
                    ('F', '5', 'Err'),
                    ('F', '6', 'Err'),
                    ('F', '7', 'Err'),
                    ('F', '8', 'Err'),
                    ('F', '9', 'Err'),
                    ('F', ' ', 'Err'),
                    ('F', '\t', 'Err'),
                    ('F', '\v', 'Err'),
                    ('F', '\f', 'Err'),
                    ('F', '\r', 'Err'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('F', 'd', 'Err'),
                    ('F', 'e', 'Err'),
                    ('F', 'f', 'Err'),
                    ('F', 'g', 'Err'),
                    ('F', 'h', 'Err'),
                    ('F', 'i', 'Err'),
                    ('F', 'j', 'Err'),
                    ('F', 'k', 'Err'),
                    ('F', 'l', 'Err'),
                    ('F', 'm', 'Err'),
                    ('F', 'n', 'Err'),
                    ('F', 'o', 'Err'),
                    ('F', 'p', 'Err'),
                    ('F', 'q', 'Err'),
                    ('F', 'r', 'Err'),
                    ('F', 's', 'Err'),
                    ('F', 't', 'Err'),
                    ('F', 'u', 'Err'),
                    ('F', 'v', 'Err'),
                    ('F', 'w', 'Err'),
                    ('F', 'x', 'Err'),
                    ('F', 'y', 'Err'),
                    ('F', 'z', 'Err'),
                    ('F', 'A', 'Err'),
                    ('F', 'B', 'Err'),
                    ('F', 'C', 'Err'),
                    ('F', 'D', 'Err'),
                    ('F', 'E', 'Err'),
                    ('F', 'F', 'Err'),
                    ('F', 'G', 'Err'),
                    ('F', 'H', 'Err'),
                    ('F', 'I', 'Err'),
                    ('F', 'J', 'Err'),
                    ('F', 'K', 'Err'),
                    ('F', 'L', 'Err'),
                    ('F', 'M', 'Err'),
                    ('F', 'N', 'Err'),
                    ('F', 'O', 'Err'),
                    ('F', 'P', 'Err'),
                    ('F', 'Q', 'Err'),
                    ('F', 'R', 'Err'),
                    ('F', 'S', 'Err'),
                    ('F', 'T', 'Err'),
                    ('F', 'U', 'Err'),
                    ('F', 'V', 'Err'),
                    ('F', 'W', 'Err'),
                    ('F', 'X', 'Err'),
                    ('F', 'Y', 'Err'),
                    ('F', 'Z', 'Err'),
                    ('F', '!', 'Err'),
                    ('F', '"', 'Err'),
                    ('F', '$', 'Err'),
                    ('F', '%', 'Err'),
                    ('F', '&', 'Err'),
                    ('F', '\'', 'Err'),
                    ('F', '(', 'Err'),
                    ('F', ')', 'Err'),
                    ('F', '*', 'Err'),
                    ('F', '+', 'Err'),
                    ('F', ',', 'Err'),
                    ('F', '-', 'Err'),
                    ('F', '.', 'Err'),
                    ('F', '/', 'Err'),
                    ('F', ':', 'Err'),
                    ('F', '<', 'Err'),
                    ('F', '=', 'Err'),
                    ('F', '>', 'Err'),
                    ('F', '?', 'Err'),
                    ('F', '@', 'Err'),
                    ('F', '[', 'Err'),
                    ('F', '\\', 'Err'),
                    ('F', ']', 'Err'),
                    ('F', '^', 'Err'),
                    ('F', '_', 'Err'),
                    ('F', '`', 'Err'),
                    ('F', '{', 'Err'),
                    ('F', '|', 'Err'),
                    ('F', '}', 'Err'),
                    ('F', '~', 'Err'),
                    ('Err', '\n', 'Err'),
                    ('Err', '#', 'Err'),
                    ('Err', ';', 'Err'),
                    ('Err', '0', 'Err'),
                    ('Err', '1', 'Err'),
                    ('Err', '2', 'Err'),
                    ('Err', '3', 'Err'),
                    ('Err', '4', 'Err'),
                    ('Err', '5', 'Err'),
                    ('Err', '6', 'Err'),
                    ('Err', '7', 'Err'),
                    ('Err', '8', 'Err'),
                    ('Err', '9', 'Err'),
                    ('Err', ' ', 'Err'),
                    ('Err', '\t', 'Err'),
                    ('Err', '\v', 'Err'),
                    ('Err', '\f', 'Err'),
                    ('Err', '\r', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err'),
                    ('Err', 'd', 'Err'),
                    ('Err', 'e', 'Err'),
                    ('Err', 'f', 'Err'),
                    ('Err', 'g', 'Err'),
                    ('Err', 'h', 'Err'),
                    ('Err', 'i', 'Err'),
                    ('Err', 'j', 'Err'),
                    ('Err', 'k', 'Err'),
                    ('Err', 'l', 'Err'),
                    ('Err', 'm', 'Err'),
                    ('Err', 'n', 'Err'),
                    ('Err', 'o', 'Err'),
                    ('Err', 'p', 'Err'),
                    ('Err', 'q', 'Err'),
                    ('Err', 'r', 'Err'),
                    ('Err', 's', 'Err'),
                    ('Err', 't', 'Err'),
                    ('Err', 'u', 'Err'),
                    ('Err', 'v', 'Err'),
                    ('Err', 'w', 'Err'),
                    ('Err', 'x', 'Err'),
                    ('Err', 'y', 'Err'),
                    ('Err', 'z', 'Err'),
                    ('Err', 'A', 'Err'),
                    ('Err', 'B', 'Err'),
                    ('Err', 'C', 'Err'),
                    ('Err', 'D', 'Err'),
                    ('Err', 'E', 'Err'),
                    ('Err', 'F', 'Err'),
                    ('Err', 'G', 'Err'),
                    ('Err', 'H', 'Err'),
                    ('Err', 'I', 'Err'),
                    ('Err', 'J', 'Err'),
                    ('Err', 'K', 'Err'),
                    ('Err', 'L', 'Err'),
                    ('Err', 'M', 'Err'),
                    ('Err', 'N', 'Err'),
                    ('Err', 'O', 'Err'),
                    ('Err', 'P', 'Err'),
                    ('Err', 'Q', 'Err'),
                    ('Err', 'R', 'Err'),
                    ('Err', 'S', 'Err'),
                    ('Err', 'T', 'Err'),
                    ('Err', 'U', 'Err'),
                    ('Err', 'V', 'Err'),
                    ('Err', 'W', 'Err'),
                    ('Err', 'X', 'Err'),
                    ('Err', 'Y', 'Err'),
                    ('Err', 'Z', 'Err'),
                    ('Err', '!', 'Err'),
                    ('Err', '"', 'Err'),
                    ('Err', '$', 'Err'),
                    ('Err', '%', 'Err'),
                    ('Err', '&', 'Err'),
                    ('Err', '\'', 'Err'),
                    ('Err', '(', 'Err'),
                    ('Err', ')', 'Err'),
                    ('Err', '*', 'Err'),
                    ('Err', '+', 'Err'),
                    ('Err', ',', 'Err'),
                    ('Err', '-', 'Err'),
                    ('Err', '.', 'Err'),
                    ('Err', '/', 'Err'),
                    ('Err', ':', 'Err'),
                    ('Err', '<', 'Err'),
                    ('Err', '=', 'Err'),
                    ('Err', '>', 'Err'),
                    ('Err', '?', 'Err'),
                    ('Err', '@', 'Err'),
                    ('Err', '[', 'Err'),
                    ('Err', '\\', 'Err'),
                    ('Err', ']', 'Err'),
                    ('Err', '^', 'Err'),
                    ('Err', '_', 'Err'),
                    ('Err', '`', 'Err'),
                    ('Err', '{', 'Err'),
                    ('Err', '|', 'Err'),
                    ('Err', '}', 'Err'),
                    ('Err', '~', 'Err')
                ]),
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
                'V': set('0123456789 \t\v\f\r\nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\\\\]^_`{|}~'),
                'T': set([
                    ('S', '#', 'Err'),
                    ('S', ';', 'Err'),
                    ('S', '0', 'Err'),
                    ('S', '1', 'Err'),
                    ('S', '2', 'Err'),
                    ('S', '3', 'Err'),
                    ('S', '4', 'Err'),
                    ('S', '5', 'Err'),
                    ('S', '6', 'Err'),
                    ('S', '7', 'Err'),
                    ('S', '8', 'Err'),
                    ('S', '9', 'Err'),
                    ('S', ' ', 'Err'),
                    ('S', '\t', 'Err'),
                    ('S', '\v', 'Err'),
                    ('S', '\f', 'Err'),
                    ('S', '\r', 'Err'),
                    ('S', '\n', 'Err'),
                    ('S', 'a', 'Err'),
                    ('S', 'b', 'Err'),
                    ('S', 'c', 'Err'),
                    ('S', 'd', 'Err'),
                    ('S', 'e', 'Err'),
                    ('S', 'f', 'Err'),
                    ('S', 'g', 'Err'),
                    ('S', 'h', 'Err'),
                    ('S', 'i', 'Err'),
                    ('S', 'j', 'Err'),
                    ('S', 'k', 'Err'),
                    ('S', 'l', 'Err'),
                    ('S', 'm', 'Err'),
                    ('S', 'n', 'Err'),
                    ('S', 'o', 'Err'),
                    ('S', 'p', 'Err'),
                    ('S', 'q', 'Err'),
                    ('S', 'r', 'Err'),
                    ('S', 's', 'Err'),
                    ('S', 't', 'Err'),
                    ('S', 'u', 'Err'),
                    ('S', 'v', 'Err'),
                    ('S', 'w', 'Err'),
                    ('S', 'x', 'Err'),
                    ('S', 'y', 'Err'),
                    ('S', 'z', 'Err'),
                    ('S', 'A', 'Err'),
                    ('S', 'B', 'Err'),
                    ('S', 'C', 'Err'),
                    ('S', 'D', 'Err'),
                    ('S', 'E', 'Err'),
                    ('S', 'F', 'Err'),
                    ('S', 'G', 'Err'),
                    ('S', 'H', 'Err'),
                    ('S', 'I', 'Err'),
                    ('S', 'J', 'Err'),
                    ('S', 'K', 'Err'),
                    ('S', 'L', 'Err'),
                    ('S', 'M', 'Err'),
                    ('S', 'N', 'Err'),
                    ('S', 'O', 'Err'),
                    ('S', 'P', 'Err'),
                    ('S', 'Q', 'Err'),
                    ('S', 'R', 'Err'),
                    ('S', 'S', 'Err'),
                    ('S', 'T', 'Err'),
                    ('S', 'U', 'Err'),
                    ('S', 'V', 'Err'),
                    ('S', 'W', 'Err'),
                    ('S', 'X', 'Err'),
                    ('S', 'Y', 'Err'),
                    ('S', 'Z', 'Err'),
                    ('S', '!', 'Err'),
                    ('S', '"', '_'),
                    ('S', '$', 'Err'),
                    ('S', '%', 'Err'),
                    ('S', '&', 'Err'),
                    ('S', '\'', 'Err'),
                    ('S', '(', 'Err'),
                    ('S', ')', 'Err'),
                    ('S', '*', 'Err'),
                    ('S', '+', 'Err'),
                    ('S', ',', 'Err'),
                    ('S', '-', 'Err'),
                    ('S', '.', 'Err'),
                    ('S', '/', 'Err'),
                    ('S', ':', 'Err'),
                    ('S', '<', 'Err'),
                    ('S', '=', 'Err'),
                    ('S', '>', 'Err'),
                    ('S', '?', 'Err'),
                    ('S', '@', 'Err'),
                    ('S', '[', 'Err'),
                    ('S', '\\', 'Err'),
                    ('S', ']', 'Err'),
                    ('S', '^', 'Err'),
                    ('S', '_', 'Err'),
                    ('S', '`', 'Err'),
                    ('S', '{', 'Err'),
                    ('S', '|', 'Err'),
                    ('S', '}', 'Err'),
                    ('S', '~', 'Err'),
                    ('_', '\n', '_'),
                    ('_', '#', '_'),
                    ('_', ';', '_'),
                    ('_', '0', '_'),
                    ('_', '1', '_'),
                    ('_', '2', '_'),
                    ('_', '3', '_'),
                    ('_', '4', '_'),
                    ('_', '5', '_'),
                    ('_', '6', '_'),
                    ('_', '7', '_'),
                    ('_', '8', '_'),
                    ('_', '9', '_'),
                    ('_', ' ', '_'),
                    ('_', '\t', '_'),
                    ('_', '\v', '_'),
                    ('_', '\f', '_'),
                    ('_', '\r', '_'),
                    ('_', 'a', '_'),
                    ('_', 'b', '_'),
                    ('_', 'c', '_'),
                    ('_', 'd', '_'),
                    ('_', 'e', '_'),
                    ('_', 'f', '_'),
                    ('_', 'g', '_'),
                    ('_', 'h', '_'),
                    ('_', 'i', '_'),
                    ('_', 'j', '_'),
                    ('_', 'k', '_'),
                    ('_', 'l', '_'),
                    ('_', 'm', '_'),
                    ('_', 'n', '_'),
                    ('_', 'o', '_'),
                    ('_', 'p', '_'),
                    ('_', 'q', '_'),
                    ('_', 'r', '_'),
                    ('_', 's', '_'),
                    ('_', 't', '_'),
                    ('_', 'u', '_'),
                    ('_', 'v', '_'),
                    ('_', 'w', '_'),
                    ('_', 'x', '_'),
                    ('_', 'y', '_'),
                    ('_', 'z', '_'),
                    ('_', 'A', '_'),
                    ('_', 'B', '_'),
                    ('_', 'C', '_'),
                    ('_', 'D', '_'),
                    ('_', 'E', '_'),
                    ('_', 'F', '_'),
                    ('_', 'G', '_'),
                    ('_', 'H', '_'),
                    ('_', 'I', '_'),
                    ('_', 'J', '_'),
                    ('_', 'K', '_'),
                    ('_', 'L', '_'),
                    ('_', 'M', '_'),
                    ('_', 'N', '_'),
                    ('_', 'O', '_'),
                    ('_', 'P', '_'),
                    ('_', 'Q', '_'),
                    ('_', 'R', '_'),
                    ('_', 'S', '_'),
                    ('_', 'T', '_'),
                    ('_', 'U', '_'),
                    ('_', 'V', '_'),
                    ('_', 'W', '_'),
                    ('_', 'X', '_'),
                    ('_', 'Y', '_'),
                    ('_', 'Z', '_'),
                    ('_', '!', '_'),
                    ('_', '"', 'F'),
                    ('_', '$', '_'),
                    ('_', '%', '_'),
                    ('_', '&', '_'),
                    ('_', '\'', '_'),
                    ('_', '(', '_'),
                    ('_', ')', '_'),
                    ('_', '*', '_'),
                    ('_', '+', '_'),
                    ('_', ',', '_'),
                    ('_', '-', '_'),
                    ('_', '.', '_'),
                    ('_', '/', '_'),
                    ('_', ':', '_'),
                    ('_', '<', '_'),
                    ('_', '=', '_'),
                    ('_', '>', '_'),
                    ('_', '?', '_'),
                    ('_', '@', '_'),
                    ('_', '[', '_'),
                    ('_', '\\', '_'),
                    ('_', ']', '_'),
                    ('_', '^', '_'),
                    ('_', '_', '_'),
                    ('_', '`', '_'),
                    ('_', '{', '_'),
                    ('_', '|', '_'),
                    ('_', '}', '_'),
                    ('_', '~', '_'),
                    ('F', '\n', 'Err'),
                    ('F', '#', 'Err'),
                    ('F', ';', 'Err'),
                    ('F', '0', 'Err'),
                    ('F', '1', 'Err'),
                    ('F', '2', 'Err'),
                    ('F', '3', 'Err'),
                    ('F', '4', 'Err'),
                    ('F', '5', 'Err'),
                    ('F', '6', 'Err'),
                    ('F', '7', 'Err'),
                    ('F', '8', 'Err'),
                    ('F', '9', 'Err'),
                    ('F', ' ', 'Err'),
                    ('F', '\t', 'Err'),
                    ('F', '\v', 'Err'),
                    ('F', '\f', 'Err'),
                    ('F', '\r', 'Err'),
                    ('F', 'a', 'Err'),
                    ('F', 'b', 'Err'),
                    ('F', 'c', 'Err'),
                    ('F', 'd', 'Err'),
                    ('F', 'e', 'Err'),
                    ('F', 'f', 'Err'),
                    ('F', 'g', 'Err'),
                    ('F', 'h', 'Err'),
                    ('F', 'i', 'Err'),
                    ('F', 'j', 'Err'),
                    ('F', 'k', 'Err'),
                    ('F', 'l', 'Err'),
                    ('F', 'm', 'Err'),
                    ('F', 'n', 'Err'),
                    ('F', 'o', 'Err'),
                    ('F', 'p', 'Err'),
                    ('F', 'q', 'Err'),
                    ('F', 'r', 'Err'),
                    ('F', 's', 'Err'),
                    ('F', 't', 'Err'),
                    ('F', 'u', 'Err'),
                    ('F', 'v', 'Err'),
                    ('F', 'w', 'Err'),
                    ('F', 'x', 'Err'),
                    ('F', 'y', 'Err'),
                    ('F', 'z', 'Err'),
                    ('F', 'A', 'Err'),
                    ('F', 'B', 'Err'),
                    ('F', 'C', 'Err'),
                    ('F', 'D', 'Err'),
                    ('F', 'E', 'Err'),
                    ('F', 'F', 'Err'),
                    ('F', 'G', 'Err'),
                    ('F', 'H', 'Err'),
                    ('F', 'I', 'Err'),
                    ('F', 'J', 'Err'),
                    ('F', 'K', 'Err'),
                    ('F', 'L', 'Err'),
                    ('F', 'M', 'Err'),
                    ('F', 'N', 'Err'),
                    ('F', 'O', 'Err'),
                    ('F', 'P', 'Err'),
                    ('F', 'Q', 'Err'),
                    ('F', 'R', 'Err'),
                    ('F', 'S', 'Err'),
                    ('F', 'T', 'Err'),
                    ('F', 'U', 'Err'),
                    ('F', 'V', 'Err'),
                    ('F', 'W', 'Err'),
                    ('F', 'X', 'Err'),
                    ('F', 'Y', 'Err'),
                    ('F', 'Z', 'Err'),
                    ('F', '!', 'Err'),
                    ('F', '"', 'Err'),
                    ('F', '$', 'Err'),
                    ('F', '%', 'Err'),
                    ('F', '&', 'Err'),
                    ('F', '\'', 'Err'),
                    ('F', '(', 'Err'),
                    ('F', ')', 'Err'),
                    ('F', '*', 'Err'),
                    ('F', '+', 'Err'),
                    ('F', ',', 'Err'),
                    ('F', '-', 'Err'),
                    ('F', '.', 'Err'),
                    ('F', '/', 'Err'),
                    ('F', ':', 'Err'),
                    ('F', '<', 'Err'),
                    ('F', '=', 'Err'),
                    ('F', '>', 'Err'),
                    ('F', '?', 'Err'),
                    ('F', '@', 'Err'),
                    ('F', '[', 'Err'),
                    ('F', '\\', 'Err'),
                    ('F', ']', 'Err'),
                    ('F', '^', 'Err'),
                    ('F', '_', 'Err'),
                    ('F', '`', 'Err'),
                    ('F', '{', 'Err'),
                    ('F', '|', 'Err'),
                    ('F', '}', 'Err'),
                    ('F', '~', 'Err'),
                    ('Err', '\n', 'Err'),
                    ('Err', '#', 'Err'),
                    ('Err', ';', 'Err'),
                    ('Err', '0', 'Err'),
                    ('Err', '1', 'Err'),
                    ('Err', '2', 'Err'),
                    ('Err', '3', 'Err'),
                    ('Err', '4', 'Err'),
                    ('Err', '5', 'Err'),
                    ('Err', '6', 'Err'),
                    ('Err', '7', 'Err'),
                    ('Err', '8', 'Err'),
                    ('Err', '9', 'Err'),
                    ('Err', ' ', 'Err'),
                    ('Err', '\t', 'Err'),
                    ('Err', '\v', 'Err'),
                    ('Err', '\f', 'Err'),
                    ('Err', '\r', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err'),
                    ('Err', 'c', 'Err'),
                    ('Err', 'd', 'Err'),
                    ('Err', 'e', 'Err'),
                    ('Err', 'f', 'Err'),
                    ('Err', 'g', 'Err'),
                    ('Err', 'h', 'Err'),
                    ('Err', 'i', 'Err'),
                    ('Err', 'j', 'Err'),
                    ('Err', 'k', 'Err'),
                    ('Err', 'l', 'Err'),
                    ('Err', 'm', 'Err'),
                    ('Err', 'n', 'Err'),
                    ('Err', 'o', 'Err'),
                    ('Err', 'p', 'Err'),
                    ('Err', 'q', 'Err'),
                    ('Err', 'r', 'Err'),
                    ('Err', 's', 'Err'),
                    ('Err', 't', 'Err'),
                    ('Err', 'u', 'Err'),
                    ('Err', 'v', 'Err'),
                    ('Err', 'w', 'Err'),
                    ('Err', 'x', 'Err'),
                    ('Err', 'y', 'Err'),
                    ('Err', 'z', 'Err'),
                    ('Err', 'A', 'Err'),
                    ('Err', 'B', 'Err'),
                    ('Err', 'C', 'Err'),
                    ('Err', 'D', 'Err'),
                    ('Err', 'E', 'Err'),
                    ('Err', 'F', 'Err'),
                    ('Err', 'G', 'Err'),
                    ('Err', 'H', 'Err'),
                    ('Err', 'I', 'Err'),
                    ('Err', 'J', 'Err'),
                    ('Err', 'K', 'Err'),
                    ('Err', 'L', 'Err'),
                    ('Err', 'M', 'Err'),
                    ('Err', 'N', 'Err'),
                    ('Err', 'O', 'Err'),
                    ('Err', 'P', 'Err'),
                    ('Err', 'Q', 'Err'),
                    ('Err', 'R', 'Err'),
                    ('Err', 'S', 'Err'),
                    ('Err', 'T', 'Err'),
                    ('Err', 'U', 'Err'),
                    ('Err', 'V', 'Err'),
                    ('Err', 'W', 'Err'),
                    ('Err', 'X', 'Err'),
                    ('Err', 'Y', 'Err'),
                    ('Err', 'Z', 'Err'),
                    ('Err', '!', 'Err'),
                    ('Err', '"', 'Err'),
                    ('Err', '$', 'Err'),
                    ('Err', '%', 'Err'),
                    ('Err', '&', 'Err'),
                    ('Err', '\'', 'Err'),
                    ('Err', '(', 'Err'),
                    ('Err', ')', 'Err'),
                    ('Err', '*', 'Err'),
                    ('Err', '+', 'Err'),
                    ('Err', ',', 'Err'),
                    ('Err', '-', 'Err'),
                    ('Err', '.', 'Err'),
                    ('Err', '/', 'Err'),
                    ('Err', ':', 'Err'),
                    ('Err', '<', 'Err'),
                    ('Err', '=', 'Err'),
                    ('Err', '>', 'Err'),
                    ('Err', '?', 'Err'),
                    ('Err', '@', 'Err'),
                    ('Err', '[', 'Err'),
                    ('Err', '\\', 'Err'),
                    ('Err', ']', 'Err'),
                    ('Err', '^', 'Err'),
                    ('Err', '_', 'Err'),
                    ('Err', '`', 'Err'),
                    ('Err', '{', 'Err'),
                    ('Err', '|', 'Err'),
                    ('Err', '}', 'Err'),
                    ('Err', '~', 'Err')
                ]),
                'S': 'S',
                'F': set(['F'])
            }
        },
        {
            'name': 'Identifiers',
            'valid': True,
            'expressions': {
                'id': '[_a..zA..Z][_a..zA..Z0..9]*',
            },
            'DFA': {
                'Q': set(['Char', 'DigitOrChar', 'Err']),
                'V': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
                'T': set([
                    ('Char', 'x', 'DigitOrChar'),
                    ('Char', 'G', 'DigitOrChar'),
                    ('Err', 'w', 'Err'),
                    ('Char', 'o', 'DigitOrChar'),
                    ('Char', 'Q', 'DigitOrChar'),
                    ('Err', 'k', 'Err'),
                    ('Err', '5', 'Err'),
                    ('Err', '7', 'Err'),
                    ('Char', 'D', 'DigitOrChar'),
                    ('DigitOrChar', 'c', 'DigitOrChar'),
                    ('DigitOrChar', 'E', 'DigitOrChar'),
                    ('Err', 'b', 'Err'),
                    ('Char', '5', 'Err'),
                    ('DigitOrChar', '7', 'DigitOrChar'),
                    ('DigitOrChar', 'B', 'DigitOrChar'),
                    ('Err', 'E', 'Err'),
                    ('Err', 'l', 'Err'),
                    ('DigitOrChar', 'L', 'DigitOrChar'),
                    ('Err', 'F', 'Err'),
                    ('Err', '3', 'Err'),
                    ('Char', 'K', 'DigitOrChar'),
                    ('Err', 'J', 'Err'),
                    ('Err', 't', 'Err'),
                    ('Char', 'E', 'DigitOrChar'),
                    ('DigitOrChar', 'j', 'DigitOrChar'),
                    ('Err', 'C', 'Err'),
                    ('Err', 'T', 'Err'),
                    ('DigitOrChar', 'U', 'DigitOrChar'),
                    ('Char', '0', 'Err'),
                    ('DigitOrChar', 'w', 'DigitOrChar'),
                    ('Char', 'c', 'DigitOrChar'),
                    ('Char', 'J', 'DigitOrChar'),
                    ('Err', 'H', 'Err'),
                    ('DigitOrChar', 'V', 'DigitOrChar'),
                    ('DigitOrChar', 'O', 'DigitOrChar'),
                    ('DigitOrChar', '2', 'DigitOrChar'),
                    ('Err', 'u', 'Err'),
                    ('Err', '6', 'Err'),
                    ('Char', '2', 'Err'),
                    ('Char', 'P', 'DigitOrChar'),
                    ('Err', 'i', 'Err'),
                    ('Char', 'b', 'DigitOrChar'),
                    ('Char', 'I', 'DigitOrChar'),
                    ('Err', 's', 'Err'),
                    ('DigitOrChar', 'h', 'DigitOrChar'),
                    ('DigitOrChar', 'Y', 'DigitOrChar'),
                    ('DigitOrChar', 'K', 'DigitOrChar'),
                    ('DigitOrChar', 'q', 'DigitOrChar'),
                    ('Char', 'W', 'DigitOrChar'),
                    ('Err', 'g', 'Err'),
                    ('Err', '1', 'Err'),
                    ('Char', 'a', 'DigitOrChar'),
                    ('Err', 'I', 'Err'),
                    ('DigitOrChar', 'T', 'DigitOrChar'),
                    ('Err', 'n', 'Err'),
                    ('Char', '1', 'Err'),
                    ('DigitOrChar', '0', 'DigitOrChar'),
                    ('DigitOrChar', 'a', 'DigitOrChar'),
                    ('Err', 'A', 'Err'),
                    ('Err', 'Q', 'Err'),
                    ('Err', 'R', 'Err'),
                    ('Char', 'V', 'DigitOrChar'),
                    ('DigitOrChar', 'r', 'DigitOrChar'),
                    ('DigitOrChar', '_', 'DigitOrChar'),
                    ('Err', 'v', 'Err'),
                    ('Err', '_', 'Err'),
                    ('Char', 'l', 'DigitOrChar'),
                    ('Err', 'P', 'Err'),
                    ('Char', 'U', 'DigitOrChar'),
                    ('Err', 'W', 'Err'),
                    ('Err', 'D', 'Err'),
                    ('Char', 'F', 'DigitOrChar'),
                    ('Char', 'H', 'DigitOrChar'),
                    ('DigitOrChar', 'g', 'DigitOrChar'),
                    ('Err', 'q', 'Err'),
                    ('Char', 's', 'DigitOrChar'),
                    ('Char', 'Z', 'DigitOrChar'),
                    ('Err', '8', 'Err'),
                    ('DigitOrChar', 'F', 'DigitOrChar'),
                    ('DigitOrChar', 'p', 'DigitOrChar'),
                    ('Err', 'e', 'Err'),
                    ('DigitOrChar', 'S', 'DigitOrChar'),
                    ('Char', 'O', 'DigitOrChar'),
                    ('Char', '3', 'Err'),
                    ('Char', 'r', 'DigitOrChar'),
                    ('Char', 'Y', 'DigitOrChar'),
                    ('DigitOrChar', 'n', 'DigitOrChar'),
                    ('DigitOrChar', 'd', 'DigitOrChar'),
                    ('Err', 'c', 'Err'),
                    ('DigitOrChar', 'I', 'DigitOrChar'),
                    ('DigitOrChar', '5', 'DigitOrChar'),
                    ('Err', 'z', 'Err'),
                    ('Char', 'N', 'DigitOrChar'),
                    ('DigitOrChar', 'Z', 'DigitOrChar'),
                    ('Char', 'q', 'DigitOrChar'),
                    ('DigitOrChar', '6', 'DigitOrChar'),
                    ('DigitOrChar', 'D', 'DigitOrChar'),
                    ('Char', 'd', 'DigitOrChar'),
                    ('Err', 'x', 'Err'),
                    ('Err', 'B', 'Err'),
                    ('Char', 'f', 'DigitOrChar'),
                    ('Char', 'M', 'DigitOrChar'),
                    ('DigitOrChar', 'G', 'DigitOrChar'),
                    ('DigitOrChar', 'b', 'DigitOrChar'),
                    ('DigitOrChar', 'l', 'DigitOrChar'),
                    ('DigitOrChar', 'M', 'DigitOrChar'),
                    ('DigitOrChar', '9', 'DigitOrChar'),
                    ('Char', '8', 'Err'),
                    ('Err', 'O', 'Err'),
                    ('Char', 'k', 'DigitOrChar'),
                    ('Char', 'e', 'DigitOrChar'),
                    ('DigitOrChar', 'X', 'DigitOrChar'),
                    ('Err', '4', 'Err'),
                    ('DigitOrChar', 'u', 'DigitOrChar'),
                    ('Char', 'X', 'DigitOrChar'),
                    ('Err', 'a', 'Err'),
                    ('Char', 'j', 'DigitOrChar'),
                    ('Char', 'T', 'DigitOrChar'),
                    ('DigitOrChar', 'v', 'DigitOrChar'),
                    ('DigitOrChar', 'Q', 'DigitOrChar'),
                    ('DigitOrChar', 'C', 'DigitOrChar'),
                    ('Char', 'p', 'DigitOrChar'),
                    ('Char', '_', 'DigitOrChar'),
                    ('Char', 'i', 'DigitOrChar'),
                    ('Err', 'f', 'Err'),
                    ('Char', '9', 'Err'),
                    ('DigitOrChar', 'y', 'DigitOrChar'),
                    ('Err', 'Y', 'Err'),
                    ('DigitOrChar', 'k', 'DigitOrChar'),
                    ('DigitOrChar', '4', 'DigitOrChar'),
                    ('Char', 'w', 'DigitOrChar'),
                    ('DigitOrChar', 'J', 'DigitOrChar'),
                    ('Char', 'g', 'DigitOrChar'),
                    ('Err', 'M', 'Err'),
                    ('DigitOrChar', 't', 'DigitOrChar'),
                    ('Err', 'N', 'Err'),
                    ('DigitOrChar', 'W', 'DigitOrChar'),
                    ('Char', 't', 'DigitOrChar'),
                    ('Char', 'C', 'DigitOrChar'),
                    ('DigitOrChar', '3', 'DigitOrChar'),
                    ('Err', 'h', 'Err'),
                    ('Err', '2', 'Err'),
                    ('Char', 'v', 'DigitOrChar'),
                    ('Char', '4', 'Err'),
                    ('Err', 'K', 'Err'),
                    ('Char', 'B', 'DigitOrChar'),
                    ('Err', '0', 'Err'),
                    ('Char', 'u', 'DigitOrChar'),
                    ('DigitOrChar', 'H', 'DigitOrChar'),
                    ('DigitOrChar', 'e', 'DigitOrChar'),
                    ('Char', 'h', 'DigitOrChar'),
                    ('Char', 'z', 'DigitOrChar'),
                    ('Char', 'A', 'DigitOrChar'),
                    ('DigitOrChar', 'f', 'DigitOrChar'),
                    ('DigitOrChar', 'A', 'DigitOrChar'),
                    ('DigitOrChar', 's', 'DigitOrChar'),
                    ('Err', 'r', 'Err'),
                    ('Err', 'o', 'Err'),
                    ('Err', '9', 'Err'),
                    ('DigitOrChar', 'R', 'DigitOrChar'),
                    ('Char', 'y', 'DigitOrChar'),
                    ('Err', 'U', 'Err'),
                    ('DigitOrChar', '8', 'DigitOrChar'),
                    ('DigitOrChar', 'i', 'DigitOrChar'),
                    ('Char', 'L', 'DigitOrChar'),
                    ('Err', 'p', 'Err'),
                    ('Err', 'Z', 'Err'),
                    ('Char', 'n', 'DigitOrChar'),
                    ('DigitOrChar', 'z', 'DigitOrChar'),
                    ('Err', 'S', 'Err'),
                    ('Err', 'd', 'Err'),
                    ('DigitOrChar', '1', 'DigitOrChar'),
                    ('Err', 'G', 'Err'),
                    ('Char', 'S', 'DigitOrChar'),
                    ('Err', 'X', 'Err'),
                    ('Char', 'm', 'DigitOrChar'),
                    ('DigitOrChar', 'P', 'DigitOrChar'),
                    ('Err', 'L', 'Err'),
                    ('DigitOrChar', 'm', 'DigitOrChar'),
                    ('DigitOrChar', 'o', 'DigitOrChar'),
                    ('Err', 'y', 'Err'),
                    ('Char', 'R', 'DigitOrChar'),
                    ('DigitOrChar', 'N', 'DigitOrChar'),
                    ('Char', '6', 'Err'),
                    ('Err', 'V', 'Err'),
                    ('Err', 'j', 'Err'),
                    ('DigitOrChar', 'x', 'DigitOrChar'),
                    ('Err', 'm', 'Err'),
                    ('Char', '7', 'Err')
                ]),
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
        {
            'name': 'Invalid Expression Character Range',
            'valid': False,
            'expressions': {
                'invalid': '[a..]',
            },
            'DFA': {}
        }
    ]


    from itertools import permutations

    def isomorphic(set1, set2, _map, mfunc):
        if len(set1) != len(set2):
            return False

        for elem in set1:
            if mfunc(_map, elem) not in set2:
                return False

        return True

    def final_map(_map, state):
        return _map[state]

    def delta_map(_map, move):
        return (_map[move[0]], move[1], _map[move[2]])

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

        if grammar.alphabet() != _DFA['V']:
            raise ValueError('Error: Incorrect alphabet produced')

        if len(grammar.states()) != len(_DFA['Q']):
            raise ValueError('Error: Incorrect number of states produced')

        if len(grammar.accepting()) != len(_DFA['F']):
            raise ValueError('Error: Incorrect number of finish states')

        if len(grammar.transitions()) != len(_DFA['T']):
            raise ValueError('Error: Incorrect number of transitions produced')

        # Check if DFA's are isomorphic by attempting to find a bijection
        # between them since they both already look very 'similar'.
        Q1 = grammar.states()
        Q2 = _DFA['Q']

        found = False
        for _map in (dict(zip(Q1, perm)) for perm in permutations(Q2, len(Q2))):
            if _map[grammar.start()] == _DFA['S'] and\
               isomorphic(grammar.accepting(), _DFA['F'], _map, final_map) and\
               isomorphic(grammar.transitions(), _DFA['T'], _map, delta_map):
                found = True
                break

        if not found:
            raise ValueError('Error: Non-isomorphic DFA produced')
