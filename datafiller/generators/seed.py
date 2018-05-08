from __future__ import print_function, unicode_literals

import random

from datafiller.generators.numeric import IntGenerator

__author__ = "danishabdullah"
__all__ = ("SeedGenerator",)


class SeedGenerator(IntGenerator):
    DIRS = {}

    def __init__(self, att, params):
        IntGenerator.__init__(self, att, params)
        self._rand2 = random.Random()
        self.cleanParams(SeedGenerator.DIRS)

    def reseed(self):
        self._rand2.seed(self.seed + str(super(SeedGenerator, self).genData()))

    def genData(self):
        raise Exception("{0}: cannot call genData() on this class")
