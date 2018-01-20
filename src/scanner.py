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
        | (union -> choice -> either or)
        ? (question -> choice -> 1 or none)
        . (concatenation -> combine)
        * (kleene star -> repitition >= 0)
        + (plus -> repitition >= 1)
    - concat can be either implicit or explicit
    - grouping/disambiguation is allowed using parenthesis ()
    - supported escape sequences:
        operator literals -> \?, \*, \., \+, \|
        grouping literals -> \(, \)
        epsilon           -> \e

        **COMING SOON**
    - character classes [abc]
    - character ranges [a..c]
    - character class/range negation (^)

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
    _Left = 6
    _Right = 7

    _operators = {
        '*': _Star,
        '|': _Union,
        '+': _Plus,
        '?': _Question,
        '(': _Left,
        ')': _Right,
        '.': _Concat
    }

    _escapable = {
        '*': '*',
        '|': '|',
        '+': '+',
        '?': '?',
        '(': '(',
        ')': ')',
        '.': '.',
        '\\': '\\',
        'e': _Epsilon
    }

    _postfix = set([_Right, _Star, _Plus, _Question]) | _characters
    _prefix = set([_Left]) | _characters

    _precedence = {  # higher is better
        _Left:     (3, None),
        _Right:    (3, None),
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
        expr = self._expand(expr)
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

    def _expand(self, expr):
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
            elif token == self._Left:
                stack.append(self._Left)
            elif token == self._Right:
                while len(stack) > 0 and stack[-1] != self._Left:
                    queue.append(stack.pop())
                if len(stack) == 0:
                    raise ValueError('Error: unbalanced parenthesis')
                stack.pop()
            elif token in self._precedence:
                while len(stack) > 0 and stack[-1] != self._Left and\
                      self._precedence[token][0] <= \
                      self._precedence[stack[-1]][0]\
                      and self._precedence[token][1]:  # left-associative?
                    queue.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError('Error: invalid input')

        while len(stack) > 0:
            token = stack.pop()
            if token == self._Left or token == self._Right:
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
        Type: list -> set x set x set x set x string x string
        """
        Q = set()  # states
        V = set()  # input symbols (alphabet)
        T = set()  # transition relation: T in P(Q x V x Q)
        E = set()  # e-transition relation: E in P(Q x Q)
        S = None   # start state S in Q
        F = None   # accepting state F in Q

        stk = []  # NFA machine stk
        for token in expr:
            if token in self._precedence:
                if token == self._Concat:
                    if len(stk) < 2:
                        raise ValueError('Error: not enough args to op .')
                    p, F = stk.pop()
                    S, q = stk.pop()
                    E.update([(q, p)])
                elif token == self._Union:
                    if len(stk) < 2:
                        raise ValueError('Error: not enough args to op |')
                    p, q = stk.pop()
                    r, t = stk.pop()
                    S, F = self._state(), self._state()
                    E.update([(S, p), (S, r), (q, F), (t, F)])
                elif token == self._Star:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op *')
                    p, q = stk.pop()
                    S, F = self._state(), self._state()
                    E.update([(S, p), (q, p), (q, F), (S, F)])
                elif token == self._Plus:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op +')
                    p, q = stk.pop()
                    S, F = self._state(), self._state()
                    E.update([(S, p), (q, p), (q, F)])
                elif token == self._Question:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op ?')
                    p, q = stk.pop()
                    S, F = self._state(), self._state()
                    E.update([(S, p), (q, F), (S, F)])
                else:
                    raise ValueError('Error: operator not implemented')
            elif token in self._characters:
                S, F = self._state(), self._state()
                V.update([token])
                T.update([(S, token, F)])
            elif token == self._Epsilon:
                S, F = self._state(), self._state()
                E.update([(S, F)])
            else:
                raise ValueError('Error: invalid input')
            Q.update([S, F])
            stk.append((S, F))

        if len(stk) != 1:
            raise ValueError('Error: invalid expression')
        S, F = stk.pop()
        return frozenset(Q), frozenset(V), frozenset(T), frozenset(E), S, F

    def _e_closure(self, q, E, cache):
        """
        Find the epsilon closure of state q and epsilon transitions E. A cache
        is utilized to speed things up for repeated invocations. Stated in set
        notation: { q' | q ->*e q' }, from a given start state q find all
        states q' which are reachable using only epsilon transitions, handling
        cycles appropriately.

        Runtime: O(n) - linear in the number of epsilon transitions
        Type: string x set x dict[frozenset]set -> set
        """
        if q in cache:
            return cache[q]

        closure, explore = set(), set([q])
        while len(explore) > 0:
            qp = explore.pop()
            if qp in closure:
                continue

            closure.update([qp])
            if qp in cache:
                closure.update(cache[qp])
            else:  # perform a single step: { q' | q ->e q' }
                explore.update({t[1] for t in E if t[0] == qp})

        cache[q] = closure
        return closure

    def _DFA(self, eNFA):
        """
        Convert the epsilon NFA to a DFA using subset construction and
        e-closure conversion. Only states wich are reachable from the start
        state are considered. This results in a minimized DFA with reguard to
        reachable states, but not with reguard to nondistinguishable states.

        Runtime: O(2^n) - exponential in the number of states
        Type: set x set x set x set x string x string
                -> set x set x set x string x set
        """
        Q, V, T, E, S, F = eNFA

        cache = {}
        Sp = frozenset(self._e_closure(S, E, cache))
        Qp, Fp, Tp, explore = set(), set(), set(), set([Sp.copy()])
        while len(explore) > 0:
            q = explore.pop()  # DFA state; set of NFA states
            Qp.update([q])
            if len(q & frozenset([F])) > 0:
                Fp.update([q])
            for a in V:
                nqs = {t[2] for t in T for s in q if t[0] == s and t[1] == a}
                if len(nqs) == 0:
                    continue
                qps = [self._e_closure(nq, E, cache) for nq in nqs]
                qp = set()
                for _q in qps:
                    qp.update(_q)
                qp = frozenset(qp)
                if qp not in Qp:
                    explore.update([qp])
                Tp.update([(q, a, qp)])

        return frozenset(Qp), V, frozenset(Tp), Sp, frozenset(Fp)

    def _alpha(self, dfa):
        """
        Perform an alpha rename on all DFA states to simplify the
        representation which the end user will consume.

        Runtime: O(n) - linear in the number of states and transitions
        Type: set x set x set x string x set -> set x set x set x string x set
        """
        Q, V, T, S, F = dfa
        rename = {q: self._state() for q in Q}
        Qp = frozenset(rename.values())
        Fp = frozenset({rename[f] for f in F})
        Sp = rename[S]
        Tp = frozenset({(rename[t[0]], t[1], rename[t[2]]) for t in T})

        return Qp, V, Tp, Sp, Fp

    def _total(self, dfa):
        """
        Make the DFA's delta function total, if not already, by adding a
        sink/error state. All unspecified state transitions are then specified
        by adding a transition to the new sink/error state.

        Runtime: O(n) - linear in the number of states and transitions
        Type: set x set x set x string x set -> set x set x set x string x set
        """
        Q, V, T, S, F = dfa

        M = {q: {} for q in Q}
        for t in T:
            M[t[0]][t[1]] = t[2]

        fix = False
        q_err = self._state()
        for q_trans in M.values():
            if len(q_trans) != len(V):
                Q = Q | frozenset([q_err])
                M[q_err] = {}
                fix = True
                break

        if fix:
            Tp = set()
            for q in M.keys():
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

        P = set([F, Q - F])   # partitions -> set of DFA state
        if frozenset() in P:  # if Q - F was empty
            P.remove(frozenset())

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
                        updates.append((Y, [s1, s2]))
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
            if len(part & frozenset([S])) > 0:
                Sp = part
                break
        Fp = frozenset({part for part in P if len(part & F) > 0})

        return frozenset(P), V, frozenset(Tp), Sp, Fp


if __name__ == '__main__':

    TESTS = [
        {
            'name': 'Single Alpha',
            'valid': True,
            'expressions': {
                'alpha': 'a'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'Err']),
                'V': frozenset(['a']),
                'T': frozenset([
                    ('S', 'a', 'A'),
                    ('A', 'a', 'Err'),
                    ('Err', 'a', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['A'])
            }
        },
        {
            'name': 'Explicit Concatenation',
            'valid': True,
            'expressions': {
                'concat': 'a.b'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Alternation',
            'valid': True,
            'expressions': {
                'alt': 'a|b'
            },
            'DFA': {
                'Q': frozenset(['S', 'AB', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
                    ('S', 'a', 'AB'),
                    ('S', 'b', 'AB'),
                    ('AB', 'a', 'Err'),
                    ('AB', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['AB'])
            }
        },
        {
            'name': 'Kleene Star',
            'valid': True,
            'expressions': {
                'star': 'a*'
            },
            'DFA': {
                'Q': frozenset(['A']),
                'V': frozenset(['a']),
                'T': frozenset([('A', 'a', 'A')]),
                'S': 'A',
                'F': frozenset(['A'])
            }
        },
        {
            'name': 'Kleene Plus',
            'valid': True,
            'expressions': {
                'plus': 'a+'
            },
            'DFA': {
                'Q': frozenset(['S', 'A']),
                'V': frozenset(['a']),
                'T': frozenset([
                    ('S', 'a', 'A'),
                    ('A', 'a', 'A')
                ]),
                'S': 'S',
                'F': frozenset(['A'])
            }
        },
        {
            'name': 'Choice',
            'valid': True,
            'expressions': {
                'maybe': 'a?'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'Err']),
                'V': frozenset(['a']),
                'T': frozenset([
                    ('S', 'a', 'A'),
                    ('A', 'a', 'Err'),
                    ('Err', 'a', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['S', 'A'])
            }
        },
        {
            'name': 'Grouping',
            'valid': True,
            'expressions': {
                'group': '(a|b)*'
            },
            'DFA': {
                'Q': frozenset(['AB*']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
                    ('AB*', 'a', 'AB*'),
                    ('AB*', 'b', 'AB*')
                ]),
                'S': 'AB*',
                'F': frozenset(['AB*'])
            }
        },
        {
            'name': 'Association',
            'valid': True,
            'expressions': {
                'assoc': 'a|b*'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['S', 'A', 'B'])
            }
        },
        {
            'name': 'Concat Alpha',
            'valid': True,
            'expressions': {
                'concat': '\.'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['.']),
                'T': frozenset([
                    ('S', '.', 'F'),
                    ('F', '.', 'Err'),
                    ('Err', '.', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Alternation Alpha',
            'valid': True,
            'expressions': {
                'alt': '\|'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['|']),
                'T': frozenset([
                    ('S', '|', 'F'),
                    ('F', '|', 'Err'),
                    ('Err', '|', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Kleene Star Alpha',
            'valid': True,
            'expressions': {
                'star': '\*'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['*']),
                'T': frozenset([
                    ('S', '*', 'F'),
                    ('F', '*', 'Err'),
                    ('Err', '*', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Choice Alpha',
            'valid': True,
            'expressions': {
                'question': '\?'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['?']),
                'T': frozenset([
                    ('S', '?', 'F'),
                    ('F', '?', 'Err'),
                    ('Err', '?', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Kleene Plus Alpha',
            'valid': True,
            'expressions': {
                'plus': '\+'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['+']),
                'T': frozenset([
                    ('S', '+', 'F'),
                    ('F', '+', 'Err'),
                    ('Err', '+', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Epsilon',
            'valid': True,
            'expressions': {
                'epsilon': '\e'
            },
            'DFA': {
                'Q': frozenset(['S']),
                'V': frozenset([]),
                'T': frozenset([]),
                'S': 'S',
                'F': frozenset(['S'])
            }
        },
        {
            'name': 'Backslash Alpha',
            'valid': True,
            'expressions': {
                'slash': '\\\\'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['\\']),
                'T': frozenset([
                    ('S', '\\', 'F'),
                    ('F', '\\', 'Err'),
                    ('Err', '\\', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Left Parenthesis Alpha',
            'valid': True,
            'expressions': {
                'lparen': '\('
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset(['(']),
                'T': frozenset([
                    ('S', '(', 'F'),
                    ('F', '(', 'Err'),
                    ('Err', '(', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Right Parenthesis Alpha',
            'valid': True,
            'expressions': {
                'rparen': '\)'
            },
            'DFA': {
                'Q': frozenset(['S', 'F', 'Err']),
                'V': frozenset([')']),
                'T': frozenset([
                    ('S', ')', 'F'),
                    ('F', ')', 'Err'),
                    ('Err', ')', 'Err')
                ]),
                'S': 'S',
                'F': frozenset(['F'])
            }
        },
        {
            'name': 'Implicit Concatenation 1',
            'valid': True,
            'expressions': {
                'concat': 'ab'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 2',
            'valid': True,
            'expressions': {
                'concat': 'a(b)'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 3',
            'valid': True,
            'expressions': {
                'concat': '(a)(b)'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 4',
            'valid': True,
            'expressions': {
                'concat': 'a*(b)'
            },
            'DFA': {
                'Q': frozenset(['A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
                    ('A', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'A',
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 5',
            'valid': True,
            'expressions': {
                'concat': 'a+(b)'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 6',
            'valid': True,
            'expressions': {
                'concat': 'a?(b)'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 7',
            'valid': True,
            'expressions': {
                'concat': 'a*b'
            },
            'DFA': {
                'Q': frozenset(['A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
                    ('A', 'a', 'A'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'Err'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'A',
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 8',
            'valid': True,
            'expressions': {
                'concat': 'a+b'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 9',
            'valid': True,
            'expressions': {
                'concat': 'a?b'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
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
                'F': frozenset(['B'])
            }
        },
        {
            'name': 'Implicit Concatenation 10 - Mixed',
            'valid': True,
            'expressions': {
                'concat': 'a.bc.de'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'B', 'C', 'D', 'E', 'Err']),
                'V': frozenset(['a', 'b', 'c', 'd', 'e']),
                'T': frozenset([
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
                'F': frozenset(['E'])
            }
        },
        {
            'name': 'Randomness 1',
            'valid': True,
            'expressions': {
                'random': 'a*(b|cd)*'
            },
            'DFA': {
                'Q': frozenset(['AC', 'B', 'DE', 'Err']),
                'V': frozenset(['a', 'b', 'c', 'd']),
                'T': frozenset([
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
                'F': frozenset(['AC', 'DE']),
            }
        },
        {
            'name': 'Randomness 2',
            'valid': True,
            'expressions': {
                'random': '(a|\e)b*'
            },
            'DFA': {
                'Q': frozenset(['A', 'B', 'Err']),
                'V': frozenset(['a', 'b']),
                'T': frozenset([
                    ('A', 'a', 'B'),
                    ('A', 'b', 'B'),
                    ('B', 'a', 'Err'),
                    ('B', 'b', 'B'),
                    ('Err', 'a', 'Err'),
                    ('Err', 'b', 'Err')
                ]),
                'S': 'A',
                'F': frozenset(['A', 'B'])
            }
        },
        {
            'name': 'Randomness 3',
            'valid': True,
            'expressions': {
                'random': '(a*b)|(a.bcd.e)'
            },
            'DFA': {
                'Q': frozenset(['S', 'A', 'A*', 'B', 'C', 'D', 'F', 'Err']),
                'V': frozenset(['a', 'b', 'c', 'd', 'e']),
                'T': frozenset([
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
                'F': frozenset(['F', 'B'])
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
        Q1 = list(grammar.states())
        Q2 = list(_DFA['Q'])

        _map = {}
        found = False
        for permutation in permutations(Q2, len(Q2)):
            for i in range(0, len(Q1)):
                _map[Q1[i]] = permutation[i]

            if _map[grammar.start()] == _DFA['S'] and\
               isomorphic(grammar.accepting(), _DFA['F'], _map, final_map) and\
               isomorphic(grammar.transitions(), _DFA['T'], _map, delta_map):
                found = True
                break

        if not found:
            raise ValueError('Error: Non-isomorphic DFA produced')
