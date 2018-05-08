from __future__ import print_function, unicode_literals

from datafiller.generators.base import RandomGenerator, WithLength

__author__ = "danishabdullah"

__all__ = ('BoolGenerator', 'BitGenerator')


class BoolGenerator(RandomGenerator):
    """Generate True/False at a given 'rate'.

    - float rate: truth's rate, defaults to 0.5
    """
    DIRS = {'rate': float}

    def __init__(self, att, params=None):
        RandomGenerator.__init__(self, att, params)
        self.rate = self.params.get('rate', 0.5)
        assert 0.0 <= self.rate and self.rate <= 1.0, \
            "{0}: rate {1} not in [0,1]".format(self, self.rate)
        self.cleanParams(BoolGenerator.DIRS)

    def genData(self):
        return False if self.rate == 0.0 else \
            True if self.rate == 1.0 else \
                self._rand.random() < self.rate


class BitGenerator(WithLength, RandomGenerator):
    DIRS = {}

    def __init__(self, att=None, params=None):
        RandomGenerator.__init__(self, att, params)
        WithLength.__init__(self, 8, 32)
        self.cleanParams(BitGenerator.DIRS)

    def genData(self):
        len = self._rand.randint(self.lenmin, self.lenmax)
        return "{0:0{1}b}".format(self._rand.getrandbits(len), len)
