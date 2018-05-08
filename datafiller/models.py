from __future__ import print_function, unicode_literals

import re

from datafiller.consts import RE_TSTZ, RE_FLT, RE_BLO, RE_IPN, RE_MAC, RE_BIT, is_ser, is_int, RE_EAN
from datafiller.generators import GENERATORS
from datafiller.generators.base import Generator, RandomGenerator, WithLength
from datafiller.generators.funcs import findGenerator, strDict
from datafiller.generators.shared import SharedGenerator
from datafiller.scripts.cli import addType, db, opts
from datafiller.utils import getParams, debug, numeric_types

__author__ = "danishabdullah"
__all__ = ('Model', 'Attribute', 'Table', 'Database', 'CSV', 'PostgreSQL', 'MySQL')


#
# Relation model
#
class Model(object):
    """Modelize something"""
    # global parameters and their types
    PARAMS = {'size': int, 'offset': int, 'null': float, 'seed': str, 'type': str}

    @staticmethod
    def checkPARAMS(obj, params, PARAMS):
        """Check parameters against their description."""
        for k, v in params.items():
            assert k in PARAMS, "unexpected parameter '{0}'".format(k)
            if PARAMS[k] == float:
                assert type(v) is float or type(v) is int, \
                    "type {0} instead of float parameter '{1}'". \
                        format(v.__class__.__name__, k)
            elif PARAMS[k] == int:
                assert type(v) is int, \
                    "type {0} instead of int for parameter '{1}'". \
                        format(v.__class__.__name__, k)
            elif PARAMS[k] == bool:
                assert type(v) is bool, \
                    "type {0} instead bool for parameter '{1}'". \
                        format(v.__class__.__name__, k)
            # fix value type in some cases
            if type(v) == bool and PARAMS[k] == str:
                params[k] = ''
            elif type(v) != str and PARAMS[k] == str:
                params[k] = str(v)
            elif type(v) == int and PARAMS[k] == float:
                params[k] = float(v)
        assert not ('mult' in params and 'size' in params), \
            "{0}: must not have both 'mult' and 'size'".format(obj)
        # else everything is fine

    def __init__(self, name):
        # unquote attributes names (PostgreSQL or MySQL)
        self.quoted = name[0] == '"' or name[0] == '`'
        self.name = name[1:-1] if self.quoted else name.lower()
        self.size = None
        self.params = {}

    def __str__(self):
        return self.getName()

    def checkParams(self):
        Model.checkPARAMS(self, self.params, self.__class__.PARAMS)
        # handle type additions on the fly
        if 'type' in self.params:
            addType(self.params['type'])
            del self.params['type']

    def setParams(self, dfline):
        self.params.update(getParams(dfline))
        self.checkParams()

    def getName(self):
        return db.quoteIdent(self.name) if self.quoted else self.name


class Attribute(Model):
    """Represent an attribute in a table."""
    # all attribute PARAMETERS and their types
    PARAMS = {'nogen': bool, 'mult': float}
    # directives from hidden generators & options
    PARAMS.update(Generator.DIRS)
    PARAMS.update(RandomGenerator.DIRS)
    PARAMS.update(SharedGenerator.DIRS)
    PARAMS.update(WithLength.DIRS)
    # directives from public generators
    import inspect
    for k in GENERATORS:
        if inspect.isclass(GENERATORS[k]):
            PARAMS.update(GENERATORS[k].DIRS)
    # bool directives from generator names
    for k in GENERATORS:
        if not k in PARAMS:
            PARAMS[k] = bool

    # methods
    def __init__(self, name, number, type):
        Model.__init__(self, name)
        self.number = number
        self.type = type.lower()
        self.FK = None
        self.isPK = False
        self.unique = False
        self.not_null = False
        self.gen = None

    def __repr__(self):
        return "{0}: {1} type={2} PK={3} U={4} NN={5} FK=[{6}]". \
            format(self, self.number, self.type,
                   self.isPK, self.unique, self.not_null, self.FK)

    def __str__(self):
        return "Attribute {0}.{1}". \
            format(self.table.getName(), self.getName())

    def getGenerator(self):
        return findGenerator(self, self.params)

    def getData(self):
        assert self.gen, "{0}: generator not set".format(self)
        return self.gen.getData()

    def checkParams(self):
        Model.checkParams(self)
        assert not ('mult' in self.params and 'size' in self.params), \
            "{0}: not both 'mult' and 'size'".format(self)
        # other consistency checks would be possible

    def isUnique(self):
        return self.isPK or self.unique

    def isNullable(self):
        return not self.not_null and not self.isPK

    def isSerial(self):
        return db.serialType(self.type)


class Table(Model):
    """Represent a relational table."""
    # table-level parameters
    PARAMS = {'mult': float, 'size': int, 'nogen': bool,
              'skip': float, 'null': float}

    def __init__(self, name):
        Model.__init__(self, name)
        # attributes
        self.atts = {}
        self.att_list = []  # list of attributes in occurrence order
        self.unique = []
        self.ustuff = {}  # uniques are registered in this dictionnary
        self.constraints = []

    def __str__(self):
        return "Table {0} [{1:d}] ({2})". \
            format(self.getName(), self.size, strDict(self.params))

    def __repr__(self):
        s = str(self) + "\n"
        for att in self.att_list:
            s += "  " + repr(att) + "\n"
        for u in self.unique:
            s += "  UNIQUE: " + str(u) + "\n"
        s += "  CONSTRAINTS: " + str(self.constraints) + "\n"
        return s

    def checkParams(self):
        Model.checkParams(self)

    def addAttribute(self, att):
        self.att_list.append(att)
        self.atts[att.name] = att
        # point back
        att.table = self
        # pg-specific generated constraint names
        if att.isPK:
            self.constraints.append(self.name + '_pkey')
            att.not_null = True
        elif att.isUnique():
            self.constraints.append(self.name + '_' + att.name + '_key')
        elif att.FK:
            self.constraints.append(self.name + '_' + att.name + '_fkey')

    def addUnique(self, atts, type=None):
        if opts.debug: debug(3, "addUnique " + str(atts) + " type=" + type)
        assert len(atts) >= 1
        if len(atts) == 1:
            att = self.getAttribute(atts[0])
            if type != None and type.lower() == 'unique':
                att.unique = True
            else:
                att.isPK = True
                att.not_null = True
        else:  # multiple attributes
            self.unique.append([self.getAttribute(a).number for a in atts])
            self.constraints.append(self.name + '_' + \
                                    '_'.join(a.lower() for a in atts) +
                                    ('_key' if type.lower() == 'unique' else '_pkey'))

    def getAttribute(self, name):
        assert name.lower() in self.atts, "{0} Attribute {1}".format(self, name)
        return self.atts[name.lower()]

    def getPK(self):
        for a in self.att_list:
            if a.isPK:
                return a
        assert False, "{0}: no PK found".format(self)

    def mapGen(self, func):
        # apply func on all attribute's generators
        list(map(lambda g: g.mapGen(func), \
                 map(lambda a: a.gen, filter(lambda x: x.gen, self.att_list))))

    def getData(self):
        # generate initial stuff
        lg = list(filter(lambda x: x.gen, self.att_list))
        # possibly reseed shared
        global tuple_count
        tuple_count += 1
        self.mapGen(lambda s: s.shareSeed())
        l0 = [g.getData() for g in lg]
        l = l0
        tries = opts.tries
        while tries:
            tries -= 1
            nu, collision = 0, False
            sul = []
            for u in self.unique:
                # one case is not implemented:
                # unique contains indexes in att_list, but we do not know
                # to which value it corresponds in the generated list because
                # some attributes may have been skipped in the generation.
                # should generate a mapping to get the index among generated
                assert len(l) == len(self.att_list), \
                    "{0}: no unique subset".format(self)
                nu += 1
                su = str(nu) + ':' + str([l[i - 1] for i in u])
                if su in self.ustuff:
                    collision = True
                    break  # non unique tuple
                else:
                    sul.append(su)
            if collision:
                # update l, but reuse l0 if serial/pk, otherwise it cycles!
                i = 0
                l = []
                # reseed again! otherwise the new value would be generated.
                # another option would be to keep the previous value when
                # the generator is synchronized.
                tuple_count += 1
                self.mapGen(lambda s: s.shareSeed())
                for g in lg:
                    l.append(l0[i] if g.isUnique() or g.isSerial() \
                                 else g.getData())
                    i += 1
                continue  # restart while with updated values
            else:  # record unique value
                for su in sul:
                    self.ustuff[su] = 1
                return l
        assert False, \
            "{0}: cannot build tuple after {1} tries".format(self, opts.tries)


#
# Databases
#

class Database(object):
    """Abstract a database target."""

    def comment(self, s):
        print('-- ' + s)

    def echo(self, s):
        raise Exception('not implemented in abstract class')

    # transactions
    def begin(self):
        raise Exception('not implemented in abstract class')

    def commit(self):
        raise Exception('not implemented in abstract class')

    # operations
    def insertBegin(self, table):
        raise Exception('not implemented in abstract class')

    def insertValue(self, table, value, isLast):
        raise Exception('not implemented in abstract class')

    def insertEnd(self):
        raise Exception('not implemented in abstract class')

    def setSequence(self, att, number):
        raise Exception('not implemented in abstract class')

    def dropTable(self, table):
        return "DROP TABLE {0};".format(self.quote_ident(table.name))

    def truncateTable(self, table):
        return "DELETE FROM {0};".format(self.quote_ident(table.name))

    # types
    def arrayType(self, type):
        t = type.upper()
        return '[' in t or ' ARRAY' in t

    def serialType(self, type):
        return False

    def intType(self, type):
        t = type.lower()
        return t == 'smallint' or t == 'int' or t == 'integer' or t == 'bigint'

    def textType(self, type):
        t = type.lower()
        return t == 'text' or re.match(r'(var)?char\(', t)

    def boolType(self, type):
        t = type.lower()
        return t == 'bool' or t == 'boolean'

    def dateType(self, type):
        return type.lower() == 'date'

    def intervalType(self, type):
        return type.lower() == 'interval'

    def timestampType(self, type):
        return re.match(RE_TSTZ + '$', type, re.I)

    def floatType(self, type):
        return re.match(RE_FLT + '$', type, re.I)

    def blobType(self, type):
        return re.match(RE_BLO + '$', type, re.I)

    def inetType(self, type):
        return re.match(RE_IPN + '$', type, re.I)

    def macAddrType(self, type):
        return re.match(RE_MAC + '$', type, re.I)

    def eanType(self, s):
        return 0

    def uuidType(self, s):
        return s.upper() == 'UUID'

    def bitType(self, type):
        return re.match(RE_BIT + '$', type, re.I)

    # quoting
    def quoteIdent(self, ident):
        raise Exception('not implemented in abstract class')

    def quoteLiteral(self, literal):
        return '\'' + literal + '\''

    # values
    def null(self):
        raise Exception('not implemented in abstract class')

    def boolValue(self, b):
        return 'TRUE' if b else 'FALSE'

    def dateValue(self, d):
        return d.strftime('%Y-%m-%d')

    def timestampValue(self, t, tz=None):
        ts = t.strftime('%Y-%m-%d %H:%M:%S')
        if tz:
            ts += ' ' + tz
        return ts

    def intervalValue(self, val, unit):
        return str(val) + ' ' + unit

    def blobValue(self, lo):
        raise Exception('not implemented in abstract class')

    def showValue(self, s):
        return s

    analyse = None


class CSV(Database):
    """CSV output."""

    def comment(self, s):
        pass

    def _comment(self, s):
        return "# " + s

    def echo(self, s):
        return self._comment(s)

    # transactions
    def begin(self):
        return None

    def commit(self):
        return None

    # operations
    def insertBegin(self, table):
        return self._comment("%s: %s" % \
                             (table.getName(), ','.join(a.getName() \
                                                        for a in filter(lambda x: x.gen, table.att_list))))

    def insertValue(self, table, value, isLast):
        return ','.join(db.quoteLiteral(i) for i in value)

    def insertEnd(self):
        return ''

    def setSequence(self, tab, att, number):
        return ''

    def dropTable(self, table):
        return ''

    def truncateTable(self, table):
        return ''

    # quoting
    def quoteIdent(self, ident):
        return '"%s"' % ident

    def quoteLiteral(self, literal):
        if isinstance(literal, (int, float)):
            return str(literal)
        else:
            return '"%s"' % literal

    # type
    def serialType(self, type):
        return is_ser.match(type)

    def intType(self, type):
        t = type.lower()
        return Database.intType(self, t) or \
               self.serialType(type) or is_int.match(t)

    # values
    def null(self):
        return 'NULL'


class PostgreSQL(Database):
    """PostgreSQL database."""

    def echo(self, s):
        return '\\echo ' + s

    def begin(self):
        return 'BEGIN;'

    def commit(self):
        return 'COMMIT;'

    def insertBegin(self, table):
        # build COPY options
        copyopts = []
        if opts.encoding:
            copyopts.append("ENCODING '{0}'".format(opts.encoding))
        if opts.freeze:
            copyopts.append("FREEZE ON")
        scopyopts = (" (" + ", ".join(copyopts) + ")") if len(copyopts) else ''
        # build copy statement
        return "COPY {0} ({1}) FROM STDIN{2};".format(
            table.getName(),
            ','.join(a.getName() \
                     for a in filter(lambda x: x.gen, table.att_list)),
            scopyopts)

    def quoteEsc(self, s, q, esc, n):
        if s == None:
            return n
        elif isinstance(s, list):  # ',' is for all types but Box...
            return '{' + ','.join(self.dQuoteEsc(i) for i in s) + '}'
        elif isinstance(s, bool):
            return self.boolValue(s)
        elif isinstance(s, numeric_types):
            return str(s)
        elif isinstance(s, bytes):
            return db.blobValue(s)
        elif isinstance(s, tuple):
            return '(' + ','.join(self.dQuoteEsc(e, '') for e in s) + ')'
        else:
            return q + ''.join(esc[c] if c in esc else c for c in str(s)) + q

    # double quotes
    DQESC = {'"': r'\"', '\\': r'\\'}

    def dQuoteEsc(self, s, null='NULL'):
        return self.quoteEsc(s, '"', PostgreSQL.DQESC, null)

    # simple quotes
    SQESC = {"'": r"''"}

    def sQuoteEsc(self, s, null='NULL'):
        return self.quoteEsc(s, "'", PostgreSQL.SQESC, null)

    # how to escape some characters for PostgreSQL's COPY:
    CPESC = {'\n': r'\n', '\t': r'\t', '\b': r'\b', '\r': r'\r', '\f': r'\f',
             '\v': r'\v', '\a': r'\007', '\0': r'\000', '\\': r'\\'}

    def copyEsc(self, s):
        return self.quoteEsc(s, '', PostgreSQL.CPESC, self.null())

    # overwrite value display function
    showValue = copyEsc

    def insertValue(self, table, value, isLast):
        # generate tab-separated possibly escaped values
        return '\t'.join(self.copyEsc(i) for i in value)

    def insertEnd(self):
        return '\\.'

    def setSequence(self, tab, att, number):
        name = "{0}_{1}_seq".format(tab.name, att.name)
        if tab.quoted or att.quoted:
            name = db.quoteIdent(name)
        return "ALTER SEQUENCE {0} RESTART WITH {1};".format(name, number)

    def dropTable(self, table):
        return "DROP TABLE IF EXISTS {0} CASCADE;".format(table.getName())

    def truncateTable(self, table):
        return "TRUNCATE TABLE {0} CASCADE;".format(table.getName())

    def quoteIdent(self, ident):
        # no escaping?
        return '"{0}"'.format(ident)

    def null(self):
        return r'\N'

    def serialType(self, type):
        return is_ser.match(type)

    def intType(self, type):
        t = type.lower()
        return Database.intType(self, t) or \
               self.serialType(type) or is_int.match(t)

    def eanType(self, type):
        # return the expected byte size
        t = type.upper()
        return 0 if not re.match('(' + RE_EAN + ')', t) else \
            12 if t == 'UPC' else \
                13 if t[-2:] == '13' else \
                    8 if t == 'ISSN' else \
                        10

    def blobValue(self, lo):
        return r'\\x' + ''.join("{0:02x}".format(o) for o in lo)

    def analyse(self, name):
        return "ANALYZE {0};".format(name)


class MySQL(Database):
    """MySQL database (experimental)."""

    def begin(self):
        return 'START TRANSACTION;'

    def commit(self):
        return 'COMMIT;'

    def insertBegin(self, table):
        return "INSERT INTO {0} ({1}) VALUES".format(table.getName(),
                                                     ','.join(a.getName() for a in table.att_list))

    def insertValue(self, table, value, isLast):
        qv = []
        for v in value:
            qv.append(self.boolValue(v) if type(v) is bool else
                      self.quoteLiteral(v) if type(v) is str else str(v))
        s = '  (' + ','.join(str(v) for v in qv) + ')'
        if not isLast:
            s += ','
        return s

    def insertEnd(self):
        return ';'

    def null(self):
        return 'NULL'

    def intType(self, type):
        t = type.lower()
        return Database.intType(self, t) or t == 'tinyint' or t == 'mediumint'
