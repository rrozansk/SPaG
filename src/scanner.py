"""
During Lexical Analysis the Lexer/Scanner recognizes regular expressions as
corresponding token types. These tokens are then sent to the parser.
Tokens have a type and value, but can also have character and line number
information as well.

The difference between lexers and parser is that a lexer reconizes regular
grammars/expressions, while parser recognize context free grammars. The main
difference is regular grammars can be converted into NFA with epsilon
prodcutions using thompsons algorithm, and then used to construct a
corresponding DFA using subset construction. After this is completed it can
further be minimized. Context free grammars can be converted into PDA's,
which require a stack, but they are also more powerful than regular grammars
since they can properly deal with recursion.
"""
from uuid import uuid4
from itertools import permutations


class RegularGrammar(object):
    """
    RegularGrammar represents a collection of formal regular expressions which
    can be programatically transformed into a parser.
    """

    spaces = set('\s\t\v\f\r\n')
    uppers = set('abcdefghijklmnopqrstuvwxyz')
    lowers = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    digits = set('0123456789')
    specials = set('!"#$%&\'`_/:;<=>-^\\{}~,@[]')
    metas = set('?+()*|.')  # FIXME: . just tmp for testing

    characters = uppers | lowers | digits | spaces | specials

    Star = 0
    Union = 1
    Concat = 2
    Plus = 3
    Question = 4
    Epsilon = 5
    Left = 6
    Right = 7

    escapes = {
        '*': Star,
        '|': Union,
        '+': Plus,
        '?': Question,
        '(': Left,
        ')': Right,
        '.': Concat,  # FIXME: . just tmp for testing
        'e': Epsilon,
        '\\': '\\'
    }

    shunt = {  # ***precedence (higher is better), left associative?***
        Left:     (3, None),
        Right:    (3, None),
        Star:     (2, False),  # right-associative
        Plus:     (2, False),  # right-associative
        Question: (2, False),  # right-associative
        Concat:   (1, True),   # left-associative
        Union:    (0, True),   # left-associative
    }

    name = None      # name of scanner
    regexps = None     # token dictionary ::=  name -> regexp

    def __init__(self, name):
        """ Initialize the RegularGrammar class with a name."""
        self.name = name
        self.regexps = {}

    def token(self, descriptor, expression):
        """
        add a token (expression) to the language as a regular expression to
        match against with a given name and whether or not discard the token
        after reading it (ex. comments). only accepts printable ASCII char
        values (33-126) and space chars ( \s, \t, \v, \f, \r, \n)
        """
        self.regexps[descriptor] = expression

    def _convert(self, expr):
        """
        Convert the expression from an external to an internal representation.

        character conversions:
          meta -> internal representation (integer enum)
          escaped meta -> character
          escaped escape -> character
          escape sequence -> internal representation

        runs in time linear to the input expression O(n).
        input expr: string -> output expr: list or raise ValueError
        """
        output = []
        escape = False
        for char in expr:
            if escape:
                escape = False
                if char in self.metas:
                    output.append(char)
                if char in self.escapes:
                    output.append(self.escapes[char])
                else:
                    raise ValueError('Error: invalid escape seq: \\' + char)
            else:
                if char == '\\':
                    escape = True
                elif char in self.characters:
                    output.append(char)
                elif char in self.metas:
                    output.append(self.escapes[char])
                else:
                    raise ValueError('Error: unrecognized character: ' + char)
        if escape:
            raise ValueError('Error: empty escape sequence')
        return output

    def _shunt(self, expression):  # FIXME: expose concatenation
        """
        converts infix notation expression into a postfix (reverse poslish
        notation; RPN) expression, therefore removing the need for
        parenthesis and allowing for the output expression to easily be
        evaluated with an iterative stack based method.
        algorithm @https://en.wikipedia.org/wiki/Shunting-yard_algorithm
        runs in time linear to the input expression O(n).
        """
        stack, queue = [], []  # operators, output (RPN expression)

        for token in expression:
            if token in self.characters:
                queue.append(token)
            elif token is self.Epsilon:
                queue.append(token)
            elif token == self.Left:
                stack.append(self.Left)
            elif token == self.Right:
                while len(stack) > 0 and stack[-1] != self.Left:
                    queue.append(stack.pop())
                if len(stack) == 0:
                    raise ValueError('Error: unbalanced parenthesis')
                stack.pop()
            elif token in self.shunt:
                while len(stack) > 0 and stack[-1] != self.Left and\
                      self.shunt[token][0] <= self.shunt[stack[-1]][0]\
                      and self.shunt[token][1]:  # left-associative?
                    queue.append(stack.pop())
                stack.append(token)
            else:
                raise ValueError('Error: invalid input')

        while len(stack) > 0:
            token = stack.pop()
            if token == self.Left or token == self.Right:
                raise ValueError('Error: unbalanced parenthesis')
            queue.append(token)

        return queue

    def _eNFA(self, expression):
        """
        converts a regular expression in RPN to an NFA with epsilon productions
        (eNFA) which can handle: union |, kleene star *, concatenation .,
        epsilon \e, literals, and syntax extensions + and ?. adapted to a
        iterative stacked based evaluation algorithm (standard RPN evaluation
        algorithm) from thompson construction as described in section 4.1 in 'A
        taxonomy of finite automata construction algorithms' by Bruce Watson,
        located @http://alexandria.tue.nl/extra1/wskrap/publichtml/9313452.pdf
        runs in time linear to the input expression O(n).
        """
        Q = set()  # set of states
        V = set()  # set of input symbols (alphabet)
        T = set()  # transition relation: T in P(Q x V x Q)
        E = set()  # e-transition relation: E in P(Q x Q)
        S = None   # start state S in Q
        F = None   # accepting state F in Q

        def state(): return str(uuid4())

        stk = []  # NFA machine stk
        for token in expression:
            if token in self.shunt:
                if token == self.Concat:
                    if len(stk) < 2:
                        raise ValueError('Error: not enough args to op .')
                    p, F = stk.pop()
                    S, q = stk.pop()
                    E.update([(q, p)])
                elif token == self.Union:
                    if len(stk) < 2:
                        raise ValueError('Error: not enough args to op |')
                    p, q = stk.pop()
                    r, t = stk.pop()
                    S, F = state(), state()
                    E.update([(S, p), (S, r), (q, F), (t, F)])
                elif token == self.Star:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op *')
                    p, q = stk.pop()
                    S, F = state(), state()
                    E.update([(S, p), (q, p), (q, F), (S, F)])
                elif token == self.Plus:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op +')
                    p, q = stk.pop()
                    S, F = state(), state()
                    E.update([(S, p), (q, p), (q, F)])
                elif token == self.Question:
                    if len(stk) < 1:
                        raise ValueError('Error: not enough args to op ?')
                    p, q = stk.pop()
                    S, F = state(), state()
                    E.update([(S, p), (q, F), (S, F)])
                else:
                    raise ValueError('Error: operator not implemented')
            elif token in self.characters:
                S, F = state(), state()
                V.update([token])
                T.update([(S, token, F)])
            elif token == self.Epsilon:
                S, F = state(), state()
                E.update([(S, F)])
            else:
                raise ValueError('Error: invalid input')
            Q.update([S, F])
            stk.append((S, F))

        if len(stk) != 1:
            raise ValueError('Error: invalid expression')
        S, F = stk.pop()
        return [frozenset(elem) for elem in [Q, V, T, E, [S], [F]]]

    def _e_closure(self, q, E, cache=dict()):
        """
        { q' | q ->*e q' } from a given start state q given a set of epsilon
        transitions in the form: (in, out), find all reachable state using only
        epsilon transitions, handling cycles appropriately. optionally a cache
        can be passed for memoization; map NFA state -> set of NFA states
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
            else:
                # perform a single step: { q' | q ->e q' }
                explore.update({t[1] for t in E if t[0] == qp})

        cache[q] = closure
        return closure

    def _DFA(self, eNFA):
        """
        converts the eNFA to DFA using subset construction and e closure
        conversion. We only consider states reachable from the start state,
        so the resulting DFA is minimized with reguard to reachable states
        """
        Q, V, T, E, S, F = eNFA

        cache = {}
        Sp = set([frozenset(self._e_closure(s, E, cache)) for s in S])
        Qp, Fp, Tp, explore = set(), set(), set(), Sp.copy()
        while len(explore) > 0:
            q = explore.pop()  # DFA state; set of NFA states
            Qp.update([q])
            if len(q & F) > 0:
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

        return [frozenset(Qp), V, frozenset(Tp), frozenset(Sp), frozenset(Fp)]

    def _Hopcroft(self, dfa):
        """
        minimizes the DFA using hopcrafts algorithm to merge equivalent states
        """
        Q, V, T, S, F = dfa

        P = set([F, Q - F])  # partitions -> set of DFA state
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
        Sp = frozenset({part for part in P if len(part & S) > 0})
        Fp = frozenset({part for part in P if len(part & F) > 0})

        return (frozenset(P), V, frozenset(Tp), Sp, Fp)

    def make(self):
        """
        converts all tokens representing regular expressions (regular grammars)
        to NFAs with epsilon transitions, which are then converted into
        equivalent DFAs and finally minimized to a unique DFA capable of
        parsing any input in O(n) time to produce a possible match against any
        token type specified to the tokenizer
        """
        scanners = {}
        for (name, regexp) in self.regexps.items():
            expression = self._shunt(self._convert(regexp))
            (Q, V, T, S, F) = self._Hopcroft(self._DFA(self._eNFA(expression)))
            scanners[name] = {
                'expr': regexp,
                'Q': Q,
                'V': V,
                'T': T,
                'S': S,
                'F': F,
            }

        # FIXME: combine all token is 1 scanner. | between all tokens
        # add this as new key in return dictionary

        return {'name': self.name, 'scanners': scanners}


if __name__ == '__main__':

    TESTS = [
        {
            'name': 'Core Functionality',
            'tokens': {
                'test0': 'a*.(b|c.d)*',
                'test1': '(a|\e).b*',
            },
            'scanners': {
                'test0': {
                    'expr': 'a*.(b|c.d)*',
                    'Q': frozenset(['AC', 'B', 'DE']),
                    'V': frozenset(['a', 'b', 'c', 'd']),
                    'T': frozenset([
                        ('AC', 'a', 'AC'),
                        ('AC', 'b', 'DE'),
                        ('AC', 'c', 'B'),
                        ('B', 'd', 'DE'),
                        ('DE', 'b', 'DE'),
                        ('DE', 'c', 'B'),
                    ]),
                    'S': frozenset(['AC']),
                    'F': frozenset(['AC', 'DE']),
                },
                'test1': {
                    'expr': '(a|\e).b*',
                    'Q': frozenset(['A', 'B']),
                    'V': frozenset(['a', 'b']),
                    'T': frozenset([
                        ('A', 'a', 'B'),
                        ('A', 'b', 'B'),
                        ('B', 'b', 'B'),
                    ]),
                    'S': frozenset(['A']),
                    'F': frozenset(['A', 'B']),
                }
            },
            '': None  # 'test*': '(a|\e).b*', NOTE: composite scanner testing spec
        }
    ]

    for test in TESTS:
        grammar = RegularGrammar(test['name'])
        for tname, texpression in test['tokens'].items():
            grammar.token(tname, texpression)
        result = grammar.make()

        if result['name'] != test['name']:
            raise ValueError('Error: Incorrect reporting of scanner name')

        if len(result['scanners']) != len(test['scanners']):
            raise ValueError('Error: Incorrect number of tokenizers produced')

        for (tname, DFA) in test['scanners'].items():
            _DFA = result['scanners'].get(tname, None)

            if _DFA is None:
                raise ValueError('Error: No scanner produced for token')

            if _DFA['expr'] != DFA['expr']:
                raise ValueError('Error: Incorrect expression')

            if _DFA['V'] != DFA['V']:
                raise ValueError('Error: Incorrect alphabet')

            if len(_DFA['Q']) != len(DFA['Q']):
                raise ValueError('Error: Incorrect number of states')

            if len(_DFA['T']) != len(DFA['T']):
                raise ValueError('Error: Incorrect number of transitions')

            if len(_DFA['S']) != len(DFA['S']):
                raise ValueError('Error: Incorrect number of start states')

            if len(_DFA['F']) != len(DFA['F']):
                raise ValueError('Error: Incorrect number of end states')

            # attempt to find if DFA's are isomorphic by finding a bijection.
            # since both DFA's are the same size we find all mappings and then
            # just check if one matches...slow but works
            qs1, qs2 = list(_DFA['Q']), list(DFA['Q'])

            mappings = []
            for p in list(permutations(qs2, len(qs2))):
                mappings.append({qs1[i]: p[i] for i in range(0, len(qs1))})

            found = False
            while len(mappings) != 0:
                imap = mappings.pop()  # possibly an isomorphic map
                try:
                    for s in _DFA['S']:
                        if imap[s] not in DFA['S']:
                            raise ValueError('Error: Incorrect start set')

                    for f in _DFA['F']:
                        if imap[f] not in DFA['F']:
                            raise ValueError('Error: Incorrect final set')

                    for t in _DFA['T']:
                        if (imap[t[0]], t[1], imap[t[2]]) not in DFA['T']:
                            raise ValueError('Error: Incorrect transition set')
                except ValueError as e:
                    continue
                found = True  # found a mapping which didn't give an error
                break

            if not found:
                raise ValueError('Error: Incorrect DFA produced')
