from __future__ import print_function, unicode_literals

import sys

from datafiller.scripts.cli import opts

__author__ = "danishabdullah"
__all__ = ('StdoutExitError',)


class StdoutExitError(BaseException):
    """Exception class used for unit tests."""

    def __init__(self, msg=''):
        print('## ' + msg)
        if not opts.debug:
            sys.exit(1)
