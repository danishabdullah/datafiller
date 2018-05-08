from __future__ import print_function, unicode_literals

from datafiller.generators.base import WithPersistent
from datafiller.generators.numeric import IntGenerator
from datafiller.globals import df_macro

__author__ = "danishabdullah"

__all__ = ('SharedGenerator',)


class SharedGenerator(WithPersistent, IntGenerator):
    """Generate persistent integers."""
    _generators = {}
    DIRS = {}

    @staticmethod
    def getGenerator(obj, name):
        if not name in SharedGenerator._generators:
            assert name in df_macro, \
                "{0}: 'share' {1} directive must be a macro".format(obj, name)
            SharedGenerator._generators[name] = \
                SharedGenerator(name, df_macro[name])
        return SharedGenerator._generators[name]

    def __init__(self, name, params):
        assert name != None and params != None, "mandatory parameters"
        size = params['size'] if 'size' in params else None
        mult = params['mult'] if 'mult' in params else None
        IntGenerator.__init__(self, None, params)
        self.nullp = 0.0
        # set size, possibly overriding super constructor
        if size:
            self.setSize(size)
        elif mult and opts.size:
            self.setSize(mult * opts.size)
        elif opts.size:
            self.setSize(opts.size)
        assert self.size != None, \
            "{0}: size not set in macro {1}".format(self, name)
        # persistent
        WithPersistent.__init__(self)
        self.cleanParams(SharedGenerator.DIRS)
