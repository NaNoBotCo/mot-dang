-- live.js: a reader's position shared for an hour. One row per share.
CREATE TABLE IF NOT EXISTS live (
  id TEXT PRIMARY KEY, tok TEXT NOT NULL, made INTEGER NOT NULL, until INTEGER NOT NULL,
  lat REAL, lng REAL, acc REAL, at INTEGER);
