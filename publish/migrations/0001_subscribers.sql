-- 0001_subscribers.sql — the mailing list, in its own D1 database.
--
-- NOT the search index (a reload of that must never touch a person's address)
-- and NOT the site bucket (that IS the public web). A database of its own,
-- bound as SUBSCRIBERS in publish/wrangler.toml.
--
-- DO NOT RUN THIS AS PART OF A CONTENT DEPLOY. It is applied once, by Nan,
-- against the database she creates:
--   npx wrangler d1 create motdang-subscribers        # note the id → wrangler.toml
--   npx wrangler d1 execute motdang-subscribers --file=publish/migrations/0001_subscribers.sql --remote
--
-- A subscriber is PENDING until they click the link in their own inbox, then
-- CONFIRMED. 'unsubscribed' is here for the unsubscribe seam; the flow that
-- sets it is not built yet.

CREATE TABLE IF NOT EXISTS subscribers (
  email        TEXT PRIMARY KEY,                 -- normalised: trimmed, lower-cased
  status       TEXT NOT NULL DEFAULT 'pending'   -- 'pending' | 'confirmed' | 'unsubscribed'
                 CHECK (status IN ('pending','confirmed','unsubscribed')),
  token        TEXT NOT NULL,                     -- confirm + unsubscribe key (128-bit hex)
  source       TEXT,                              -- which page/block sent them; a breadcrumb, not a tracker
  lang         TEXT DEFAULT 'both',               -- 'th' | 'en' | 'both'
  created_at   TEXT NOT NULL,                     -- ISO 8601, when the PENDING row was written
  confirmed_at TEXT,                              -- ISO 8601, set on PENDING → CONFIRMED; NULL until then

  -- THE PERKS SEAM. Opting in is what later unlocks "goodies"; none are built
  -- now. This JSON object is the documented place a capability lands
  -- (e.g. {"early_access": true}) without another migration. Left '{}'.
  perks        TEXT NOT NULL DEFAULT '{}'
);

-- Confirm and unsubscribe both arrive by token, so it is looked up by token.
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_token ON subscribers (token);

-- "How many are confirmed", "who is still pending" — the two counts Nan will
-- ask for, answered without a scan.
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers (status);
