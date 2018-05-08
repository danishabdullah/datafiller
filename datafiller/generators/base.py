from __future__ import print_function, unicode_literals

import random
import re

from datafiller.generators import IntGenerator
from datafiller.generators.funcs import macroGenerator, strDict, createGenerator
from datafiller.generators.shared import SharedGenerator
from datafiller.globals import tuple_count, df_macro
from datafiller.scripts.cli import opts
from datafiller.utils import debug, reduce

__author__ = "danishabdullah"

__all__ = ('Generator', 'WithSubgen', 'RandomGenerator', 'WithLength', 'NULLGenerator', 'ListGenerator',
           'CatGenerator', 'TupleGenerator', 'ReduceGenerator', 'AltGenerator', 'WithPersistent',
           'PersistentGenerator', 'ValueGenerator')


class Generator(object):
    """Generator is the base class for generating valid data,
    typically for a given attribute.

    Generators are driven by parameters (directives).
    They may depend on a random generator.
    The framework also allows to generate NULL values.

    - {} params: parameters
    - Attribute att: attribute (may be None in some cases)
    - str type: type to consider, possibly from att
    - float nullp: NULL value rate
    - int gens: call count
    - int size: number of underlying values (may be None)
    """
    # expected/allowed directives
    DIRS = {'null': float, 'type': str}

    def __init__(self, att, params=None):
        global generator_count
        generator_count += 1
        self.att = att
        self.params = {}
        self.params.update(params if params != None else \
                               att.params if att != None else \
                                   {})
        # show generators
        if opts.debug:
            debug(1, "{0}: {1} {2}".format(att, generator_count,
                                           self.__class__))
            debug(2, "params: {0}".format(strDict(self.params)))
        self.type = self.params['type'].lower() if 'type' in self.params else \
            att.type if att else \
                None
        # null probability
        self.nullp = 0.0
        if self.att == None:  # for tests
            self.nullp = \
                self.params.get('null', opts.null if opts.null else 0.0)
        elif self.att.isNullable():
            self.nullp = self.params['null'] if 'null' in self.params else \
                self.att.table.params['null'] \
                    if 'null' in self.att.table.params else \
                    opts.null
        assert 0.0 <= self.nullp and self.nullp <= 1.0, \
            "{0}: 'null' not in [0,1]".format(self)
        # underlying call counter and overall size, common to all generators
        self.gens, self.size = 0, None
        self.cleanParams(Generator.DIRS)

    def cleanParams(self, dirs):
        """Remove parameters once processed."""
        for d in dirs:
            if d in self.params:
                del self.params[d]

    def mapGen(self, func):
        """Apply func on all generators."""
        func(self)

    def shareSeed(self):
        """Reseed when under 'share'"""
        pass

    def notNull(self):
        self.nullp = 0.0

    def setShare(self, shared):
        self.shared = shared

    def __str__(self):
        if self.att:
            return "{0} {1}".format(self.__class__.__name__, self.att)
        else:
            return self.__class__.__name__

    def genData(self):
        """Generate actual data."""
        return None


class WithSubgen(Generator):
    """Set a sub-generator from a macro or parameters."""
    DIRS = {}

    def __init__(self, name=None, att=None, p={}, g=None, backup=False):
        if g:
            self.subgen = g
        else:
            assert (p and name in p) or backup, \
                "{0}: mandatory '{1}' directive".format(self, name)
            if p and name in p:
                self.subgen = macroGenerator(p[name], att)
                del p[name]
            else:
                self.subgen = IntGenerator(att)
        if self.shared and self.subgen:
            self.subgen.shared = self.shared
        self.cleanParams(WithSubgen.DIRS)

    def mapGen(self, func):
        super(WithSubgen, self).mapGen(func)
        if self.subgen:  # may be None for empty arrays
            self.subgen.mapGen(func)


class RandomGenerator(Generator):
    """Generate something based on random, possibly seeded.

    - Random _random: internal random number generator, possibly seeded
    """
    DIRS = {'share': str, 'seed': str}

    def __init__(self, att, params=None):
        Generator.__init__(self, att, params)
        self._rand = random.Random()
        # set generator seed, depending on the determinism requirements
        # self.seed = <gc>_(<share>_)?<seed/opts.seed/random>_
        self.seed = str(generator_count) + '_'
        if 'share' in self.params:
            self.shared = \
                SharedGenerator.getGenerator(self, self.params['share'])
            # what about self.shared.seed?
            self.seed += self.params['share'] + '_'
        else:
            self.shared = None
        # complete seeding
        if 'seed' in self.params:
            self.seed += self.params['seed'] + '_'
        elif opts.seed:
            self.seed += opts.seed + '_'
        # elif self.att:
        #    self.seed = self.att.table.name + '_' + self.att.name + '_'
        else:
            # is it necessary/useful? depending on python version?
            self.seed += str(random.random()) + '_'
        if not self.shared:
            self._rand.seed(self.seed)
        # else: it will be reseeded for each tuple in shareSeed, when called
        self.cleanParams(RandomGenerator.DIRS)

    def shareSeed(self):
        if self.shared:
            self._rand.seed(self.seed + str(self.shared.genData()))
        super(RandomGenerator, self).shareSeed()  # pass

    def setShare(self, shared):
        self.shared = shared
        super(RandomGenerator, self).setShare(shared)  # pass

    def getData(self):
        """Generate a NULL or some data with genData()."""
        # only call the random generated if really needed
        return None if self.nullp == 1.0 else \
            self.genData() if self.nullp == 0.0 else \
                None if self._rand.random() < self.nullp else \
                    self.genData()


class WithLength(Generator):
    """Set {min,max}len attributes."""
    # this is needed by String, Text & Blob...
    DIRS = {'lenmin': int, 'lenmax': int, 'length': int, 'lenvar': int}

    def __init__(self, lenmin=None, lenmax=None):
        self.lenmin, self.lenmax = lenmin, lenmax
        mm = 'lenmin' in self.params or 'lenmax' in self.params
        lv = 'length' in self.params or 'lenvar' in self.params
        assert not (mm and lv), \
            "{0}: not both 'length'/'lenvar' & 'lenmin'/'lenmax'".format(self)
        if self.type != None and not mm and not 'length' in self.params:
            # try length/var based on type
            clen = re.match(r'(var)?(char|bit)\((\d+)\)', self.type)
            self.lenmin, self.lenmax = None, None
            if clen:
                self.lenmax = int(clen.group(3))
                if re.match('var(char|bit)', self.type):
                    if 'lenvar' in self.params:
                        self.lenmin = self.lenmax - 2 * self.params['lenvar']
                        del self.params['lenvar']
                    else:
                        self.lenmin = int(self.lenmax * 3 / 4)
                else:  # char(X)
                    assert self.params.get('lenvar', 0) == 0, \
                        "{0}: non zero 'lenvar' on CHARS(*)".format(self)
                    self.lenmin = self.lenmax
        else:
            self.lenmin, self.lenmax = None, None
        if 'lenmax' in self.params:
            self.lenmax = self.params['lenmax']
        if 'lenmin' in self.params:
            self.lenmin = self.params['lenmin']
        if 'length' in self.params or 'lenvar' in self.params:
            length = self.params.get('length', int((lenmin + lenmax) / 2))
            lenvar = self.params.get('lenvar', 0)
            self.lenmin, self.lenmax = length - lenvar, length + lenvar
        if self.lenmin != None and self.lenmax == None:
            self.lenmax = int(self.lenmin * 4 / 3)
        elif self.lenmax != None and self.lenmin == None:
            self.lenmin = int(self.lenmax * 3 / 4)
        elif self.lenmin == None and self.lenmax == None:
            self.lenmin, self.lenmax = lenmin, lenmax
        assert 0 <= self.lenmin and self.lenmin <= self.lenmax, \
            "{0}: inconsistent length [{1},{2}]". \
                format(self, self.lenmin, self.lenmax)
        self.cleanParams(WithLength.DIRS)


class NULLGenerator(Generator):
    """Generate a NULL value."""
    DIRS = {}

    def __init__(self, att=None, params=None):
        # check 'null'
        self.att = att
        p = params if params else att.params if att else {}
        if 'null' in p:
            assert p['null'] == 1.0, \
                "{0}: 'null' is {1} instead of 1.0".format(self, p['null'])
        Generator.__init__(self, att, params)
        self.cleanParams(NULLGenerator.DIRS)

    def genData(self):
        return None

    def getData(self):
        return None


class ListGenerator(RandomGenerator):
    """Generate from a list of generators.

    - Generator[] gens
    """
    DIRS = {}

    def __init__(self, att=None, params=None, name=None, gens=None):
        RandomGenerator.__init__(self, att, params)
        if gens:
            assert not params
            assert not name in self.params
            self.gens = gens
        else:
            assert name in self.params, \
                "{0}: mandatory '{1}' directive".format(self, name)
            l = self.params[name]
            if l:
                self.gens = [macroGenerator(n) if n in df_macro else \
                                 createGenerator(None, n, {}) \
                             for n in l.split(',')]
            else:
                self.gens = []
            # self.gens = list(map(macroGenerator, self.params[name].split(',')))
        self.cleanParams(ListGenerator.DIRS)

    def mapGen(self, func):
        super(ListGenerator, self).mapGen(func)
        list(map(lambda g: g.mapGen(func), self.gens))

    def genData(self):
        return [c.getData() for c in self.gens]


class CatGenerator(ListGenerator):
    """Generate by concatenating texts from other generators. """
    DIRS = {'cat': str}

    def __init__(self, att=None, params=None, gens=None):
        ListGenerator.__init__(self, att, params, 'cat', gens)
        self.cleanParams(CatGenerator.DIRS)

    def genData(self):
        return ''.join(str(c) for c in super(CatGenerator, self).genData())


class TupleGenerator(ListGenerator):
    """Generate a tuple"""
    DIRS = {'tuple': str}

    def __init__(self, att=None, params=None):
        ListGenerator.__init__(self, att, params, 'tuple')
        self.cleanParams(TupleGenerator.DIRS)

    def genData(self):
        return tuple(super(TupleGenerator, self).genData())


class ReduceGenerator(ListGenerator):
    """Reduce a list of float generators"""
    DIRS = {'reduce': str, 'op': str}
    OPS = {'+': (lambda a, b: float(a) + float(b)),
           '*': (lambda a, b: float(a) * float(b)),
           'max': (lambda a, b: a if a > b else b),
           'min': (lambda a, b: a if a < b else b),
           # this is really akin to CatGenerator
           'cat': (lambda a, b: str(a) + str(b))}

    def __init__(self, att=None, params=None):
        ListGenerator.__init__(self, att, params, 'reduce')
        op = self.params.get('op', '+')
        assert op in ReduceGenerator.OPS, \
            "{0}: unexpected operation '{1}', expecting {2}". \
                format(self, op, sorted(ReduceGenerator.OPS))
        self.op = ReduceGenerator.OPS[op]
        self.cleanParams(ReduceGenerator.DIRS)

    def genData(self):
        return reduce(self.op, super(ReduceGenerator, self).genData())


class AltGenerator(RandomGenerator):
    """Generate from one in a weighted set.

    - Generator[] alts: generators to choose from
    - int[] weight: their respective weights
    - int total_weight: sum of weights
    """
    DIRS = {'alt': str}

    def __init__(self, att=None, params=None, gens=None):
        RandomGenerator.__init__(self, att, params)
        if gens != None:
            assert not params
            self.alts = gens
            self.total_weight = len(gens)
            self.weight = [1 for i in range(self.total_weight)]
        else:
            assert 'alt' in self.params, \
                "{0}: mandatory 'alt' directive".format(self)
            self.alts = []
            self.weight = []
            self.total_weight = 0
            # parse weighted macro alt: 'macro1:3,macro2,macro3:3'
            # it could be nice to order them by decreasing weight
            for mw in self.params['alt'].split(','):
                if ':' in mw:
                    m, w = mw.split(':')
                    w = int(w)
                else:
                    m, w = mw, 1
                assert w > 0, "{0}: weight {1} must be > 0".format(self, w)
                gen = macroGenerator(m)
                self.alts.append(gen)
                self.weight.append(w)
                self.total_weight += w
                if isinstance(gen, IntGenerator) and gen.size == None:  # ???
                    gen.setSize(opts.size)
        self.cleanParams(AltGenerator.DIRS)

    def mapGen(self, func):
        super(AltGenerator, self).mapGen(func)
        list(map(lambda g: g.mapGen(func), self.alts))

    def genData(self):
        # weighted choice
        index, weight = 0, self._rand.randrange(self.total_weight)
        while weight >= self.weight[index]:
            weight -= self.weight[index]
            index += 1
        return self.alts[index].genData()


class WithPersistent(Generator):
    """Persistent value per tuple."""

    def __init__(self):
        self.last_tuple_count = 0
        self.last_value = None

    def super(self):
        return super(WithPersistent, self)

    def genData(self):
        if self.last_tuple_count != tuple_count:
            self.last_tuple_count = tuple_count
            self.last_value = self.super().genData()
        return self.last_value


class PersistentGenerator(WithPersistent):
    """Encapsulate a generator to make it persistent."""

    def __init__(self, gen):
        WithPersistent.__init__(self)
        self.gen = gen

    def super(self):  # hmmm...
        return self.gen

    def mapGen(self, func):
        super(PersistentGenerator, self).mapGen(func)
        self.gen.mapGen(func)


class ValueGenerator(Generator):
    """Generate a constant value per tuple"""
    values = {}
    DIRS = {'value': str}

    def __init__(self, att, params):
        Generator.__init__(self, att, params)
        assert 'value' in self.params, \
            "{0}: mandatory 'value' directive".format(self)
        value = self.params['value']
        if not value in ValueGenerator.values:
            ValueGenerator.values[value] = \
                PersistentGenerator(macroGenerator(value))
        self.value = ValueGenerator.values[value]
        self.cleanParams(ValueGenerator.DIRS)

    def mapGen(self, func):
        super(ValueGenerator, self).mapGen(func)
        self.value.mapGen(func)

    def genData(self):
        return self.value.genData()

    def getData(self):
        return self.genData()
