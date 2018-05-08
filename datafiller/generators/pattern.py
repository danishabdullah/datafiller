from __future__ import print_function, unicode_literals

from datafiller.consts import RE_POSIX_CC, RE_DOT, RECHARS
from datafiller.generators.base import AltGenerator, RandomGenerator, CatGenerator
from datafiller.generators.funcs import createGenerator
from datafiller.generators.reapeated import RepeatGenerator
from datafiller.generators.textual import ConstGenerator, CharsGenerator
from datafiller.utils import getParams

__author__ = "danishabdullah"
__all__ = ('Pattern', 'PatternGenerator')


#
# PATTERN PARSING UTILS
#
# Hmmm... This is pretty awful code. Not sure how to improve it.


class Pattern(object):
    """Pattern parsing utils."""

    @staticmethod
    def skipRepeat(pattern, i=0):
        """Return next character after repetition specification."""
        if i < len(pattern):
            if pattern[i] == '{':
                i = pattern.find('}', i + 1) + 1
                assert i != 0, "{0}: closing '}' not found".format(pattern)
                # assert re.match('\{\d+(,\d+)?}', ...)
            elif pattern[i] in '?+*':
                i += 1
        return i

    @staticmethod
    def catSplit(pattern):
        """Split pattern for cat.

        return [ [ pattern, extent ], ... ]
        """
        if len(pattern) == 0:
            return []
        if pattern[0] == '(':
            # find matching nested ')'
            opened, i = 1, 1
            while opened > 0:
                assert i < len(pattern), "{0}: no matching ')'".format(pattern)
                if pattern[i] == ')':
                    opened -= 1
                elif pattern[i] == '(':
                    opened += 1
                elif pattern[i] == '\\':  # escaped character
                    i += 1
                elif pattern[i] == '[':  # skip embedded [...]
                    i = pattern.index(']', i + (3 if pattern[i + 1] == '^' else 2))
                i += 1
            # find whether it is repeated
            end = Pattern.skipRepeat(pattern, i)
            return [[pattern[0:i], pattern[i:end]]] + \
                   Pattern.catSplit(pattern[end:])
        elif pattern[0] == '[':
            # find matching ']', skip 1/2 whatever, may be ']' or '^]'
            i = pattern.index(']', 3 if pattern[1] == '^' else 2) + 1
            end = Pattern.skipRepeat(pattern, i)
            return [[pattern[0:i], pattern[i:end]]] + \
                   Pattern.catSplit(pattern[end:])
        elif pattern[0] == '.':
            end = Pattern.skipRepeat(pattern, 1)
            return [['.', pattern[1:end]]] + \
                   Pattern.catSplit(pattern[end:])
        else:
            # eat possibly escaped characters, handling \[dswhH] on the fly
            i = 0
            while i < len(pattern):
                if pattern[i] == '\\' and pattern[i + 1] in RECHARS:
                    end = Pattern.skipRepeat(pattern, i + 2)
                    if i == 0:  # \?{10}
                        return [['[' + RECHARS[pattern[1]] + ']',
                                 pattern[2:end]]] + \
                               Pattern.catSplit(pattern[end:])
                    else:  # STUF\?{10}
                        return [[pattern[0:i], ''], \
                                ['[' + RECHARS[pattern[i + 1]] + ']',
                                 pattern[i + 2:end]]] + \
                               Pattern.catSplit(pattern[end:])
                elif pattern[i] == '\\':
                    i += 1
                    assert i < len(pattern), \
                        "{0}: cannot end on escape".format(pattern)
                elif pattern[i] in '{?+*':
                    assert i != 0, \
                        "{0}: cannot start with repeat".format(pattern)
                    if i == 1:
                        # F{3}
                        end = Pattern.skipRepeat(pattern, i)
                        return [[pattern[0:i], pattern[i:end]]] + \
                               Pattern.catSplit(pattern[end:])
                    else:
                        # STUFF{3} -> STUF & F{3}
                        end = Pattern.skipRepeat(pattern, i)
                        return [[pattern[0:i - 1], ''], \
                                [pattern[i - 1:i], pattern[i:end]]] + \
                               Pattern.catSplit(pattern[end:])
                elif pattern[i] in '([':
                    return [[pattern[0:i], '']] + \
                           Pattern.catSplit(pattern[i:])
                i += 1
            return [[pattern, '']]

    @staticmethod
    def altSplit(pattern):
        """Split pattern for Alt

        returns [patterns]
        """
        assert pattern[0] == '(' and pattern[-1] == ')', \
            "{0} is not an alternation".format(pattern)
        pattern = pattern[1:-1]  # remove parentheses
        l, i, opened = [], 0, 0
        while i < len(pattern):
            if pattern[i] == '\\':  # skip escaped character
                i += 1
            elif pattern[i] == '[':  # skip embedded []
                i = pattern.index(']', i + (3 if pattern[i + 1] == '^' else 2))
            elif pattern[i] == '(':
                opened += 1
            elif pattern[i] == ')':
                opened -= 1
            elif pattern[i] == '|' and opened == 0:
                l.append(pattern[0:i])
                pattern = pattern[i + 1:]
                i = -1
            i += 1
        # remaining stuff
        l.append(pattern)
        return l

    @staticmethod
    def repeat(att, g, extent):
        if extent == '' or extent == '{1}' or extent == '{1,1}':
            return g
        extent = '0,1' if extent == '?' else \
            '0,8' if extent == '*' else \
                '1,8' if extent == '+' else \
                    extent[1:-1]
        if ',' in extent:
            min, max = extent.split(',')
        else:
            min, max = extent, extent
        return RepeatGenerator(att, params={'extent': min + '-' + max}, gen=g)

    @staticmethod
    def genAlt(att, pattern, extent=''):
        """Parses a single pattern like (...) or [...] or ."""
        if len(pattern) == 0:
            return ConstGenerator(att)
        # handle '.' shortcut and other special (character) classes
        if pattern == '.':
            pattern = '[' + RE_DOT + ']'
        elif pattern[:2] == '[:' and pattern[-2:] == ':]':
            desc = pattern[2:-2]
            if desc in RE_POSIX_CC:
                pattern = '[' + RE_POSIX_CC[desc] + ']'
            else:
                # allow something like [:count start=10 format=08X step=2:]
                g = createGenerator(att, None, getParams(desc), msg=pattern)
                return Pattern.repeat(att, g, extent)
        if pattern[0] == '(':
            # alternative, AltGenerator
            l = Pattern.altSplit(pattern)
            assert len(l) > 0
            if len(l) == 1:
                g = Pattern.genCat(att, l[0])
            else:
                g = AltGenerator(att, gens=[Pattern.genCat(att, p) for p in l])
            return Pattern.repeat(att, g, extent)
        elif pattern[0] == '[':
            # character class, CharGenerator...
            if pattern[1] == '^':
                assert len(pattern) > 3 and pattern[-1] == ']'
                notch = CharsGenerator.parseCharSequence(att, pattern[2:-1])
                allch = CharsGenerator.parseCharSequence(att, RE_DOT)
                difch = ''.join(sorted(list(set(allch) - set(notch))))
                g = CharsGenerator(att, chars=difch)
            else:
                assert len(pattern) > 2 and pattern[-1] == ']'
                g = CharsGenerator(att, params={'chars': pattern[1:-1]})
            g.size, g.lenmin, g.lenmax = 0xffffffff, 1, 1
            return Pattern.repeat(att, g, extent)
        else:
            # possibly repeated constant text
            return Pattern.repeat(att, ConstGenerator(att, cst=pattern), extent)

    @staticmethod
    def genCat(att, pattern, extent=''):
        """Parses a pattern sequence like (foo|bla){1,3}stuff[abc]{5}'"""
        if len(pattern) == 0:
            # assert extent == '' # what is the point of: (){3}
            return ConstGenerator(att)
        pats = Pattern.catSplit(pattern)
        if len(pats) == 0:
            assert extent == '', \
                "{0}: extent {1} on nothing".format(pattern, extent)
            return ConstGenerator(att)
        elif len(pats) == 1:
            g = Pattern.genAlt(att, pats[0][0], pats[0][1])
        else:
            g = CatGenerator(att, gens=[Pattern.genAlt(att, p[0], p[1]) \
                                        for p in pats])
        return Pattern.repeat(att, g, extent)


class PatternGenerator(RandomGenerator):
    """Generate pattern-based text.

    - Generator root
    """
    DIRS = {'pattern': str}

    def __init__(self, att, params=None):
        RandomGenerator.__init__(self, att, params)
        assert 'pattern' in self.params, \
            "{0}: mandatory 'pattern' directive".format(self)
        self.pattern = '' if isinstance(self.params['pattern'], bool) else \
            self.params['pattern']
        self.root = Pattern.genAlt(att, '(' + self.pattern + ')')
        # synchronize full generator tree
        self.root.mapGen(lambda s: s.notNull())
        if self.shared:
            self.root.mapGen(lambda s: s.setShare(self.shared))
        self.cleanParams(PatternGenerator.DIRS)

    def mapGen(self, func):
        super(PatternGenerator, self).mapGen(func)
        self.root.mapGen(func)

    def genData(self):
        return self.root.genData()


def UUIDGenerator(att, params=None):
    if not params:
        params = att.params
    params['pattern'] = r'\h{4}(\h{4}-){4}\h{12}'
    return PatternGenerator(att, params)
