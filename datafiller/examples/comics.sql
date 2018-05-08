-- Comics didactic example.

-- Set default scale to 10 tuples for one unit (1.0).
-- This can be overwritten with the size option.
-- df: size=10

-- This relation is not re-generated.
-- However the size will be used when generating foreign keys to this table.
CREATE TABLE Language( --df: nogen size=2
lid SERIAL PRIMARY KEY,
lang TEXT UNIQUE NOT NULL
);

INSERT INTO Language(lid, lang) VALUES
(1, 'French'),
(2, 'English')
;

-- Define a char generator for names:
-- df chfr: int sub=scale rate=0.17
-- df name: chars='esaitnrulodcpmvqfbghjxyzwk' cgen=chfr length=8 lenvar=3

CREATE TABLE Author( --df: mult=1.0
aid SERIAL PRIMARY KEY,
-- There are 200 firstnames do draw from, most frequent 2%.
-- In the 19th century John & Mary were given to >5% of the US population,
-- and rates reached 20% in England in 1800. Currently firstnames are much
-- more diverse, most frequent at about 1%.
firstname TEXT NOT NULL,
  -- df: use=name size=200 sub=scale rate=0.02
-- There are 10000 lastnames to draw from, most frequent 8/1000 (eg Smith)
lastname TEXT NOT NULL,
  -- df: use=name size=10000 sub=scale rate=0.008
-- Choose dates in the 20th century
birth DATE NOT NULL,     -- df: start=1901-01-01 end=2000-12-31
-- We assume that no two authors of the same name are born on the same day
UNIQUE(firstname, lastname, birth)
);

-- On average, about 10 authors per publisher (1.0/0.1)
CREATE TABLE Publisher( -- df: mult=0.1
pid SERIAL PRIMARY KEY,
pname TEXT UNIQUE NOT NULL -- df: prefix=pub length=12 lenvar=4
);

-- On average, about 15.1 books per author (15.1/1.0)
CREATE TABLE Comics( -- df: mult=15.1
cid SERIAL PRIMARY KEY,
title TEXT NOT NULL,     -- df: use=name length=20 lenvar=12
published DATE NOT NULL, -- df: start=1945-01-01 end=2013-06-25
-- The biased scale generator is set for 95% 1 and 5% for others.
-- There are 2 language values because of size=2 on table Language.
lid INTEGER NOT NULL REFERENCES Language, -- df: int sub=scale rate=0.95
pid INTEGER NOT NULL REFERENCES Publisher,
-- A publisher does not publish a title twice in a day
UNIQUE(title, published, pid)
);

-- Most books are stored once in the inventory.
-- About 1% of the books are not in the inventory (skip).
-- Some may be there twice or more (15.2 > 15.1 on Comics).
CREATE TABLE Inventory( -- df: mult=15.2 skip=0.01
iid SERIAL PRIMARY KEY,
cid INTEGER NOT NULL REFERENCES Comics, -- df: sub=serand
shelf INTEGER NOT NULL -- df: size=20
);

-- on average, about 2.2 authors per comics (33.2/15.1)
CREATE TABLE Written( -- df: mult=33.2
-- serand => at least one per author and one per comics, then random
cid INTEGER NOT NULL REFERENCES Comics, -- df: sub=serand mangle
aid INTEGER NOT NULL REFERENCES Author, -- df: sub=serand mangle
PRIMARY KEY(cid, aid)
);