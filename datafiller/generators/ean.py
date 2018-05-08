from __future__ import print_function, unicode_literals

import re

from datafiller.generators.luhn import LuhnGenerator
from datafiller.scripts.cli import db

__author__ = "danishabdullah"

__all__ = ('EANGenerator',)


# there are some isbn/ean management modules, but they must be installed
# they would be only useful for computing the checksum digit, no big deal
class EANGenerator(LuhnGenerator):
    """Generate random EAN identifiers.

    EAN = International Article Number (!)
    """
    DIRS = {}

    def __init__(self, att=None, params=None):
        LuhnGenerator.__init__(self, att, params)
        if not self.type:
            self.type = 'ean13'
        # override length, prefix, cksum
        self.length = db.eanType(self.type)
        # set prefix for IS*N embedded in EAN13. ISBN13 could also use 979.
        if not self.prefix:
            self.prefix = '977' if self.type == 'issn13' else \
                '978' if self.type == 'isbn13' else \
                    '9790' if self.type == 'ismn13' else \
                        'M' if self.type == 'ismn' else \
                            ''
        assert re.match(r'M?\d*', self.prefix), \
            "{0}: invalid 'prefix' {0}".format(self, self.prefix)
        assert len(self.prefix) < self.length, \
            "{0}: 'prefix' \"{1}\" length must be smaller than 'length' {2}". \
                format(self, self.prefix, self.length)
        self.ckSum = self.ckSumISN \
            if self.type == 'isbn' or self.type == 'issn' else \
            self.ckSumEAN  # *13 & UPC & ISMN
        self.cleanParams(EANGenerator.DIRS)

    # checksum methods
    def ckSumEAN(self, s):
        assert len(s) == self.length - 1
        t, w = 0, 3
        for i in range(1, self.length):
            # special 'M' hack for ISMN numbers
            t += w * int(3 if s[-i] == 'M' else s[-i])
            w = 4 - w  # 3 -> 1 -> 3 ...
        return str(-t % 10)

    def ckSumISN(self, s):
        assert len(s) == self.length - 1
        t = sum(int(s[-i]) * (i + 1) for i in range(1, self.length)) % 11
        return '0' if t == 0 else 'X' if t == 1 else str(11 - t)
