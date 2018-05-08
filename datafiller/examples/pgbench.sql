-- TPC-B example adapted from pgbench

-- df regress: int sub=power alpha=1.5
-- df: size=1

CREATE TABLE pgbench_branches( -- df: mult=1.0
bid SERIAL PRIMARY KEY,
bbalance INTEGER NOT NULL,   -- df: size=100000000 use=regress
filler CHAR(88) NOT NULL
);

CREATE TABLE pgbench_tellers(  -- df: mult=10.0
tid SERIAL PRIMARY KEY,
bid INTEGER NOT NULL REFERENCES pgbench_branches,
tbalance INTEGER NOT NULL,   -- df: size=100000 use=regress
filler CHAR(84) NOT NULL
);

CREATE TABLE pgbench_accounts( -- df: mult=100000.0
aid BIGSERIAL PRIMARY KEY,
bid INTEGER NOT NULL REFERENCES pgbench_branches,
abalance INTEGER NOT NULL,   -- df: offset=-1000 size=100000 use=regress
filler CHAR(84) NOT NULL
);

CREATE TABLE pgbench_history(  -- df: nogen
tid INTEGER NOT NULL REFERENCES pgbench_tellers,
bid INTEGER NOT NULL REFERENCES pgbench_branches,
aid BIGINT NOT NULL REFERENCES pgbench_accounts,
delta INTEGER NOT NULL,
mtime TIMESTAMP NOT NULL,
filler CHAR(22)
-- UNIQUE (tid, bid, aid, mtime)
);