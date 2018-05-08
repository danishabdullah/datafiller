
-- df: size=2000 null=0.0

-- define some macros:
-- df name: chars='a-z' length=6 lenvar=2
-- df dot: word=':.'
-- df domain: word=':@somewhere.org'
-- df 09: int offset=0 size=10
-- df AZ: chars='A-Z' length=2 lenvar=0
-- df ELEVEN: int size=11

CREATE SCHEMA df;

CREATE TYPE df.color AS ENUM ('red','blue','green');

-- an address type and its generator
CREATE TYPE df.addr AS (nb INTEGER, road TEXT, code VARCHAR(6), city TEXT);

-- df addr_nb: int size=1000 offset=1 sub=scale rate=0.01 null=0.0
-- df addr_rd: pattern='[A-Z][a-z]{2,8} ([A-Z][a-z]{3,7} )?(st|av|rd)' null=0.0
-- df CITY: int size=100 sub=scale rate=0.5
-- df addr_po: pattern='[0-9]{5}' null=0.0 share=CITY
-- df addr_ct: pattern='[A-Z][a-z]+' null=0.0 share=CITY
-- df addr_tuple: tuple=addr_nb,addr_rd,addr_po,addr_ct

CREATE TABLE df.Stuff( -- df: mult=1.0
  id SERIAL PRIMARY KEY
  -- *** INTEGER ***
, i0 INTEGER CHECK(i0 IS NULL) -- df: null=1.0 size=1
, i1 INTEGER CHECK(i1 IS NOT NULL AND i1=1) -- df: null=0.0 size=1
, i2 INTEGER NOT NULL CHECK(i2 BETWEEN 1 AND 6) --df: size=5
, i3 INTEGER UNIQUE -- df: offset=1000000
, i4 INTEGER CHECK(i2 BETWEEN 1 AND 6) -- df: sub=power rate=0.7 size=5
, i5 INTEGER CHECK(i2 BETWEEN 1 AND 6) -- df: sub=scale rate=0.7 size=5
, i6 INT8  -- df: size=1800000000000000000 offset=-900000000000000000
, i7 INT4  -- df: size=4000000000 offset=-2000000000
, i8 INT2  -- df: size=65000 offset=-32500
  -- *** BOOLEAN ***
, b0 BOOLEAN NOT NULL
, b1 BOOLEAN -- df: null=0.5
, b2 BOOLEAN NOT NULL -- df: rate=0.7
  -- *** FLOAT ***
, f0 REAL NOT NULL CHECK (f0 >= 0.0 AND f0 < 1.0)
, f1 DOUBLE PRECISION -- df: float=gauss alpha=5.0 beta=2.0
, f2 DOUBLE PRECISION CHECK(f2 >= -10.0 AND f2 < 10.0)
    -- df: float=uniform alpha=-10.0 beta=10.0
, f3 DOUBLE PRECISION -- df: float=beta alpha=1.0 beta=2.0
-- 'exp' output changes between 2.6 & 2.7
-- , f4 DOUBLE PRECISION -- df: float=exp alpha=0.1
, f5 DOUBLE PRECISION -- df: float=gamma alpha=1.0 beta=2.0
, f6 DOUBLE PRECISION -- df: float=log alpha=1.0 beta=2.0
, f7 DOUBLE PRECISION -- df: float=norm alpha=20.0 beta=0.5
, f8 DOUBLE PRECISION -- df: float=pareto alpha=1.0
-- 'vonmises' output changes between 3.2 and 3.3
-- , f9 DOUBLE PRECISION -- df: float=vonmises alpha=1.0 beta=2.0
, fa DOUBLE PRECISION -- df: float=weibull alpha=1.0 beta=2.0
, fb NUMERIC(2,1) CHECK(fb BETWEEN 0.0 AND 9.9)
    -- df: float=uniform alpha=0.0 beta=9.9
, fc DECIMAL(5,2) CHECK(fc BETWEEN 100.00 AND 999.99)
    -- df: float=uniform alpha=100.0 beta=999.99
  -- *** DATE ***
, d0 DATE NOT NULL CHECK(d0 BETWEEN '2038-01-19' AND '2038-01-20')
     -- df: size=2 start='2038-01-19'
, d1 DATE NOT NULL CHECK(d1 = DATE '2038-01-19')
     -- df: start=2038-01-19 end=2038-01-19
, d2 DATE NOT NULL
       CHECK(d2 = DATE '2038-01-19' OR d2 = DATE '2038-01-20')
       -- df: start=2038-01-19 size=2
, d3 DATE NOT NULL
       CHECK(d3 = DATE '2038-01-18' OR d3 = DATE '2038-01-19')
       -- df: end=2038-01-19 size=2
, d4 DATE NOT NULL
       CHECK(d4 = DATE '2013-06-01' OR d4 = DATE '2013-06-08')
       -- df: start=2013-06-01 end=2013-06-08 prec=7
, d5 DATE NOT NULL
       CHECK(d5 = DATE '2013-06-01' OR d5 = DATE '2013-06-08')
       -- df: start=2013-06-01 end=2013-06-14 prec=7
  -- *** TIMESTAMP ***
, t0 TIMESTAMP NOT NULL
          CHECK(t0 = TIMESTAMP '2013-06-01 00:00:05' OR
                t0 = TIMESTAMP '2013-06-01 00:01:05')
          -- df: start='2013-06-01 00:00:05' end='2013-06-01 00:01:05'
, t1 TIMESTAMP NOT NULL
          CHECK(t1 = TIMESTAMP '2013-06-01 00:02:00' OR
                t1 = TIMESTAMP '2013-06-01 00:02:05')
          -- df: start='2013-06-01 00:02:00' end='2013-06-01 00:02:05' prec=5
, t2 TIMESTAMP NOT NULL
          CHECK(t2 >= TIMESTAMP '2013-06-01 01:00:00' AND
                t2 <= TIMESTAMP '2013-06-01 02:00:00')
          -- df: start='2013-06-01 01:00:00' size=30 prec=120
, t3 TIMESTAMP WITH TIME ZONE NOT NULL
          CHECK(t3 = TIMESTAMP '2013-06-22 09:17:54 CEST')
          -- df: start='2013-06-22 07:17:54' size=1 tz='UTC'
  -- *** INTERVAL ***
, v0 INTERVAL NOT NULL CHECK(v0 BETWEEN '1 s' AND '1 m')
     -- df: size=59 offset=1 unit='s'
, v1 INTERVAL NOT NULL CHECK(v1 BETWEEN '1 m' AND '1 h')
     -- df: size=59 offset=1 unit='m'
, v2 INTERVAL NOT NULL CHECK(v2 BETWEEN '1 h' AND '1 d')
     -- df: size=23 offset=1 unit='h'
, v3 INTERVAL NOT NULL CHECK(v3 BETWEEN '1 d' AND '1 mon')
     -- df: size=29 offset=1 unit='d'
, v4 INTERVAL NOT NULL CHECK(v4 BETWEEN '1 mon' AND '1 y')
     -- df: size=11 offset=1 unit='mon'
, v5 INTERVAL NOT NULL -- df: size=100 offset=0 unit='y'
, v6 INTERVAL NOT NULL -- df: size=1000000 offset=0 unit='s'
  -- *** TEXT ***
, s0 CHAR(12) UNIQUE NOT NULL
, s1 VARCHAR(15) UNIQUE NOT NULL
, s2 TEXT NOT NULL -- df: length=23 lenvar=1 size=20 seed=s2
, s3 TEXT NOT NULL CHECK(s3 LIKE 'stuff%') -- df: prefix='stuff'
, s4 TEXT NOT NULL CHECK(s4 ~ '^[a-f]{9,11}$')
    -- df: chars='abcdef' size=20 length=10 lenvar=1
, s5 TEXT NOT NULL CHECK(s5 ~ '^[ab]{30}$')
    -- df skewed: int sub=scale rate=0.7
    -- df: chars='ab' size=50 length=30 lenvar=0 cgen=skewed
, s6 TEXT NOT NULL -- df: word=:calvin,hobbes,susie
, s7 TEXT NOT NULL -- df: word=:one,two,three,four,five,six,seven size=3 mangle
, s8 TEXT NOT NULL CHECK(s8 ~ '^((un|deux) ){3}(un|deux)$')
    -- df undeux: word=:un,deux
    -- df: text=undeux length=4 lenvar=0
, s9 VARCHAR(10) NOT NULL CHECK(LENGTH(s9) BETWEEN 8 AND 10)
  -- df: length=9 lenvar=1
, sa VARCHAR(8) NOT NULL CHECK(LENGTH(sa) BETWEEN 6 AND 8) -- df: lenvar=1
, sb TEXT NOT NULL CHECK(sb ~ '^10\.\d+\.\d+\.\d+$')
  -- df: inet='10.0.0.0/8'
, sc TEXT NOT NULL CHECK(sc ~ '^([0-9A-F][0-9A-F]:){5}[0-9A-F][0-9A-F]$')
  -- df: mac
, sd TEXT NOT NULL CHECK(sd ~ '^[ \\007\\n\\f\\v\\t\\r\\\\]{10}')
  -- df: chars=' \\a\\n\\t\\f\\r\\v\\\\' length=10 lenvar=0
  -- user defined *** ENUM ***
, e0 df.color NOT NULL
  -- *** EAN *** and other numbers
, e1 EAN13 NOT NULL
, e2 ISBN NOT NULL
, e3 ISMN NOT NULL
, e4 ISSN NOT NULL
, e5 UPC NOT NULL
, e6 ISBN13 NOT NULL
, e7 ISMN13 NOT NULL
, e8 ISSN13 NOT NULL
, e9 CHAR(16) NOT NULL CHECK(e9 ~ '^[0-9]{16}$') -- df: luhn
, ea CHAR(12) NOT NULL CHECK(ea ~ '^1234[0-9]{8}$')
    -- df: luhn prefix=1234 length=12
  -- *** BLOB ***
, l0 BYTEA NOT NULL
, l1 BYTEA NOT NULL CHECK(LENGTH(l1) = 3) -- df: length=3 lenvar=0
, l2 BYTEA NOT NULL CHECK(LENGTH(l2) BETWEEN 0 AND 6) -- df: length=3 lenvar=3
  -- *** INET ***
, n0 INET NOT NULL CHECK(n0 << INET '10.2.14.0/24') -- df: inet=10.2.14.0/24
, n1 CIDR NOT NULL CHECK(n1 << INET '192.168.0.0/16')
    -- df: inet=192.168.0.0/16
, n2 MACADDR NOT NULL
, n3 MACADDR NOT NULL -- df: size=17
, n4 INET NOT NULL CHECK(n4 = INET '1.2.3.5' OR n4 = INET '1.2.3.6')
    -- df: inet='1.2.3.4/30'
, n5 INET NOT NULL CHECK(n5 = INET '1.2.3.0' OR n5 = INET '1.2.3.1')
    -- df: inet=';1.2.3.0/31'
, n6 INET NOT NULL CHECK(n6::TEXT ~ '^fe80::[1-9a-f][0-9a-f]{0,3}/128$')
    -- df: inet='fe80::/112'
  -- *** AGGREGATE GENERATORS ***
, z0 TEXT NOT NULL CHECK(z0 ~ '^\w+\.\w+\d@somewhere\.org$')
  -- df: cat=name,dot,name,09,domain
, z1 TEXT NOT NULL CHECK(z1 ~ '^([0-9]|[A-Z][A-Z])$')
  -- df: alt=09,AZ:9
, z2 TEXT NOT NULL CHECK(z2 ~ '^[A-Z]{6,10}$')
  -- df: repeat=AZ extent=3-5
  -- *** SHARED GENERATOR ***
, h0 TEXT NOT NULL CHECK(h0 LIKE 'X%')
  -- df: share=ELEVEN size=1000000 prefix='X'
, h1 TEXT NOT NULL CHECK(h1 LIKE 'Y%')
  -- df: share=ELEVEN size=2000000 prefix='Y'
, h2 TEXT NOT NULL CHECK(h2 LIKE 'Z%')
  -- df: share=ELEVEN size=3000000 prefix='Z'
, h3 DOUBLE PRECISION NOT NULL
  -- df: share=ELEVEN float=uniform alpha=1.0 beta=2.0
, h4 DOUBLE PRECISION NOT NULL
  -- df: share=ELEVEN float=gamma alpha=2.0 beta=3.0
, h5 INTEGER NOT NULL CHECK(h5 BETWEEN 1 AND 1000000)
  -- df: share=ELEVEN offset=1 size=1000000
  -- df one2five: word=:one,two,three,four,five
, h6 TEXT NOT NULL -- df: share=ELEVEN text=one2five
  -- *** MISC GENERATORS ***
, u0 UUID NOT NULL
, u1 CHAR(36) NOT NULL
    CHECK(u1 ~ '^[0-9a-fA-F]{4}([0-9a-fA-F]{4}-){4}[0-9a-fA-F]{12}$')
    -- df: uuid
, u2 BIT(3) NOT NULL
, u3 VARBIT(7) NOT NULL
, u4 TEXT NOT NULL CHECK(u4 ~ '^[01]{8}') -- df: bit length=8
);

ALTER TABLE df.Stuff
  ADD COLUMN a0 INTEGER
, ADD COLUMN a1 INTEGER CHECK(a1 BETWEEN 3 AND 5)
, ADD COLUMN a2 INTEGER NOT NULL
, ADD COLUMN a3 INTEGER
, ADD COLUMN a4 INTEGER;

ALTER TABLE df.Stuff
  ALTER COLUMN a1 SET NOT NULL,
  ADD CONSTRAINT a2_unique UNIQUE(a2),
  ADD CONSTRAINT a3_a4_unique UNIQUE(a3, a4);

CREATE TABLE df.ForeignKeys( -- df: mult=2.0
  id SERIAL PRIMARY KEY
, fk1 INTEGER NOT NULL REFERENCES df.stuff
, fk2 INTEGER REFERENCES df.Stuff -- df: null=0.5
, fk3 INTEGER NOT NULL REFERENCES df.Stuff -- df: sub=serial
, fk4 INTEGER NOT NULL REFERENCES df.Stuff -- df: sub=serial mangle
, fk5 INTEGER NOT NULL REFERENCES df.Stuff -- df: sub=serand
, fk6 INTEGER NOT NULL REFERENCES df.Stuff -- df: sub=serand mangle
, fk7 INTEGER NOT NULL REFERENCES df.Stuff(id) -- df: sub=serand mangle
, fk8 INTEGER NOT NULL REFERENCES df.stuff(i3) -- df: sub=serand mangle
, fk9 INTEGER NOT NULL REFERENCES df.stuff(i3) -- df: sub=uniform
, fka INTEGER NOT NULL REFERENCES df.stuff(i3) -- df: sub=scale rate=0.2
, fkb CHAR(12) NOT NULL REFERENCES df.stuff(s0)
);

CREATE TABLE df.NotFilled( -- df: nogen
  id SERIAL PRIMARY KEY CHECK(id=1)
);
INSERT INTO df.NotFilled(id) VALUES(1);

CREATE TABLE df.Ten( -- df: size=10 null=1.0
  id SERIAL PRIMARY KEY CHECK(id BETWEEN 18 AND 27) -- df: offset=18
, nogen INTEGER CHECK(nogen = 123) DEFAULT 123 -- df: nogen
, n TEXT
  -- forced generators
, x0 TEXT NOT NULL CHECK(x0 ~ '^[0-9]+$') -- df: int size=1000
, x1 TEXT NOT NULL CHECK(x1 = 'TRUE' OR x1 = 'FALSE') -- df: bool
, x2 TEXT NOT NULL CHECK(x2::DOUBLE PRECISION >=0 AND
                         x2::DOUBLE PRECISION <= 100.0)
                         -- df: float alpha=0.0 beta=100.0
, x3 TEXT NOT NULL CHECK(x3 ~ '^\d{4}-\d\d-\d\d$')
   -- df: date end=2013-12-16
, x4 TEXT NOT NULL CHECK(x4 ~ '^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$')
                        -- df: timestamp end='2038-01-19 03:14:07'
, x5 TEXT NOT NULL CHECK(x5 LIKE 'boo%') -- df: string prefix=boo
, x6 TEXT NOT NULL CHECK(x6 ~ '^\d+\s\w+$') -- df: interval unit='day'
  -- more forced generators
, y0 INTEGER NOT NULL CHECK(y0 BETWEEN 2 AND 29)
     -- df: word=:2,3,5,7,11,13,17,19,23,29
, y1 BOOLEAN NOT NULL -- df: word=:TRUE,FALSE
, y2 DOUBLE PRECISION NOT NULL CHECK(y2=0.0 OR y2=1.0) -- df: word=:0.0,1.0
, y3 FLOAT NOT NULL CHECK(y3=0.0 OR y3=1.0) -- df: word=:0.0,1.0
, y4 DATE NOT NULL CHECK(y4 = DATE '2013-06-23' OR y4 = DATE '2038-01-19')
     -- df: word=:2013-06-23,2038-01-19
, y5 TIMESTAMP NOT NULL CHECK(y5 = TIMESTAMP '2013-06-23 19:54:55')
     -- df: word=':2013-06-23 19:54:55'
, y6 INTEGER NOT NULL CHECK(y6::TEXT ~ '^[4-8]{1,9}$')
     -- df: chars='45678' length=5 lenvar=4 size=1000000
, y7 INTERVAL NOT NULL
     -- df: word=:1y,1mon,1day,1h,1m,1s
  -- *** COUNTER ***
, c0 INTEGER NOT NULL CHECK(c0 BETWEEN 3 AND 21)
  -- df: count start=3 step=2
, c1 TEXT NOT NULL CHECK(c1 ~ '^0{7}[1-9A]$') -- df: count format=08X
  -- *** FILE GENERATOR ***
, f0 BYTEA NOT NULL -- df: file=*.blob mode=blob
, f1 TEXT NOT NULL -- df: file=*.txt mode=text
  -- *** GEOMETRY ***
  -- no predefined generators... make do with what is available
, g0 POINT NOT NULL CHECK(g0 <@ BOX '((1,2)(2,3))')
     -- df: pattern='[:float alpha=1.0 beta=2.0:], [:float alpha=2.0 beta=3.0:]'
, g1 BOX NOT NULL CHECK(g1 <@ BOX '((0.0,0.0)(100.0,100.0))')
     -- df pt: float=uniform alpha=1.0 beta=99.0
     -- df ptx: use=pt
     -- df pty: use=pt
     -- df around: float=gauss alpha=0.0 beta=0.01
     -- df ptx_val: value=ptx
     -- df pty_val: value=pty
     -- df: pattern='([:value=ptx:],[:value=pty:])([:reduce=ptx_val,around:],[:reduce=pty_val,around:])'
  -- *** ARRAYS ***
  -- df smalls: int size=9
  -- df directions: word=:N,NE,E,SE,S,SW,W,NW
, a0 INT[] NOT NULL
, a1 INT ARRAY NOT NULL
, a2 TEXT ARRAY[2] NOT NULL
, a3 INT[3] NOT NULL CHECK(array_length(a3, 1) = 3) -- df: array=smalls length=3
, a4 TEXT[2] NOT NULL CHECK(array_length(a4, 1) = 2)
   -- df: array=directions length=2
   -- *** TUPLE ***
, t0 df.addr NOT NULL -- df: use=addr_tuple
);

CREATE TABLE df.Skip( -- df: skip=0.9 size=1000
  id SERIAL PRIMARY KEY
, data CHAR(3) NOT NULL CHECK(data = 'C&H') -- df: const='C&H'
);

-- one may set a directive after the table definition
-- df T=df.Stuff A=a1: size=3 offset=3

-- user-defined types
CREATE DOMAIN df.stuffit AS TEXT;
-- df: type=df.stuffit
-- df df.stuffit: pattern=Calvin|Hobbes|Susie|Moe|Rosalyn
CREATE DOMAIN df.bluff AS TEXT;
-- df: type=df.bluff

CREATE TABLE df.Pattern(
  id SERIAL PRIMARY KEY
, p0 TEXT NOT NULL CHECK(p0 = '') -- df: pattern=''
  --- df: this must be ignored
  ---- df: this must also be ignored
  -- -- df: this must be ignored as well
  -- ignore -- df: again, to be ignored
, p1 TEXT NOT NULL CHECK(p1 = 'hi') -- df: pattern='hi'
, p2 TEXT NOT NULL CHECK(p2 = 'hh') -- df: pattern='h{2}'
, p3 TEXT NOT NULL CHECK(p3 ~ '^[a-z]$') -- df: pattern='[a-z]'
, p4 TEXT NOT NULL CHECK(p4 ~ '^[0-9]{5}$') -- df: pattern='[0-9]{5}'
, p5 TEXT NOT NULL CHECK(p5 ~ '^[A-Z]{3,7}$') -- df: pattern='[A-Z]{3,7}'
, p6 TEXT NOT NULL CHECK(p6 = 'hello') -- df: pattern='(hello)'
, p7 TEXT NOT NULL CHECK(p7 ~ '^(he|ll|o!)$') -- df: pattern='(he|ll|o!)'
, p8 TEXT NOT NULL CHECK(p8 ~ '^(|x|yy){3}$') -- df: pattern='(|x|yy){3}'
, p9 TEXT NOT NULL CHECK(p9 = 'hello') -- df: pattern='hel{2}o'
, pa TEXT NOT NULL CHECK(pa ~ '^[ab][cd]$') -- df: pattern='[ab][cd]'
, pb TEXT NOT NULL CHECK(pb ~ '^[ab][cd]$') -- df: pattern='(a|b)(c|d)'
, pc TEXT NOT NULL CHECK(pc ~ '^a[bB][cC]D$') -- df: pattern='a[bB](c|C)D'
, pd TEXT NOT NULL CHECK(pd ~ '^a?[bB]?[cC]?D?$')
   -- df: pattern='a?[bB]?(c|C)?D?'
, pe TEXT NOT NULL CHECK(pe ~ '^(ac|ad|bc|bd){1,2}$')
   -- df: pattern='((a|b)(c|d)){1,2}'
, pf TEXT NOT NULL CHECK(pf = '') -- df: pattern='(){5,10}'
, pg TEXT NOT NULL CHECK(pg ~ '^(0[a-z]0|1[A-Z]1)$')
   -- df: pattern='0[a-z]0|1[A-Z]1'
, ph TEXT NOT NULL CHECK(ph = '[(|?{') -- df: pattern='\\[\\(\\|\\?\\{'
, pi TEXT NOT NULL CHECK(pi ~ '^0{0,8}1{1,8}2{0,1}$') -- df: pattern='0*1+2?'
, pj TEXT NOT NULL CHECK(pj ~ '^.{2,9}$') -- df: pattern='..+'
, pk TEXT NOT NULL CHECK(pk ~ '^A[0-9]{1,8}[0-9a-f][0-9A-F]!$')
   -- df: pattern='\101\d+\h\H\041'
, pl CHAR(9) NOT NULL CHECK(pl ~ '^[^0-9a-z]{9}$') -- df: pattern='[^0-9a-z]{9}'
-- pm, see below
, pn TEXT NOT NULL CHECK(pn ~ '^[0-9A-Fa-f][0-9][a-z][A-Z]$')
  -- df: pattern='[:xdigit:][:digit:][:lower:][:upper:]'
, po TEXT NOT NULL CHECK(po ~ '^[€œ௲ℝ가𝄞]{1,8}$')
  -- df: pattern='[\\u20ac\\u0153\\U00000bf2\\u211d\\uAC00\\U0001D11E]+'
, pq df.stuffit NOT NULL CHECK(pq ~ '^(Calvin|Hobbes|Susie|Moe|Rosalyn)$')
, pr df.bluff NOT NULL CHECK(pr ~ '^bluff_[_\d]+$') -- df: string prefix=bluff
);

ALTER TABLE df.Pattern
  ADD COLUMN pm TEXT NOT NULL
  CHECK(pm ~ '^[œéÊµ±Þøå€çýð«©ß漢字Яαあア]{1,8}$');
  -- df: pattern='[œéÊµ±Þøå€çýð«©ß漢字Яαあア]+'