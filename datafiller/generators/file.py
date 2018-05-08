from __future__ import print_function, unicode_literals

from datafiller.generators.numeric import IntGenerator
from datafiller.scripts.cli import opts
from datafiller.tests import some_tmp_files_to_unlink

__author__ = "danishabdullah"
__all__ = ('FileGenerator',)


class FileGenerator(IntGenerator):
    """Generate contents from files.

    - str[] files: list of files
    """
    DIRS = {'file': str, 'mode': str}

    def __init__(self, att, params=None):
        IntGenerator.__init__(self, att, params)
        # get list of files
        import os, glob
        self.files = []
        assert 'file' in self.params, "{0}: no directive 'file'".format(self)
        if some_tmp_files_to_unlink:
            # ignore files
            self.files = some_tmp_files_to_unlink
        else:
            # normal operation, process directive files
            for f in self.params['file'].split(os.pathsep):
                self.files += glob.glob(f)
        # handle conversion
        mode = self.params.get('mode', 'blob')
        assert mode == 'blob' or mode == 'text', \
            "{0}: mode must be 'blob' or 'text'".format(self)
        self.conv = bytes if mode == 'blob' else \
            lambda s: s.decode(opts.encoding)
        # set size & offset
        assert len(self.files) > 0, "{0}: non empty set of files".format(self)
        if self.size == None:
            self.setSize(len(self.files))
        if self.size > len(self.files):
            self.size = len(self.files)
        self.offset = 0
        self.cleanParams(FileGenerator.DIRS)

    def genData(self):
        f = open(self.files[super(FileGenerator, self).genData()], "rb", encoding='utf-8')
        s = self.conv(f.read())
        f.close()
        return s
