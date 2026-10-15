-- 0005_newsletter.sql — which issue went to which address, written before the
-- mail goes so a repeated send of one issue skips everyone already sent to.
-- live = 0 for a send while NEWSLETTER_LIVE was off (test addresses only).
CREATE TABLE IF NOT EXISTS newsletter_sends (
  issue  TEXT NOT NULL,             -- YYYY-MM-DD, the Monday the issue covers from
  email  TEXT NOT NULL,
  at     TEXT NOT NULL,             -- ISO 8601
  live   INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (issue, email)
);
