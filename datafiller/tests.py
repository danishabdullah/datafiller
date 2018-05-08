from __future__ import print_function, unicode_literals

import sys

from datafiller.generators import WordGenerator
from datafiller.scripts.cli import self_run, opts

__author__ = "danishabdullah"

# test name, start with '!' if expected to fail
# test option, '!' if histogram, '-' if short
UNITS = [
    #
    # working tests
    #
    ("count",
     ["-count",
      "-count format=02X",
      "-count start=17 format=2o",
      "-count start=9 step=-1"]),
    ("const",
     ["-const", "-const=", "-const=hi", "-const='ho' null=0.5"]),
    ("bool",
     ["-bool", "-type=BOOL",
      "-bool rate=1.0", "-bool rate=0.0", "-bool rate=0.7", "!bool rate=0.85"]),
    ("int",
     ["-int", "-type=INTEGER",
      "-int sub=scale rate=0.4", "-int sub=power rate=0.4",
      "-int sub=serial", "-int sub=serial size=5", "-int sub=serand size=5",
      "-int sub=serial xor=17 step=7 size=20",
      "!int sub=power rate=0.8 size=3", "!int sub=scale rate=0.7 size=4",
      "-int sub=uniform size=8", "-type=SERIAL", "-type=tinyint",
      "-int null=0", "-int null=1", "-int null=0.5"]),
    ("float",  # avoid 'exp' (2.[67]) and 'vonmises' (3.[23])
     ["-float", "-type='DOUBLE PRECISION'",
      "-float=gauss alpha=0.8 beta=0.01",
      "-float=beta alpha=2.0", "-float=log alpha=5.0 beta=2.0"]),
    ("chars",
     ["-chars=abcde length=5 size=1", "-chars=abçde length=5 size=2",
      "-chars=0-9 length=5", "-chars=\dABC length=4 lenvar=3", "-chars=\w",
      r'-chars=\u211d\u20ac length=3 lenvar=2',
      "80pc:int sub=scale rate=0.8", "-chars='1.' length=10 cgen=80pc"]),
    ("string",
     ["-string", "-type=varchar(9)", "-type=CHAR(5) prefix=s",
      "-string size=5 prefix=i length=5 lenvar=1",
      "-string offset=10 size=10 lenmin=6 lenmax=7"]),
    ("word",
     ["-word=:", "-word=:un,2,3,4,5 sub=serial", "-word=:a,b,c,d,e,f size=2",
      "-word=/etc/dictionaries-common/words", ]),
    ("text",
     ["w1:string prefix=s size=10 length=5",
      "w2:word=:Gondor,Mordor,Moria,Rohan,Shire",
      "w3:int size=10 offset=0",
      "-text=w1 lenmin=1 lenmax=3 prefix=|",
      "-text=w2 length=2 lenvar=1 suffix=.",
      "-text=w3 lenmax=3 suffix=,",  # again...
      "-text=w3 lenmax=3 suffix=, separator=+",
      # hmmm... shoud I create a share just with 'size=4'?
      # does a subgen imply a share?
      "four: int size=4",
      "-text=w2 lenmax=5 share=four suffix=."]),
    ("pattern",
     ["-pattern", "-pattern=",
      "-pattern=[a-z]+", "-pattern=\w*", "-pattern=abc", "-pattern=(hi|you)",
      "-pattern=\d{2}[:lower:]{2}", "-pattern=(0|1)+[a-f]?",
      "-pattern=N=[:count:]", "-pattern='N=[:count start=9 step=-1:]'",
      "-pattern='N=[:count:]?'", "-pattern='\([:float:]\)'"]),
    ("blob",
     ["-blob", "-type=BLOB lenmin=3 lenmax=6",
      "-blob length=5 lenvar=2", "-blob length=6 lenvar=0",
      "-blob length=0 lenvar=0", "-blob length=3 size=3"]),
    ("date",
     ["-date end=1970-03-20 size=3650",
      "-date start=1970-03-20 size=36500",
      "-date start=2038-01-19 end=2038-01-19",
      "-date start=2038-01-19 end=2038-01-21",
      "-date start=1970-01-18 end=1970-03-20",
      "-date start=2038-01-19 prec=3 size=3"]),
    ("timestamp",
     ["-timestamp start='2013-12-26 17:31:05' size=7 prec=10",
      "-timestamp end='2013-12-26 17:32:01' prec=3600 size=3"]),
    ("interval",
     ["-interval", "-interval unit=d size=365", "-interval unit=y size=42"]),
    ("inet",
     ["-inet", "-inet=", "-type=INET",
      "-inet=10.2.14.0", "-inet=10.2.14.16/30", "-inet=10.2.14.0/22",
      "-inet=;10.2.14.0/31", "-inet=.10.2.15.0/31", "-inet=,10.2.16.0/31",
      "-inet=;10.2.17.12/32", "-inet=fe80::/120",
      "-inet=fe80::/64", "-inet=fe80::/16", "-inet=fe80::/24"]),
    ("mac",
     ["-mac", "-type=MACADDR", "-mac size=10"]),
    ("luhn",
     ["-luhn", "-luhn length=12", "-luhn length=8", "-luhn prefix=4800"]),
    ("ean",
     ["-ean", "-type=EAN13", "-type=ISBN13", "-type=ISSN13", "-type=ISMN13",
      "-type=UPC", "-type=ISBN", "-type=issn", "-type=ISMN size=10",
      "-type=ISSN prefix=1234567", "-type=ISMN prefix=M123",
      "-type=UPC prefix=1000000"]),
    ("uuid",
     ["-uuid", "-type=UUID", "-type=uuid"]),
    ("bit",
     ["-bit", "-bit type=BIT(3)", "-bit type=varbit(7)",
      "-bit length=7", "-bit lenmin=3 lenmax=5"]),
    ("array",
     ["ints: int size=9", "words: word=:one,two,three,four,five",
      "strings: string prefix=s size=9 length=3", "arrays: array=ints length=2",
      "-array=ints", "-array=words length=3", "-array=strings length=2",
      "-array=arrays length=3",
      "-type='INT[2]'", "-type='TEXT ARRAY'", "-type='INT ARRAY[2][3]'",
      "-type='INET[]'", "-type='FLOAT ARRAY [] [3]'"]),
    ("cat",
     ["f1: word=:un,deux,trois", "f2: int size=3",
      "-cat=f2,f1,f2"]),
    ("repeat",
     ["zero:chars='0' length=1", "-repeat=zero", "-repeat=zero extent=1-5",
      "-repeat=zero extent=1-5 sub=scale rate=0.85"]),
    ("isnull",
     ["-isnull", "-isnull null=1.0"]),
    ("tuple",
     ["digit: int size=10 offset=0", "none: isnull", "cst: const='hi' null=0.3",
      "stuff: pattern='[a-z]{2}'",
      "-tuple", "-tuple=", "-tuple=''", "-tuple null=0.3",  # empty tuples
      "-tuple=digit", "-tuple=digit null=0.8", "-tuple=digit,cst,none,stuff",
      "-tuple=digit,isnull,digit,cst null=0.3",
      "THREE: int size=3", "nb: int size=1000 share=THREE",
      r"city: pattern='[A-Z][a-z]+(\?|\!)' share=THREE",
      "-tuple=nb,city"]),
    ("reduce",
     ["f1: float=gauss beta=0.05", "f2: float", "i1: int size=2 offset=0",
      "-reduce=f1,f2", "-reduce=f1,i1", "-reduce=f1,i1 op=*",
      "-reduce=f1,f2 op=*", "-reduce=f1,f2 op=cat", "-reduce=f1,i1 op=max",
      "-reduce=f1,i1 op=min"]),
    ("value",
     ["i1: int size=10 offset=0", "f1: float", "f1v: value=f1",
      "f2: float=gauss alpha=0.0 beta=0.01",
      "-pattern='[:value=i1:]=[:value=i1:]'",
      "-pattern='[:use=f1v:],[:reduce=f1v,f2:]'"]),
    #
    # error tests
    #
    ("! count 1", ["count step=0"]),
    ("! bool 1", ["bool rate=2.0"]),
    ("! int 0", ["-int size=0"]),
    ("! int 1", ["int sub=scale rate=0.1 alpha=2.0"]),
    ("! int 2", ["int sub=foo"]),
    ("! int 3", ["int alpha=1.0"]),
    ("! int 4", ["int prefix=12 length=7 suffix=0"]),
    ("! int 5", ["int="]),
    ("! int 6", ["int=2"]),
    ("! int 7", ["int size=17.3"]),
    ("! int 8", ["int size=three"]),
    ("! int 9", ["int mult=2.0 size=20"]),
    ("! int A", ["int null=2.0"]),
    ("! float 1", ["float=exp beta=2.0"]),
    ("! chars 1", ["chars"]),  # empty set
    ("! chars 2", ["chars="]),  # idem
    ("! chars 3", ["chars=a-"]),
    ("! chars 4", ["chars=a-z\\"]),
    ("! string 1", ["string lenmin=-3 lenmax=1"]),
    ("! string 2", ["string lenmin=3 lenmax=2"]),
    ("! string 3", ["string length=10 lenmin=3"]),
    ("! word 1", ["-word="]),
    # ("! word 2", ["-word=:one,two,three size=5"]),
    ("! text 1", ["text"]),
    ("! text 2", ["text="]),
    ("! text 3", ["text=undefined"]),
    ("! text 4", ["useless: size=3", "text=useless"]),  # should it be int?
    ("! pattern 1", ["pattern=[:unknown:]"]),
    ("! date 1", ["date="]),
    ("! date 2", ["date=True"]),
    ("! date 3", ["date start=2038-01-19 end=2038-01-18"]),  # empty set
    ("! inet 1", ["inet=10"]),
    ("! inet 2", ["inet=10.0.0.0/33"]),
    ("! inet 3", ["inet=10.2.14.0/31"]),  # no available address
    ("! inet 4", ["inet=10.2.14.1/32"]),  # idem
    ("! luhn 1", ["luhn length=1"]),
    ("! luhn 2", ["luhn length=4 prefix=4800"]),
    ("! luhn 3", ["luhn prefix=000B"]),
    ("! ean 1", ["type=ISSN prefix=12345678"]),
    ("! isnull 1", ["isnull null=0.5"]),
    ("! reduce 1", ["f1: float", "f2: float", "reduce=f1,f2 op=sum"]),
    ("! * 1", ["int float"]),
    ("! * 2", ["type=flt"]),
    ("! * 3", ["int: chars=0-9"]),
]


def run_unit_tests(seed=None):
    fail = 0
    op = []
    if opts.self_test_hack:
        op.append("--self-test-hack")
    for v, lt in UNITS:
        ok = v[0] != '!'
        print('')
        print("** {0} **".format(v))
        sys.stdout.flush()
        status = self_run(validate=lt, seed=seed, op=op).wait()
        if ok != (status == 0):
            print("** FAILED **")
            fail += 1
    if fail:
        sys.stderr.write("unit tests failed: {0}\n".format(fail))
    sys.exit(fail)


#
# generate some files for file generator tests
#
some_tmp_files_to_unlink = []


def generate_some_tmp_files():
    # under self-test, generates a bunch of small temporary files
    # also do that for validation
    global some_tmp_files_to_unlink
    import tempfile as tf
    for w in WordGenerator.HOBBITS:
        f = tf.NamedTemporaryFile(delete=False)
        f.write(w.encode('utf-8') * int(3))
        f.write('\n'.encode('utf-8'))
        some_tmp_files_to_unlink.append(f.name)
        f.close()


def cleanup_some_tmp_files():
    import os
    global some_tmp_files_to_unlink
    for f in some_tmp_files_to_unlink:
        os.unlink(f)
    some_tmp_files_to_unlink = []
