from __future__ import print_function, unicode_literals

from datafiller.generators.base import WithSubgen, WithLength
from datafiller.generators.numeric import IntGenerator

__author__ = "danishabdullah"

__all__ = ('ArrayGenerator',)


class ArrayGenerator(WithSubgen, WithLength, IntGenerator):
    """Generate list from another generator."""
    DIRS = {'array': str}

    def __init__(self, att=None, params=None, dir='array',
                 lenmin=5, lenmax=25, gen=None):
        IntGenerator.__init__(self, att, params)
        if gen:
            assert not dir in self.params  # constructor consistency
            self.subgen = gen
        else:
            if dir == 'array' and not dir in self.params:
                # empty array!
                self.subgen = None
            else:
                WithSubgen.__init__(self, dir, att, self.params)
        WithLength.__init__(self, lenmin, lenmax)
        # set repetition
        if self.subgen:
            self.setSize(self.lenmax - self.lenmin + 1)
            self.offset = self.lenmin
        else:  # empty array
            self.offset, self.size = 0, 1
        self.cleanParams(ArrayGenerator.DIRS)

    def genData(self):
        return [self.subgen.genData()
                for i in range(super(ArrayGenerator, self).genData())]
