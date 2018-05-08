from __future__ import print_function, unicode_literals

import argparse
import random
import re
import sys
from datetime import datetime

from datafiller.consts import RE_DOT, RE_IDENT, RE_ARRAY, backslash, df_junk, df_tab, df_att, df_dir, df_mac, comments, \
    new_object, alter_column, create_enum, alter_table, create_type, column, primary_key, unique, not_null, reference, \
    add_unique, unicity, add_fk, create_table
from datafiller.exceptions import StdoutExitError
from datafiller.generators import GENERATORS, IntGenerator, WordGenerator
from datafiller.generators.funcs import createGenerator, findGeneratorType, findGenerator, macroGenerator
from datafiller.globals import df_macro, tuple_count, re_quoted, all_tables, all_enums, schema, tables
from datafiller.models import Model, Attribute, PostgreSQL, MySQL, CSV, Table
from datafiller.pod import POD
from datafiller.tests import cleanup_some_tmp_files, generate_some_tmp_files, run_unit_tests
from datafiller.utils import getParams, u, u8, debug, StringIO

__author__ = "danishabdullah"

VERSION = '2.0.1-dev'
Id = '$Id: datafiller.py.py 832 2015-11-01 21:55:41Z fabien $'

# extract revision informations from svn revision identifier

revision, revdate, revyear = \
    re.search(r' (\d+) ((\d{4})-\d\d-\d\d) ', Id).group(1, 2, 3)

version = "{0} (r{1} on {2})".format(VERSION, revision, revdate)

with open("./datafiller/examples/pgbench.sql", 'r', encoding='utf-8') as fyle:
    PGBENCH = fyle.read

# embedded PostgreSQL validation
with open("./datafiller/examples/internal.schema.sql", 'r', encoding='utf-8') as fyle:
    INTERNAL = fyle.read()

# some checks about the internal schema
# other checks are implicitely performed for contraints.
# some of these test occasionnaly fail with a low probability, eg s5
with open("./datafiller/examples/internal.schema.check.sql", 'r', encoding='utf-8') as fyle:
    INTERNAL_CHECK = fyle.read()

with open("./datafiller/examples/comics.sql", 'r', encoding='utf-8') as fyle:
    COMICS = fyle.read()

with open("./datafiller/examples/library.sql", 'r', encoding='utf-8') as fyle:
    LIBRARY = fyle.read()

# LIBRARY example without directives
LIBRARY_NODIR = re.sub(r'-- df.*', '', LIBRARY)

# option management
# --size=1000
# --target=postgresql|mysql
# --help is automatic

# version="version {0}".format(version),
opts = argparse.ArgumentParser(
    description='Fill database tables with random data.')
opts.add_argument('-s', '--size', type=int, default=None,
                  help='scale to size')
opts.add_argument('-t', '--target', default='postgresql',
                  help='generate for this engine')
opts.add_argument('-e', '--encoding', type=str, default=None,
                  help='set input & output encoding')
opts.add_argument('-f', '--filter', action='store_true', default=False,
                  help='also include input in output')
opts.add_argument('--no-filter', action='store_true', default=False,
                  help='do turn off filtering, whatever!')
opts.add_argument('--freeze', action='store_true', default=True,
                  help='use PostgreSQL COPY FREEZE')
opts.add_argument('--no-freeze', dest='freeze', action='store_false',
                  help='do not use PostgreSQL COPY FREEZE')
opts.add_argument('-T', '--transaction', action='store_true',
                  help='wrap output in a transaction')
opts.add_argument('-S', '--seed', default=None,
                  help='random generator seed')
opts.add_argument('-O', '--offset', type=int, default=None,
                  help='set global offset for integer primary keys')
opts.add_argument('--truncate', action='store_true', default=False,
                  help='truncate table contents before loading')
opts.add_argument('--drop', action='store_true', default=False,
                  help='drop tables before reloading')
opts.add_argument('-D', '--debug', action='count',
                  help='set debug mode')
opts.add_argument('-m', '--man', action='store_const', const=2,
                  help='show man page')
opts.add_argument('-n', '--null', type=float, default=None,
                  help='probability of generating a NULL value')
opts.add_argument('--pod', type=str, default='pod2usage -verbose 3',
                  help='override pod2usage command')
opts.add_argument('-q', '--quiet', action='store_true', default=False,
                  help='less verbose output')
opts.add_argument('--self-test', action='store_true', default=False,
                  help='run automatic self test')
opts.add_argument('--self-test-hack', action='store_true', default=False,
                  help='override system newline for self-test')
opts.add_argument('--self-test-python', type=str, default=None,
                  help="self-test must run with this python")
opts.add_argument('-X', '--test', action='append',
                  help='show generator output for directives')
opts.add_argument('--tries', type=int, default=10,
                  help='how hard to try to satisfy unique constraints')
opts.add_argument('--type', action='append', default=[],
                  help='add custom type')
opts.add_argument('--validate', type=str, default=None,
                  help='shortcut for script validation')
opts.add_argument('-V', action='store_true', default=False,
                  help='show short version on stdout and exit')
opts.add_argument('-v', '--version', action='version',
                  version="version {0}".format(version),
                  help='show version information')
opts.add_argument('file', nargs='*',
                  help='process files, or stdin if empty')
opts = opts.parse_args()

if opts.V:
    print(VERSION)
    sys.exit(0)

# set database target
db = None
if opts.target == 'postgresql':
    db = PostgreSQL()
elif opts.target == 'mysql':
    db = MySQL()
elif opts.target == 'csv':
    db = CSV()
else:
    raise Exception("unexpected target database {0}".format(opts.target))

# fix some options for consistency
if opts.validate:
    opts.transaction = True
    opts.filter = True

if opts.self_test_hack:
    # ensure some settings under self-test for determinism
    if opts.seed:
        random.seed(opts.seed)
    opts.quiet = True
    opts.freeze = False
    # consistent \n and unicode, see print overriding below
    assert not opts.encoding, "no --encoding under self-test"
    opts.encoding = 'utf-8'
    import os

    os.linesep = '\n'

# file generator test
if opts.validate == 'internal':
    generate_some_tmp_files()

if not opts.encoding:
    # note: this is ignored by python3 on input(?)
    opts.encoding = sys.getfilesystemencoding() if opts.file else \
        sys.stdin.encoding

if opts.encoding:
    # sys.stdout.encoding = opts.encoding
    import os

    if sys.version_info[0] == 3:
        def __encoded_print(s, end=os.linesep):
            # tell me there is something better than this...
            sys.stdout.buffer.write(s.encode(opts.encoding))
            sys.stdout.buffer.write(end.encode(opts.encoding))
            sys.stdout.flush()  # for python 3.4?


        print = __encoded_print
    else:  # python 2
        # simpler, although not sure why it works
        print = lambda s, end=os.linesep: \
            sys.stdout.write(s.encode(opts.encoding) + end)

if opts.test:
    AssertionError = StdoutExitError
    ntest = 0
    # process decoded tests
    for t in map(u, opts.test):
        ntest += 1
        print(u8("-- test {0}: {1}").format(ntest, t))
        # macro definition
        m = re.match(r'\s*([\w\.]+)\s*:\s*(.*)', t)
        if m:
            name = m.group(1)
            assert not name in GENERATORS, \
                "do not use generator name '{0}' as a macro name!".format(name)
            df_macro[name] = getParams(m.group(2))
            continue
        # else some directives
        d = re.match(r'\s*([!-]?)\s*(.*)', t)
        h, params = d.group(1), getParams(d.group(2))
        g = findGenerator('test', params)
        if not g and 'type' in params:
            g = findGeneratorType(params['type'])
            assert g, "unknown type {0} ({1})".format(params['type'], t)
        assert g, "must specify a generator: {0}".format(t)
        Model.checkPARAMS('--test', params, Attribute.PARAMS)
        gen = createGenerator(None, g, params)
        if isinstance(gen, IntGenerator) and gen.size == None:
            gen.setSize(opts.size if opts.size else 10)
        assert not gen.params, "unused parameter: {0}".format(gen.params)
        if h == '!':  # show histogram
            n = opts.size if opts.size else 10000
            vals = {}
            for i in range(n):
                tuple_count += 1
                gen.mapGen(lambda s: s.shareSeed())
                v = gen.getData()
                vals[v] = 0 if not v in vals else vals[v] + 1
            print("histogram on {0} draws".format(n))
            for v in sorted(vals):
                print(u8("{0}: {1:6.3f} %").format(v, 100.0 * vals[v] / n))
        else:  # show values
            for i in range(opts.size if opts.size else 10):
                tuple_count += 1
                gen.mapGen(lambda s: s.shareSeed())
                d = db.showValue(gen.getData())
                if h == '-':  # short
                    print(str(d), end=' ')  # '\t' ?
                else:
                    print(u8("{0}: {1}").format(i, d))
            if h == '-':
                print('')
    # just in case
    cleanup_some_tmp_files()
    sys.exit(0)

# option consistency
if opts.drop or opts.test:
    opts.filter = True

if opts.no_filter:  # may be forced back for some tests
    opts.filter = False

assert not (opts.filter and opts.truncate), \
    "option truncate does not make sense with option filter"

if opts.man:
    # Let us use Perl's POD from Python:-)
    import os, tempfile

    pod = tempfile.NamedTemporaryFile(prefix='datafiller_', mode='w')
    name = sys.argv[0].split('/')[-1]
    pod.write(POD.format(comics=COMICS, pgbench=PGBENCH, library=LIBRARY_NODIR,
                         name=name, DOT=RE_DOT, NGENS=len(GENERATORS),
                         GLIST=' '.join("B<{0}>".format(g) for g in sorted(GENERATORS)),
                         version=version, year=revyear))
    pod.flush()
    os.system(opts.pod + ' ' + pod.name)
    pod.close()
    sys.exit(0)


# auto run a test with some options
def self_run(validate=None, seed=None, pipe=False, op=[]):
    import subprocess
    # command to run
    cmd = [sys.argv[0]] + op
    if isinstance(validate, list):
        cmd += map(lambda t: '--test=' + t, validate)
    else:  # must be str
        cmd += ['--validate=' + validate]
    if opts.self_test_python:
        cmd += ['--self-test-python=' + opts.self_test_python]
    if seed:
        cmd.append('--seed=' + seed)
    if opts.self_test_python:
        cmd.insert(0, opts.self_test_python)
    if opts.debug: debug(1, "self-test cmd: {0}".format(cmd))
    return subprocess.Popen(cmd, stdout=subprocess.PIPE if pipe else None)


# the self-test allows to test the script on hosts without PostgreSQL
def self_test(validate=None, seed='Calvin', D=None):
    import hashlib, time
    start = time.time()
    h = hashlib.sha256()
    p = self_run(validate, seed=seed, pipe=True, op=['--self-test-hack'])
    for line in p.stdout:
        h.update(line)
    okay = p.wait() == 0
    d = h.hexdigest()[0:16]
    end = time.time()
    print("self-test {0} seed={1} hash={2} seconds={3:.2f}: {4}".
          format(validate, seed, d, end - start,
                 'PASS' if okay and d == D else 'FAIL'))
    return okay and d == D


if opts.self_test:
    # self test results for python 2 & 3
    TESTS = [
        # [test, seed, [ py2h, py3h ]]
        ['unit', 'Wormwood!', ['73d9b211839c90d6', '05183e0be6ac649e']],
        ['internal', 'Moe!!', ['8b56d03d6220dca3', 'aa7ccdc56a147cc4']],
        ['library', 'Calvin', ['d778fe6adc57eea7', 'adc029f5d9a3a0fb']],
        ['comics', 'Hobbes!', ['fff09e9ac33a4e2a', '49edd6998e04494e']],
        ['pgbench', 'Susie!', ['891cd4a00d89d501', '55d66893247d3461']]]
    fail = 0
    for test, seed, hash in TESTS:
        if not opts.validate or opts.validate == test:
            fail += not self_test(test, seed, hash[sys.version_info[0] - 2])
    sys.exit(fail)

# reset arguments for fileinput
sys.argv[1:] = opts.file


def addType(t):
    global re_types, column_type
    if re_types:
        re_types += '|' + t
    else:
        re_types = t
    column_type = re.compile(r'^\s*,?\s*(ADD\s+COLUMN\s+)?({0})\s+({1}{2})'. \
                             format(RE_IDENT, re_types, RE_ARRAY), re.I)


for t in opts.type:
    addType(t)

#
# INPUT SCHEMA
#
if opts.validate:
    if opts.validate == 'unit':
        run_unit_tests(seed=opts.seed)
    elif opts.validate == 'internal':
        lines = StringIO(INTERNAL).readlines()
    elif opts.validate == 'library':
        lines = StringIO(LIBRARY).readlines()
        if opts.self_test_hack:
            lines.append("--df T=Borrow A=borrowed:end='2038-01-19 03:14:07'\n")
    elif opts.validate == 'comics':
        lines = StringIO(COMICS).readlines()
    elif opts.validate == 'pgbench':
        lines = StringIO(PGBENCH).readlines()
    else:
        raise Exception("unexpected validation {0}".format(opts.validate))
    lines = [u8(l) for l in lines]
else:
    import fileinput  # despite the name this is really a filter...

    fi = fileinput.input(openhook=fileinput.hook_encoded(opts.encoding))
    lines = [l for l in fi]


#
# SCHEMA PARSER
#

def sql_string_list(line):
    """Return an unquoted list of sql strings."""
    sl = []
    quoted = re_quoted.match(line)
    while quoted:
        sl.append(quoted.group(1))
        line = quoted.group(3)
        quoted = re_quoted.match(line)
    return sl


for line in lines:
    # if opts.debug: sys.stderr.write(u8("line={0}").format(line))
    # skip \commands
    if backslash.match(line):
        continue
    # skip commented out directives
    if df_junk.match(line):
        continue
    # get datafiller.py stuff
    # directives with explicit table & attribute
    d = df_tab.match(line)
    if d:
        if opts.debug: debug(2, "explicit TA directive")
        current_table = all_tables[d.group(2).lower()]
        current_attribute = None
    d = df_att.match(line)
    if d:
        if opts.debug: debug(2, "set attribute")
        assert current_table != None
        current_attribute = current_table.getAttribute(d.group(2))
    # extract directive
    d = df_dir.match(line)
    if d:
        if opts.debug: debug(2, "is a directive")
        dfstuff = d.group(1)
    # get datafiller.py macro definition
    d = df_mac.match(line)
    if d:
        if opts.debug: debug(2, "is a macro")
        mname = d.group(1)
        if mname in df_macro:
            sys.stderr.write("warning: macro {0} is redefined\n".
                             format(mname))
        assert mname not in GENERATORS, \
            "do not use generator name '{0}' as a macro name!".format(mname)
        df_macro[mname] = getParams(d.group(2))
        # reset current params so that it is not stored in an object
        dfstuff = None
    # cleanup comments
    c = comments.match(line)
    if c:
        if opts.debug: debug(2, "cleanup comment")
        line = c.group(1)
    # reset current object
    # argh, beware of ALTER TABLE ... ALTER COLUMN!
    if new_object.match(line) and not alter_column.match(line):
        current_table = None
        current_attribute = None
        current_enum = None
        att_number = 0
    #
    # CREATE TYPE ... AS ENUM
    #
    is_ce = create_enum.match(line)
    if is_ce:
        current_enum = is_ce.group(1)  # lower()?
        if opts.debug:
            debug(2, "create enum " + current_enum)
        if re:
            re += '|'
        # ??? should escape special characters such as "."
        re += current_enum
        all_enums[current_enum] = sql_string_list(line)
        column_enum = re.compile(r'\s*,?\s*(ADD\s+COLUMN\s+)?({0})\s+({1})'. \
                                 format(RE_IDENT, re), re.I)
        continue
    # follow up...
    if current_enum:
        all_enums[current_enum].extend(sql_string_list(line))
        continue
    #
    # CREATE TYPE ... AS
    #
    is_ty = create_type.match(line)
    if is_ty:
        addType(is_ty.group(1))
        continue
    #
    # ALTER/CREATE TABLE
    #
    is_at = alter_table.match(line)
    if is_at:
        name = is_at.group(2)
        if opts.debug: debug(2, "alter table " + name)
        current_table = all_tables[name.lower()]
        att_number = len(current_table.atts)
    is_ct = create_table.match(line)
    if is_ct:
        name = is_ct.group(1)
        if opts.debug: debug(2, "create table " + name)
        current_table = Table(name)
        tables.append(current_table)
        all_tables[name.lower()] = current_table
    elif current_table != None:
        #
        # COLUMN
        #
        is_enum = False
        # try standard types
        c = column.match(line)
        # try enums
        if not c and column_enum:
            c = column_enum.match(line)
            is_enum = bool(c)
        # try other types
        if not c and column_type:
            c = column_type.match(line)
        if c:
            if opts.debug: debug(2, "column " + c.group(2))
            att_number += 1
            current_attribute = Attribute(c.group(2), att_number, c.group(3))
            current_attribute.is_enum = is_enum
            if primary_key.match(line):
                if opts.debug: debug(2, "primary key")
                current_attribute.isPK = True
            if unique.match(line):
                if opts.debug: debug(2, "unique")
                current_attribute.unique = True
            if not_null.match(line):
                if opts.debug: debug(2, "not null")
                current_attribute.not_null = True
            current_table.addAttribute(current_attribute)
            r = reference.match(line)
            if r:
                if opts.debug: debug(2, "reference")
                target = r.group(1)
                current_attribute.FK = all_tables[target.lower()]
                current_attribute.FKatt = r.group(5) if r.group(4) else None
        # ADD UNIQUE
        q = add_unique.match(line)
        if q:
            if opts.debug: debug(2, "add unique")
            current_table.addUnique(re.split(r'[\s,]+', q.group(3)), q.group(2))
        else:
            # UNIQUE()
            q = unicity.match(line)
            if q:
                if opts.debug: debug(2, "unicity")
                current_table.addUnique(re.split(r'[\s,]+', q.group(2)), \
                                        q.group(1))
        r = add_fk.match(line)
        if r:
            if opts.debug: debug(2, "add foreign key")
            src, target = r.group(2, 3)
            current_attribute = current_table.getAttribute(src)
            current_attribute.FK = all_tables[target.lower()]
            current_attribute.FKatt = r.group(7) if r.group(6) else None
        c = alter_column.match(line)
        if c:
            if opts.debug: debug(2, "alter column " + c.group(1))
            current_attribute = current_table.getAttribute(c.group(1))
            # ... SET NOT NULL
            if not_null.match(line):
                if opts.debug: debug(2, "set not null")
                current_attribute.not_null = True
    # attribute df stuff to current object: schema, table or attribute
    # this come last if the dfstuff is on the same line as its object
    if dfstuff != None:
        if current_attribute != None:
            current_attribute.setParams(dfstuff)
        elif current_table != None:
            current_table.setParams(dfstuff)
        else:
            schema.setParams(dfstuff)
        dfstuff = None

#
# SET DEFAULT VALUES for some options, possibly from directives
#
if opts.size == None:
    opts.size = schema.params.get('size', 100)

if not opts.offset:
    opts.offset = schema.params.get('offset')

if not opts.null:
    opts.null = schema.params.get('null', 0.01)

if not opts.seed:
    opts.seed = schema.params.get('seed')

# set seed, default uses os random or time
random.seed(opts.seed)

#
# START OUTPUT
#
if not opts.self_test_hack and opts.target != 'csv':
    print('')
    print("-- This file is generated by the DataFiller free software.")
    print("-- This software comes without any warranty whatsoever.")
    print("-- Use at your own risk. Beware, this script may destroy your data!")
    print("-- License is GPLv3, see http://www.gnu.org/copyleft/gpl.html")
    print("-- Get latest version from http://www.coelho.net/datafiller.py.html")
    print('')
    print("-- Data generated by: {0}".format(sys.argv[0]))
    print("-- Version {0}".format(version))
    print("-- For {0} on {1} (UTC)".
          format(opts.target, datetime.utcnow().isoformat()))

if opts.test and opts.filter and opts.target == 'postgresql':
    print('')
    print("\\set ON_ERROR_STOP")

if opts.quiet and opts.target == 'postgresql':
    print('')
    print("SET client_min_messages = 'warning';")

if opts.transaction:
    print('')
    print(db.begin())

#
# DROP
#
if opts.drop:
    print('')
    print('-- drop tables')
    for t in reversed(tables):
        print(db.dropTable(t))

#
# SHOW INPUT
#
if opts.filter:
    print('')
    print('-- INPUT FILE BEGIN')
    for line in lines:
        print(line, end='')
    print('-- INPUT FILE END')

#
# TRUNCATE
#
if opts.truncate:
    print('')
    print('-- truncate tables')
    for t in filter(lambda t: not 'nogen' in t.params, reversed(tables)):
        print(db.truncateTable(t))

#
# SET TABLE AND ATTRIBUTE SIZES
#
# first table sizes
for t in tables:
    t.skip = t.params.pop('skip') if 'skip' in t.params else 0.0
    assert t.skip >= 0.0 and t.skip <= 1.0
    if t.size == None:
        t.size = t.params.pop('size') if 'size' in t.params else \
            int(t.params.pop('mult') * opts.size) if 'mult' in t.params else \
                opts.size

# *then* set att sizes and possible offset
for t in tables:
    for a in t.att_list:
        if a.FK != None:
            a.size = a.FK.size
            if a.FK.skip:
                raise Exception("reference on table {0} with skipped tuples".
                                format(a.FK.name))
            key = a.FK.atts[a.FKatt] if a.FKatt else a.FK.getPK()
            assert key.isUnique(), \
                "foreign key {0}.{1} target {2} must be unique". \
                    format(a.table.name, a.name, key.name)
            # override default prefix
            # ??? only for text types!?
            if db.textType(a.type):
                assert not 'prefix' in a.params, \
                    "no prefix on FK {0}.{1}".format(a.table.name, a.name)
                a.params['prefix'] = key.params.get('prefix', key.name)
            # transfer all other directives
            for d, v in key.params.items():
                if not d in a.params:
                    a.params[d] = v
        elif 'size' in a.params:
            # the directive is not removed now, it should be done later?
            a.size = a.params['size']
        elif a.size == None:
            a.size = int(t.size * a.params.pop('mult', 1.0))

#
# CREATE DATA GENERATORS per attribute
#
for t in filter(lambda t: not 'nogen' in t.params, tables):
    for a in t.att_list:
        # do not generate
        if 'nogen' in a.params:
            del a.params['nogen']
            a.gen = None
            assert not a.params, \
                "unused '{0}' parameters: {1}".format(a.name, a.params)
            continue
        # generators triggered by their directives
        gname = a.getGenerator()
        if gname:
            a.gen = GENERATORS[gname](a)
            a.gen.params.pop(gname, None)
        # type-based default generators
        elif a.is_enum:
            a.gen = WordGenerator(a, None, words=all_enums[a.type])
        else:
            gname = findGeneratorType(a.type)
            if gname:
                a.gen = GENERATORS[gname](a)
            elif a.type in df_macro:
                # try a macro homonymous to the type name
                a.gen = macroGenerator(a.type, a)
            else:
                a.gen = None
        # checks!
        assert a.gen, \
            "generator for {0}.{1} type {2}". \
                format(t.name, a.name, a.type)
        assert not a.gen.params, \
            "unused {0}.{1} directives: {2}". \
                format(t.name, a.name, a.gen.params)

# print tables
if opts.debug:
    sys.stderr.write(str(tables) + "\n")

#
# CALL GENERATORS on each table
#
for t in tables:
    db.comment('')
    if 'nogen' in t.params or t.size == 0:
        t.params.pop('nogen', None)
        assert not t.params, \
            "unused {0} parameters: {1}".format(t.name, t.params)
        db.comment("skip table {0}".format(t.name))
    else:
        size = "{0:d}*{1:g}".format(t.size, 1.0 - t.skip) if t.skip else \
            str(t.size)
        db.comment("fill table {0} ({1})".format(t.name, size))
        if not opts.quiet:
            print(db.echo("# filling table {0} ({1})".format(t.name, size)))
        print(db.insertBegin(t))
        for i in range(t.size):
            tup = t.getData()
            # although the tuple is generated, it may yet not be inserted
            if not t.skip or not random.random() < t.skip or i == t.size - 1:
                print(db.insertValue(t, tup, i == t.size - 1))
        print(db.insertEnd())

#
# CLEANUP
#
cleanup_some_tmp_files()

#
# RESTART SEQUENCES
#
db.comment('')
db.comment('restart sequences')
for t in filter(lambda t: not 'nogen' in t.params, tables):
    for a in filter(lambda a: a.isSerial() and a.gen, t.att_list):
        print(db.setSequence(t, a, a.gen.offset + a.gen.size))

#
# DONE
#

if opts.transaction:
    db.comment('')
    print(db.commit())

#
# ANALYZE, if needed
#

if db.analyse:
    db.comment('')
    db.comment('analyze modified tables')
    for t in filter(lambda t: not 'nogen' in t.params, tables):
        print(db.analyse(t.getName()))

#
# validation
#
if opts.validate == 'internal':
    print(INTERNAL_CHECK);
