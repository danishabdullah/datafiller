from __future__ import print_function, unicode_literals

import re

from datafiller.consts import RECHARS, UCHARS, df_txt, df_flt, df_int, df_str, df_bol
from datafiller.globals import df_macro
from datafiller.scripts.cli import opts

__author__ = "danishabdullah"

import sys

if sys.version_info < (3,):
    # python 2

    range = xrange  # ah!
    numeric_types = (int, long, float, complex)
    u = lambda s: unicode(s, opts.encoding)  # for outside strings
    u8 = lambda s: unicode(s, 'utf-8')  # for strings in this file
    bytes = bytearray  # ah!
    str = unicode  # ah! should it be u? u8? depends?
    # see also print_function import above
    # see also print overriding below
else:
    # python 3

    numeric_types = (int, float, complex)
    u = lambda s: s  # hmmm... too late, managed by fileinput...
    u8 = lambda s: s  # the file is in utf-8
    unichr = chr  # ah!
    long = int  # ah!
    # see print overriding below


def unescape(s, regexp=False):
    """Return an unescaped string."""
    r, i = u8(''), 0
    # hmmm... not very efficient, and probably buggy
    while i < len(s):
        c = s[i]
        if c == '\\':
            assert i + 1 < len(s), \
                "escaped string '{0}' must not end with '\\'".format(s)
            if re.match(r'[012][0-7]{2}', s[i + 1:]):  # octal
                r += chr(int(s[i + 1:i + 4], 8))
                i += 4
            elif re.match(r'[xX][0-9a-fA-F]{2}', s[i + 1:]):  # hexadecimal
                r += chr(int(s[i + 2:i + 4], 16))
                i += 4
            elif re.match(r'u[0-9a-fA-F]{4}', s[i + 1:]):  # 4 digit unicode
                r += unichr(int(s[i + 2:i + 6], 16))
                i += 6
            elif re.match(r'U[0-9a-fA-F]{8}', s[i + 1:]):  # 8 digit unicode
                r += unichr(int(s[i + 2:i + 10], 16))
                i += 10
            else:  # other escaped characters
                c = s[i + 1]
                r += u8(RECHARS[c]) if regexp and c in RECHARS else \
                    u8(UCHARS[c]) if c in UCHARS else \
                        c
                i += 2
        else:
            r += c
            i += 1
    return r


def debug(level, message):
    """Print a debug message, maybe."""
    if opts.debug >= level:
        sys.stderr.write("*" * level + " " + message + "\n")


def getParams(dfline):
    """return a dictionnary from a string like "x=123 y='str' ...". """
    if dfline == '':
        return {}
    params = {}
    dfline += ' '
    # eat up leading blanks, just in case
    while dfline[0] == ' ':
        dfline = dfline[1:]
    # do parse
    while len(dfline) > 0:
        # python does not like combining assign & test, so use continue
        d = df_txt.match(dfline)
        if d:
            params[d.group(1)] = str(d.group(2))
            dfline = d.group(3)
            continue
        d = df_flt.match(dfline)
        if d:
            params[d.group(1)] = float(d.group(2))
            dfline = d.group(3)
            continue
        d = df_int.match(dfline)
        if d:
            params[d.group(1)] = int(d.group(2))
            dfline = d.group(3)
            continue
        d = df_str.match(dfline)
        if d:
            # handle use of a macro directly
            if d.group(1) == 'use':
                assert d.group(2) in df_macro, \
                    "macro {0} is defined".format(d.group(2))
                params.update(df_macro[d.group(2)])
            else:
                params[d.group(1)] = d.group(2)
            dfline = d.group(3)
            continue
        d = df_bol.match(dfline)
        if d:
            params[d.group(1)] = True
            dfline = d.group(2)
            continue
        raise Exception("cannot parse: '{0}'".format(dfline))
    return params
