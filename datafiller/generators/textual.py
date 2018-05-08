from __future__ import print_function, unicode_literals

from datafiller.generators.array import ArrayGenerator
from datafiller.generators.base import RandomGenerator, WithLength, WithSubgen
from datafiller.generators.numeric import IntGenerator
from datafiller.generators.seed import SeedGenerator
from datafiller.scripts.cli import opts
from datafiller.utils import unescape, u8, u

__author__ = "danishabdullah"


# yep, RandomGenerator because of 'null'
class ConstGenerator(RandomGenerator):
    """Generate a constant possibly escaped string.

    - str cst: constant string to return.
    """
    DIRS = {'const': str}

    def __init__(self, att=None, params=None, cst=None, escape=True):
        RandomGenerator.__init__(self, att, params)
        if cst == None:
            cst = self.params['const'] if 'const' in self.params else ''
        if isinstance(cst, bool):  # fix if empty directive
            cst = ''
        self.cst = unescape(cst) if escape and cst.find('\\') != -1 else cst
        self.cleanParams(ConstGenerator.DIRS)

    def genData(self):
        return self.cst


# similar to RepeatGenerator, but with a different syntax
class TextGenerator(ArrayGenerator):
    """Generate text from another generator."""
    DIRS = {'text': str, 'separator': str, 'prefix': str, 'suffix': str}

    def __init__(self, att, params=None):
        ArrayGenerator.__init__(self, att, params, 'text')
        self.sep = self.params.get('separator', ' ')
        self.prefix = self.params.get('prefix', '')
        self.suffix = self.params.get('suffix', '')
        self.cleanParams(TextGenerator.DIRS)

    def genData(self):
        l = super(TextGenerator, self).genData()
        return self.prefix + self.sep.join(str(i) for i in l) + self.suffix


class BlobGenerator(WithLength, SeedGenerator):
    """Generate binary large object."""
    DIRS = {}

    def __init__(self, att, params=None):
        SeedGenerator.__init__(self, att, params)
        WithLength.__init__(self, 8, 16)
        self.cleanParams(BlobGenerator.DIRS)

    def genData(self):
        self.reseed()
        len = self._rand2.randint(self.lenmin, self.lenmax)
        return bytes([self._rand2.randrange(256) for o in range(len)])


class WordGenerator(IntGenerator):
    """Generate words, from a list of file

    - str[] words: list of words to draw from
    """
    # list from http://en.wikipedia.org/wiki/List_of_Hobbits
    HOBBITS = u8('Adaldrida Adamanta Adalgrim Adelard Amaranth Andwise ' +
                 'Angelica Asphodel Balbo Bandobras Belba Bell Belladonna ' +
                 'Berylla Bilbo Bill Bingo Bodo Bowman Bucca Bungo Camellia ' +
                 'Carl Celandine Chica Daddy Daisy Déagol Diamond Dinodas ' +
                 'Doderic Dodinas Donnamira Dora Drogo Dudo Eglantine Elanor ' +
                 'Elfstan Esmeralda Estella Everard Falco Faramir Farmer ' +
                 'Fastolph Fastred Ferdibrand Ferdinand Ferumbras').split(' ')
    DIRS = {'word': str}

    def __init__(self, att, params=None, words=None):
        # keep explicit size for later
        self.__size = params['size'] if params and 'size' in params else \
            att.params['size'] if att and 'size' in att.params else \
                None
        # NOT att.size: this is computed and does not supersede len(words)
        self.words = None  # temporary
        IntGenerator.__init__(self, att, params)
        assert not (words and 'word' in self.params), \
            "internal constructor issue, two word list specification!"
        if words:
            self.words = words
        else:
            spec = self.params['word']
            assert len(spec) > 0, "{0}: empty word specification".format(self)
            if spec[0] == ':':
                self.words = spec[1:].split(',')
            elif opts.self_test_hack:
                # self tests cannot depend from an external file
                # print("-- use Hobbit list for testing...")
                self.words = WordGenerator.HOBBITS
            else:
                # load word list from file
                f = open(spec, encoding='utf-8')
                assert f, "{0}: cannnot open '{1}'".format(self, spec)
                self.words = [u(l.rstrip()) for l in f]
                f.close()
        # TODO: should check that UNIQUE is ok?
        # overwrite default size from IntGenerator
        self.setSize(self.__size if self.__size else len(self.words))
        assert self.size <= len(self.words), \
            "{0}: 'size' {1} >  number of words {2}". \
                format(self, self.size, len(self.words))
        self.cleanParams(WordGenerator.DIRS)

    def setSize(self, size):
        if self.words == None:
            #  hack: too early!
            return
        IntGenerator.setSize(self, size)
        # ??? fix anyway...
        if self.size > len(self.words):
            self.size = len(self.words)
        # do not access the list out of bounds
        if self.offset + self.size > len(self.words):
            self.offset = self.size - len(self.words)

    def genData(self):
        return self.words[super(WordGenerator, self).genData()]


class StringGenerator(IntGenerator, WithLength):
    """Generate a basic string, like "stuff_12_12_12"

    - str prefix: use attribute name by default
    - int lenmin, lenmax: expected length
    """
    DIRS = {'prefix': str}  # | WithLength.DIRS

    def __init__(self, att, params=None):
        IntGenerator.__init__(self, att, params)
        WithLength.__init__(self, 8, 16)
        # set defaults from attributes
        self.prefix = self.params.get('prefix', att.name if att else 'str')
        if self.size == None:
            self.setSize(opts.size if opts.size else 1000)  # ???
        self.cleanParams(StringGenerator.DIRS)

    def lenData(self, length, n):
        """Generate a data for int n of length"""
        sn = '_' + str(n)
        s = self.prefix + sn * int(2 + (length - len(self.prefix)) / len(sn))
        return s[:int(length)]

    def baseData(self, n):
        # data dependent length so as to be deterministic
        s = self.lenData(self.lenmax, n)
        # ! hash(s) is not deterministic from python 3.3
        hs = sum(ord(s[i]) * (997 * i + 1) for i in range(len(s)))
        length = self.lenmin + hs % (self.lenmax - self.lenmin + 1)
        return s[:int(length)]

    def genData(self):
        return self.baseData(super(StringGenerator, self).genData())


# two generators are needed, one for the chars & one for the words
# the parameterized inherited generator is used for the words
# BUG: unique is not checked nor structurally inforced
class CharsGenerator(WithSubgen, StringGenerator):
    """Generate a string based on a character list.

    The generated string is deterministic in length +- lenvar.

    - str chars: list of characters to draw from
    - IntGenerator cgen: generator for choosing characters"""
    DIRS = {'chars': str, 'cgen': str}

    @staticmethod
    def parseCharSequence(obj, s):
        """Generate list of characters to choose from."""
        if isinstance(s, bool):
            s = ''
        c = unescape(s, regexp=True)
        # ((<stuff>)?X-Y|-)*<stuff>
        chars = ''
        d = c.find('-')
        while d != -1:
            if d == 0:
                chars += '-'  # leading dash means itself
                c = c[1:]
            else:
                assert d < len(c) - 1, \
                    "{0}: '{1}' cannot end with dash".format(obj, s)
                if d > 1:  # extract leading <stuff>
                    chars += c[0:d - 1]
                chars += \
                    ''.join(chr(x) for x in range(ord(c[d - 1]), ord(c[d + 1]) + 1))
                c = c[d + 2:]
            d = c.find('-')
        # append remaining stuff
        chars += c
        return chars

    def __init__(self, att=None, params=None, chars=None):
        StringGenerator.__init__(self, att, params)
        if att != None and att.isUnique():
            raise Exception("chars generator does not support UNIQUE")
        self.chars = \
            CharsGenerator.parseCharSequence(self, self.params['chars']) \
                if chars == None else chars
        assert len(self.chars) > 0, \
            "{0}: no characters to draw from".format(self)
        WithSubgen.__init__(self, 'cgen', None, self.params, backup=True)
        self.subgen.setSize(len(self.chars))  # number of chars
        self.subgen.offset = 0
        self.cleanParams(CharsGenerator.DIRS)

    def lenData(self, length, n):
        # ??? be deterministic in n and depend on seed option
        self.subgen._rand.seed(self.seed + str(n))
        s = ''.join(self.chars[self.subgen.genData()] for i in range(length))
        return s
