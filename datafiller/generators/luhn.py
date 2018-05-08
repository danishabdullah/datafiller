from __future__ import print_function, unicode_literals

import re

from datafiller.generators.seed import SeedGenerator
from datafiller.scripts.cli import opts

__author__ = "danishabdullah"
__all__ = ('LuhnGenerator',)


class LuhnGenerator(SeedGenerator):
    """Generate stuff with a Luhn checksum.

    - int length: (default 16 for bank card numbers)
    - str prefix: optional prefix, defaults to empty
    - ckSum: function to compute check digit
    """
    DIRS = {'length': int, 'prefix': str}

    def __init__(self, att, params=None):
        SeedGenerator.__init__(self, att, params)
        self.length = self.params.get('length', 16)
        assert self.length >= 2, \
            "{0}: 'length' {1} must be > 1".format(self, self.length)
        if self.size == None:
            self.setSize(opts.size if opts.size else 100)
        self.prefix = str(self.params.get('prefix', ''))
        assert len(self.prefix) < self.length, \
            "{0}: 'prefix' \"{1}\" length not smaller than 'length' {2}". \
                format(self, self.prefix, self.length)
        if self.__class__ == LuhnGenerator:
            assert re.match(r'\d*$', self.prefix), \
                "{0}: 'prefix' {1} not decimal".format(self, self.prefix)
        self.ckSum = self.luhnDigit
        self.cleanParams(LuhnGenerator.DIRS)

    def luhnDigit(self, s):
        """Luhn's algorithm, see http://en.wikipedia.org/wiki/Luhn_algorithm."""
        assert len(s) == self.length - 1
        t = s[-2::-2] + ''.join(str(2 * int(c)) for c in s[-1::-2])
        return str(9 * sum(int(i) for i in t) % 10)

    def genData(self):
        self.reseed()
        code = self.prefix + \
               ''.join(str(self._rand2.randint(0, 9)) \
                       for i in range(self.length - len(self.prefix) - 1))
        return code + self.ckSum(code)
