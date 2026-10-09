-- What people tap on /find (publish/findlearn.js). Beside the index in
-- motdang-search, so the ranking reads it in the same database. load.py never
-- touches these tables: an in-place reload replaces pages/keys/fts rows, a
-- --beside reload swaps only its own tables. Keyed by page ADDRESS, not id —
-- ids are renumbered by every reload.
--   npx wrangler d1 execute motdang-search --remote --file=fleetsearch/learn.sql
CREATE TABLE IF NOT EXISTS learn (
  qk       TEXT NOT NULL,              -- learnKey(query): folded, sorted words
  url      TEXT NOT NULL,
  shown    INTEGER NOT NULL DEFAULT 0, -- impressions (ranked above the deepest tap, or top 3)
  taps     INTEGER NOT NULL DEFAULT 0,
  pogo     INTEGER NOT NULL DEFAULT 0, -- back on the results within 10 s of a tap
  via      INTEGER NOT NULL DEFAULT 0, -- tapped after this query was rephrased into another
  rank_sum INTEGER NOT NULL DEFAULT 0, -- sum of the ranks it was tapped at
  dwell_ms INTEGER NOT NULL DEFAULT 0, -- time away before coming back, capped at 10 min a visit
  dwell_n  INTEGER NOT NULL DEFAULT 0,
  last     TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (qk, url)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS learn_q (
  qk     TEXT PRIMARY KEY,
  views  INTEGER NOT NULL DEFAULT 0,   -- results pages left by a person
  tapped INTEGER NOT NULL DEFAULT 0,   -- … of which a result was tapped
  reform INTEGER NOT NULL DEFAULT 0,   -- … rephrased within five minutes with no tap
  last   TEXT NOT NULL DEFAULT (datetime('now'))
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS learn_pair (
  qk   TEXT NOT NULL,                  -- the query asked first
  next TEXT NOT NULL,                  -- the one asked next, in the same tab, within five minutes
  n    INTEGER NOT NULL DEFAULT 0,
  last TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (qk, next)
) WITHOUT ROWID;
