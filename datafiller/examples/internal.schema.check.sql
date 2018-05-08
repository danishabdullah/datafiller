-- useful for additional checks
CREATE OR REPLACE FUNCTION df.assert(what TEXT, ok BOOLEAN) RETURNS BOOLEAN
IMMUTABLE CALLED ON NULL INPUT AS $$
BEGIN
  IF ok IS NULL OR NOT ok THEN
    RAISE EXCEPTION 'assert failed: %', what;
  END IF;
  RETURN ok;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION df.assert_eq(what TEXT, v BIGINT, r BIGINT)
RETURNS BOOLEAN
IMMUTABLE CALLED ON NULL INPUT AS $$
BEGIN
  IF v IS NULL OR r IS NULL OR v <> r THEN
    RAISE EXCEPTION 'assert failed: % (% vs %)', what, v, r;
  END IF;
  RETURN TRUE;
END
$$ LANGUAGE plpgsql;

-- one if true else 0
CREATE FUNCTION df.oitez(ok BOOLEAN) RETURNS INTEGER
IMMUTABLE STRICT AS $$
  SELECT CASE WHEN ok THEN 1 ELSE 0 END;
$$ LANGUAGE SQL;

-- check value to a precision
CREATE FUNCTION df.value(d DOUBLE PRECISION,
                         val DOUBLE PRECISION, epsilon DOUBLE PRECISION)
RETURNS BOOLEAN
IMMUTABLE STRICT AS $$
  SELECT d BETWEEN val-epsilon AND val+epsilon;
$$ LANGUAGE SQL;

\\echo '# generator checks'
SELECT
  -- check ints
  df.assert('skewed power',
      df.value(AVG(df.oitez(i4=1)), 0.7, 0.1)) AS "i4"
, df.assert('skewed scale',
      df.value(AVG(df.oitez(i5=1)), 0.7, 0.1)) AS "i5"

  -- check bools
, df.assert('b0 rate',
      df.value(AVG(df.oitez(b0)), 0.5, 0.1) AND
      df.value(AVG(df.oitez(b0)), 0.5, 0.1)) AS "b0"
, df.assert('b1 rates',
      df.value(AVG(df.oitez(b1 IS NULL)), 0.5, 0.1) AND
      df.value(AVG(df.oitez(b1)), 0.5, 0.1)) AS "b1"
, df.assert('b2 0.7 rate',
      df.value(AVG(df.oitez(b2)), 0.7, 0.1)) AS "b2"

  -- check floats
, df.assert('uniform', -- 0.5 +- 0.29
      df.value(AVG(f0), 0.5, 0.05) AND df.value(STDDEV(f0), 0.289, 0.05))
      AS "f0"
, df.assert('gaussian',
      df.value(AVG(f1), 5.0, 0.5) AND df.value(STDDEV(f1), 2.0, 0.5))
      AS "f1"
, df.assert('uniform 2',
      df.value(AVG(f2), 0.0, 1.0) AND df.value(STDDEV(f2), 5.77, 0.5))
      AS "f2"
-- , df.assert('exponential', df.value(AVG(f4), 1.0/0.1, 1.0)) AS "f4"
, df.assert('normal',
      df.value(AVG(f7), 20.0, 0.1) AND df.value(STDDEV(f7), 0.5, 0.1)) AS "f7"

  -- check dates
, df.assert_eq('d4 days', COUNT(DISTINCT d4), 2) AS "d4"
, df.assert_eq('d5 days', COUNT(DISTINCT d5), 2) AS "d5"

  -- check timestamps
, df.assert_eq('t0 stamps', COUNT(DISTINCT t0), 2) AS "t0"
, df.assert_eq('t1 stamps', COUNT(DISTINCT t1), 2) AS "t1"
, df.assert_eq('t2 stamps', COUNT(DISTINCT t2), 30) AS "t2"

  -- check text
, df.assert_eq('s2 text 1', COUNT(DISTINCT s2), 20) AS "s2-1"
, df.assert_eq('s2 text 2', MAX(LENGTH(s2))-MIN(LENGTH(s2)), 2) AS "s2-2"
, df.assert_eq('s4 text', COUNT(DISTINCT s4), 20) AS "s4"
, df.assert_eq('s5 text 1', COUNT(DISTINCT s5), 50) AS "s5-1"
, df.assert('s5 text 2',
            df.value(AVG(LENGTH(REPLACE(s5,'b',''))), 30*0.7, 1.0)) AS "s5-2"
, df.assert_eq('s6 text', COUNT(DISTINCT s6), 3) AS "s6"
, df.assert_eq('s7 text', COUNT(DISTINCT s7), 3) AS "s7"
, df.assert_eq('s8 text', COUNT(DISTINCT s8), 16) AS "s8"
, df.assert_eq('n3 mac', COUNT(DISTINCT n3), 17) AS "n3"
  -- expected z1 length is 0.9 * 2 + 0.1 * 1 = 1.9
, df.assert('z1 list', AVG(LENGTH(z1)) BETWEEN 1.85 AND 1.95) AS "z1"

  -- check ELEVEN share
, df.assert_eq('h0', COUNT(DISTINCT h0), 11) AS "h0"
, df.assert_eq('h1', COUNT(DISTINCT h1), 11) AS "h1"
, df.assert_eq('h2', COUNT(DISTINCT h2), 11) AS "h2"
, df.assert_eq('h3', COUNT(DISTINCT h3), 11) AS "h3"
, df.assert_eq('h4', COUNT(DISTINCT h4), 11) AS "h4"
, df.assert_eq('h5', COUNT(DISTINCT h5), 11) AS "h5"
, df.assert_eq('h6', COUNT(DISTINCT h6), 11) AS "h6"
, df.assert_eq('h0-6 share',
            COUNT(DISTINCT (h0, h1, h2, h3, h4, h5, h6)), 11) AS "h0-6"
FROM df.stuff;

\\echo '# foreign key checks'
SELECT
  df.assert('fk2', df.value(AVG(df.oitez(fk2 IS NULL)), 0.5, 0.1)) AS "fk2"
, df.assert('fka', df.value(AVG(df.oitez(fka = 1000000)), 0.2, 0.05)) AS "fka"
FROM df.ForeignKeys;

\\echo '# miscellaneous checks'
SELECT
  df.assert_eq('ten', COUNT(*), 10) AS "ten"
, df.assert_eq('123', SUM(df.oitez(nogen=123)), 10) AS "123"
, df.assert_eq('null', SUM(df.oitez(n IS NULL)), 10) AS "null"
, df.assert_eq('c0', COUNT(DISTINCT c0), 10) AS "c0"
, df.assert_eq('c1', COUNT(DISTINCT c1), 10) AS "c1"
FROM df.Ten;

\\echo '# skip check'
SELECT
  df.assert('skip', COUNT(*) BETWEEN 50 AND 150) AS "skip"
FROM df.Skip;

DROP SCHEMA df CASCADE;