from __future__ import print_function, unicode_literals

import math
import random
import sys

from datafiller.generators.base import RandomGenerator
from datafiller.scripts.cli import opts
from datafiller.utils import u8, long

__author__ = "danishabdullah"
__all__ = ('CountGenerator', 'FloatGenerator', 'IntGenerator')


class CountGenerator(RandomGenerator):
    """Generate a count."""
    DIRS = {'start': str, 'step': int, 'format': str}

    def __init__(self, att, params=None):
        RandomGenerator.__init__(self, att, params)
        self.start = int(self.params.get('start', 1))
        self.step = int(self.params.get('step', 1))
        self.format = u8("{{0:{0}}}").format(self.params.get('format', 'd'))
        assert self.step != 0, "{0}: 'step' must not be zero".format(self)
        self.cleanParams(CountGenerator.DIRS)

    def genData(self):
        self.gens += 1
        return self.format.format((self.gens - 1) * self.step + self.start)


class FloatGenerator(RandomGenerator):
    """Generate floats with various distributions.

    The generation is driven by 'type' and parameters 'alpha' and 'beta'.
    - str sub: subtype of random generator
    - float alpha, beta: parameters
    """
    DIRS = {'float': str, 'alpha': float, 'beta': float}

    def __init__(self, att, params=None):
        RandomGenerator.__init__(self, att, params)
        self.sub = self.params.get('float', 'uniform')
        if self.sub == True or self.sub == '':
            self.sub = 'uniform'
        self.alpha = self.params.get('alpha', 0.0)
        self.beta = self.params.get('beta', 1.0)
        r, a, b, s = self._rand, self.alpha, self.beta, self.sub
        # check consistency
        if self.sub in ['exp', 'pareto']:
            assert not 'beta' in self.params, \
                "{0}: unexpected 'beta' for float generator '{1}'". \
                    format(self, s)
        # genData() is overwritten depending on the generator subtype
        self.genData = \
            (lambda: r.gauss(a, b)) if s == 'gauss' else \
                (lambda: r.betavariate(a, b)) if s == 'beta' else \
                    (lambda: r.expovariate(a)) if s == 'exp' else \
                        (lambda: r.gammavariate(a, b)) if s == 'gamma' else \
                            (lambda: r.lognormvariate(a, b)) if s == 'log' else \
                                (lambda: r.normalvariate(a, b)) if s == 'norm' else \
                                    (lambda: r.paretovariate(a)) if s == 'pareto' else \
                                        (lambda: r.uniform(a, b)) if s == 'uniform' else \
                                            (lambda: r.vonmisesvariate(a, b)) if s == 'vonmises' else \
                                                (lambda: r.weibullvariate(a, b)) if s == 'weibull' else \
                                                    None
        assert self.genData, \
            "{0}: unexpected float generator '{1}'".format(self, s)
        self.cleanParams(FloatGenerator.DIRS)


class IntGenerator(RandomGenerator):
    """Generate integers, possibly mangled and offset.

    - int offset: generate between offset and offset+size-1
    - int shift, step, xor: mangling parameters
      return offset + (shift + step * (i "^" xor)) % size
    - str sub: serial, serand, uniform, power & scale
      . serial: a counter
      . serand: serial up to size, then random
    - uniform, power and scale are random generators
    - power & scale use either parameter 'alpha' or 'rate' to define
      their skewness.
    """
    # 60 handy primes for step mangling, about every 10,000,000
    PRIMES = [1234567129, 1244567413, 1254567911, 1264567631, 1274567381,
              1284567247, 1294567787, 1304567897, 1314568139, 1324568251,
              1334568007, 1344567943, 1354567987, 1364568089, 1374568339,
              1384568699, 1394567981, 1404568153, 1414568359, 1424568473,
              1434567973, 1444568269, 1454567999, 1464568463, 1474568531,
              1484568011, 1494568219, 1504568887, 1514568533, 1524567899,
              1534568531, 1544568271, 1554568441, 1564568519, 1574568419,
              1584567949, 1594568149, 1604568283, 1614568231, 1624568417,
              1634568427, 1644568397, 1654568557, 1664568677, 1674568109,
              1684568321, 1694568241, 1704567959, 1714568899, 1724568239,
              1734567899, 1744567901, 1754567891, 1764567913, 1774567901,
              1784567899, 1794567911, 1804567907, 1814567891, 1824567893]
    DIRS = {'sub': str, 'mangle': bool,
            'size': int, 'offset': int, 'step': int, 'shift': int, 'xor': int,
            'alpha': float, 'rate': float}

    def __init__(self, att, params=None):
        RandomGenerator.__init__(self, att, params)
        # set generator subtype depending on attribute
        self.sub = self.params.get('sub')
        if not self.sub:
            self.sub = 'serial' if att != None and att.isUnique() else 'uniform'
        # {'x','y'} does not work with 2.6
        assert self.sub in ['serial', 'serand', 'uniform', 'power', 'scale'], \
            "{0}: invalid int generator '{1}'".format(self, self.sub)
        # set offset from different sources
        # first check for explicit directives
        if 'offset' in self.params:
            self.offset = self.params['offset']
        # then PK or FK information
        elif att != None and att.isPK and opts.offset:
            self.offset = opts.offset
        elif att != None and att.FK:
            fk = att.FK.getPK()
            self.offset = \
                fk.params.get('offset', opts.offset if opts.offset else 1)
        else:
            self.offset = 1
        # scale & power
        if 'alpha' in self.params or 'rate' in self.params:
            assert self.sub in ['power', 'scale'], \
                "{0}: unexpected 'alpha'/'beta' for int generator '{1}'". \
                    format(self, self.sub)
        assert not ('alpha' in self.params and 'rate' in self.params), \
            "{0}: not both 'alpha' and 'rate' for '{1}'".format(self, self.sub)
        if 'alpha' in self.params:
            self.alpha, self.rate = float(self.params['alpha']), None
        elif 'rate' in self.params:
            self.alpha, self.rate = None, float(self.params['rate'])
        else:
            self.alpha, self.rate = None, None
        # set step, shift & xor...
        self.shift, self.xor, self.step = 0, 0, 1
        self.mangle = self.params.get('mangle', False)
        self.step = self.params['step'] if 'step' in self.params else \
            IntGenerator.PRIMES[random.randrange(0, \
                                                 len(IntGenerator.PRIMES))] if self.mangle else \
                1
        assert self.step != 0, "{0}: 'step' must not be zero".format(self)
        self.shift = self.params['shift'] if 'shift' in self.params else None
        self.xor = self.params['xor'] if 'xor' in self.params else None
        self.mask = 0
        # set size if explicit, other will have to be set later.
        if 'size' in self.params:
            self.setSize(self.params['size'])
        elif att != None and att.size != None:
            self.setSize(att.size)  # possibly computed from table & mult
        else:  # later? when??
            self.size = None
        self.cleanParams(IntGenerator.DIRS)

    def setSize(self, size):
        assert (isinstance(size, int) or isinstance(size, long)) and size > 0, \
            "{0}: 'size' {1} must be > 0".format(self, size)
        self.size = size
        # shortcut if nothing to generate...
        if size <= 1:
            self.shift = 0
            return
        # adjust step, xor, shift depending on size
        if self.step != 1 and math.gcd(size, self.step) != 1:
            # very unlikely for big primes steps
            sys.stderr.write("{0}: step {1} ignored for size {2}\n".
                             format(self.att, self.step, size))
            self.step = 1
        if self.xor == None:
            self.xor = random.randrange(1, 1000 * size) if self.mangle else 0
        if self.shift == None:
            self.shift = random.randrange(0, size) if self.mangle else 0
        if self.xor != 0:
            # note: int.bit_length available from 2.7 & 3.1
            m = 1
            while m <= self.size:
                m *= 2
            self.mask = int(m / 2)  # ???
        # get generator parameters, which may depend on size
        if self.sub == 'power' or self.sub == 'scale':
            if self.rate != None:
                assert 0.0 < self.rate and self.rate < 1.0, \
                    "{0}: rate {1} not in (0,1)".format(self, self.rate)
                if self.sub == 'power':
                    self.alpha = - math.log(size) / math.log(self.rate)
                else:  # self.sub == 'scale':
                    self.alpha = self.rate * (size - 1.0) / (1.0 - self.rate)
            elif self.alpha == None:
                self.alpha = 1.0
            assert self.alpha > 0, \
                "{0}: 'alpha' {1:f} not > 0".format(self, self.alpha)
        else:  # should not get there
            assert self.alpha == None, \
                "{0}: useless 'alpha' {1} set".format(self, self.alpha)

    def genData(self):
        assert self.size != None and self.size > 0, \
            "{0}: cannot draw from empty set".format(self)
        # update counter
        self.gens += 1
        # set base in 0..size-1 depending on generator type
        if self.size == 1:
            return self.offset
        assert self.shift != None, "{0}: shift is set".format(self)
        if self.sub == 'serial' or \
                self.sub == 'serand' and self.gens - 1 < self.size:
            base = (self.gens - 1) % self.size
        elif self.sub == 'uniform' or self.sub == 'serand':
            base = int(self._rand.randrange(0, self.size))
        elif self.sub == 'power':
            base = int(self.size * self._rand.random() ** self.alpha)
        else:  # self.sub == 'scale':
            v = self._rand.random()
            base = int(self.size * (v / ((1 - self.alpha) * v + self.alpha)))
        assert 0 <= base and base < self.size, \
            "{0}: base {1:d} not in [0,{2:d})".format(self, base, self.size)
        # return possibly mangled result
        if self.xor != 0:
            # non linear step: apply xor to the largest possible power of 2
            m = self.mask
            while m > 0:
                if m & self.size != 0 and m & base == 0:
                    base = ((base ^ self.xor) & (m - 1)) | (base & ~ (m - 1))
                    break
                m = int(m / 2)
        # then linear step:
        return self.offset + (self.shift + self.step * base) % self.size
