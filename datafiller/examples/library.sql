-- df English: word=/etc/dictionaries-common/words
CREATE TABLE Book( -- df: mult=100.0
bid SERIAL PRIMARY KEY,
title TEXT NOT NULL, -- df: text=English length=4 lenvar=3
isbn ISBN13 NOT NULL -- df: size=1000000000
);

CREATE TABLE Reader( -- df: mult=1.0
rid SERIAL PRIMARY KEY,
firstname TEXT NOT NULL, -- df: prefix=fn size=1000 sub=power rate=0.03
lastname TEXT NOT NULL, -- df: prefix=ln size=10000 sub=power rate=0.01
born DATE NOT NULL, -- df: start=1923-01-01 end=2010-01-01
gender BOOLEAN NOT NULL, -- df: rate=0.25
phone TEXT -- df:  chars='0-9' null=0.01 size=1000000 length=10 lenvar=0
);

CREATE TABLE Borrow( -- df: mult=1.5
borrowed TIMESTAMP NOT NULL, -- df: size=72000
rid INTEGER NOT NULL REFERENCES Reader,
bid INTEGER NOT NULL REFERENCES Book, -- df: mangle
PRIMARY KEY(bid) -- a book is borrowed once at a time!
);