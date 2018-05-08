from __future__ import print_function, unicode_literals

__author__ = "danishabdullah"

import re

# escaped list of caracters for . in regular expressions
RE_DOT = r' -~'  # from ASCII 0x20 to 0x7E
RE_POSIX_CC = { \
    'alpha': 'A-Za-z', 'alnum': 'A-Za-z0-9', 'ascii': ' -~', 'blank': r' \t',
    'cntrl': '\000-\037\177', 'digit': '0-9', 'graph': '!-~', 'lower': 'a-z',
    'print': ' -~', 'punct': ' -/:-@[-^`{-~', 'space': r'\s', 'upper': 'A-Z',
    'word': r'\w', 'xdigit': '0-9a-fA-F'
}

# re helpers: alas this is not a parser.

# identifier
RE_IDENT = r'"[^"]+"|`[^`]+`|[a-z0-9_]+'
# possibly schema-qualified
# ??? this won't work with quoted identifiers?
# 1=schema, 2=table
RE_IDENT2 = r'({0})\.({0})|{0}'.format(RE_IDENT)

# SQL commands
RE_CMD = r'CREATE|ALTER|DROP|SELECT|INSERT|UPDATE|DELETE|SET|GRANT|REVOKE|SHOW'

# types
RE_SER = r'(SMALL|BIG)?SERIAL|SERIAL[248]'
RE_BLO = r'BYTEA|BLOB'
RE_INT = r'{0}|(TINY|SMALL|MEDIUM)INT|INT[248]|INTEGER|INT\b'.format(RE_SER)
RE_FLT = r'REAL|FLOAT|DOUBLE\s+PRECISION|NUMERIC|DECIMAL'
RE_TXT = r'TEXT|CHAR\(\d+\)|VARCHAR\(\d+\)'
RE_BIT = r'BIT\(\d+\)|VARBIT\(\d+\)'
RE_TSTZ = r'TIMESTAMP(\s+WITH\s+TIME\s+ZONE)?'
RE_INTV = r'INTERVAL'
RE_TIM = r'DATE|{0}|{1}'.format(RE_TSTZ, RE_INTV)
RE_BOO = r'BOOL(EAN)?'
RE_IPN = r'INET|CIDR'
RE_MAC = r'MACADDR'
RE_EAN = r'EAN13|IS[BMS]N(13)?|UPC'
RE_GEO = r'POINT|LINE|LSEG|BOX|PATH|POLYGON|CIRCLE'
RE_OTH = r'UUID'

# all predefined PostgreSQL types
RE_TYPE = '|'.join([RE_INT, RE_FLT, RE_TXT, RE_BIT, RE_TIM, RE_BOO, RE_BLO,
                    RE_IPN, RE_MAC, RE_EAN, RE_GEO, RE_OTH])

RE_ARRAY = r'((\s+ARRAY)?(\s*\[[][0-9 ]*\])?)?'

# and arrays thereof
RE_ALLT = r'({0}){1}'.format(RE_TYPE, RE_ARRAY)

# SQL syntax
new_object = re.compile(r"^\s*({0})\s".format(RE_CMD), re.I)
# 1=table name, [2, 3]
create_table = \
    re.compile(r'^\s*CREATE\s+TABLE\s*({0})\s*\('.format(RE_IDENT2), re.I)
# 1=type name, [2, 3]
create_enum = \
    re.compile(r'^\s*CREATE\s+TYPE\s+({0})\s+AS\s+ENUM'.format(RE_IDENT2), re.I)
# 1=type
create_type = \
    re.compile(r'\s*CREATE\s+TYPE\s+({0})\s+AS'.format(RE_IDENT2), re.I)

# 1=?, 2=column, 3=type
r_column = r'^\s*,?\s*(ADD\s+COLUMN\s+)?({0})\s+({1})'.format(RE_IDENT, RE_ALLT)
column = re.compile(r_column, re.I)
is_int = re.compile(r'^({0})$'.format(RE_INT), re.I)
is_ser = re.compile(r'^({0})$'.format(RE_SER), re.I)
# enums are added when definitions are encountered
column_enum = None

s_reference = \
    r'.*\sREFERENCES\s+({0})\s*(\(({1})\))?'.format(RE_IDENT2, RE_IDENT)
# 1=table, [2, 3], 4=?, 5=dest columns (?)
reference = re.compile(s_reference, re.I)
primary_key = re.compile('.*\sPRIMARY\s+KEY', re.I)
unique = re.compile(r'.*\sUNIQUE', re.I)
not_null = re.compile(r'.*\sNOT\s+NULL', re.I)
s_unicity = r'.*(UNIQUE|PRIMARY\s+KEY)\s*\(([^\)]+)\)'
# 1=unicity type, 2=columns
unicity = re.compile(s_unicity, re.I)
# 1=?, 2=table name, [3, 4]
alter_table = \
    re.compile(r'\s*ALTER\s+TABLE\s+(ONLY\s+)?({0})'.format(RE_IDENT2), re.I)
add_constraint = r',?\s*ADD\s+CONSTRAINT\s+({0})\s+'.format(RE_IDENT)
# 1=constraint name, 2=unicity type, 3=columns
add_unique = re.compile(add_constraint + s_unicity, re.I)
# 1=constraint_name, 2=source columns, 3=table, [4, 5], 6=, 7=dest columns
add_fk = \
    re.compile(add_constraint + r'FOREIGN\s+KEY\s*\(([^\)]+)\)' + s_reference,
               re.I)
# 1=column
alter_column = re.compile(r',?\s*ALTER\s+COLUMN\s+({0})'.format(RE_IDENT), re.I)

# DETECT DATAFILLER DIRECTIVES
# commented-out directives, say '--- df...' or '---- df...' or '-- -- df...'
df_junk = re.compile('.*?--.*-\s*df.*')
# simple directive: 1=contents
df_dir = re.compile(r'.*--\s*df[^:]*:\s*(.*)')
# macro definition: 1=name, 2=contents
df_mac = re.compile(r'.*--\s*df\s+([\w\.]+)\s*:\s*(.*)')
# explicit table: 2=name
df_tab = \
    re.compile(r'.*--\s*df[^:]*\s+(t|table)=({0})(\s|:)'. \
               format(RE_IDENT2), re.I)
# explicit attribute: 2=name
df_att = \
    re.compile(r'.*--\s*df[^:]*\s+(a|att|attribute)=({0})(\s|:)'. \
               format(RE_IDENT), re.I)
# string/float/int directives: 1=name 2=value 3=reminder
df_txt = re.compile(r'(\w+)=\'([^\']*)\'\s+(.*)')
df_flt = re.compile(r'(\w+)=(-?\d+\.\d*)\s+(.*)')
df_int = re.compile(r'(\w+)=(-?\d+)\s+(.*)')
df_str = re.compile(r'(\w+)=(\S*)\s+(.*)')
# simple directive: 1=name 2=reminder
df_bol = re.compile(r'(\w+)\s+(.*)')

# remove SQL comments & \xxx commands
comments = re.compile(r'(.*?)\s*--.*')
backslash = re.compile(r'\s*\\')

# some ASCII control characters
UCHARS = {'0': '\0', 'a': '\a', 'b': '\b', 'f': '\f', \
          'n': '\n', 'r': '\r', 't': '\t', 'v': '\v'}
# re special escaped characters, which may appear within [] or out of them
RECHARS = {'d': '0-9', 's': ' \t\r\n\v\f', 'w': 'a-zA-Z0-9_', \
           'h': '0-9a-f', 'H': '0-9A-F'}
