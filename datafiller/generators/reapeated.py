from __future__ import print_function, unicode_literals

import re

from datafiller.generators.array import ArrayGenerator
from datafiller.generators.base import WithLength

__author__ = "danishabdullah"
__all__ = ('RepeatGenerator',)


class RepeatGenerator(ArrayGenerator):
    """Generate repeated stuff."""
    DIRS = {'repeat': str, 'extent': str}

    def __init__(self, att, params=None, gen=None):
        p = params if params else att.params
        self.att = None
        if 'extent' in p:
            assert \
                not list(filter(lambda d: d in p, WithLength.DIRS.keys())), \
                "{0}: both 'extent' and 'len*' directives".format(self)
            extent = p['extent']
            assert re.match(r'\d+(-\d+)?$', extent), \
                "{0}: bad 'extent' {1}".format(self, extent)
            if extent.find('-') != -1:
                min, max = extent.split('-')
            else:
                min, max = extent, extent
            min, max = int(min), int(max)
            assert 0 <= min and min <= max, \
                "{0}: extent must be 0 <= {1} <= {2}".format(self, min, max)
        else:
            min, max = 1, 1
        ArrayGenerator.__init__(self, att, params, 'repeat', min, max, gen)
        # ??? hmmmm... overwrite extent from type (CHAR(36))
        # WithLength logic shoud distinguish defauts and sets...
        self.setSize(max - min + 1)
        self.offset = min
        self.cleanParams(RepeatGenerator.DIRS)

    def genData(self):
        return ''.join(super(RepeatGenerator, self).genData())
