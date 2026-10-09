-- 0003_lister_checks.sql — what the confirm-time sanity check needs
-- (publish/lister.js, sanityCheck). Applied once, by Nan, after 0002:
--   npx wrangler d1 execute motdang-subscribers --file=migrations/0003_lister_checks.sql --remote
-- ALTER TABLE ... ADD COLUMN has no IF NOT EXISTS in SQLite, so a second run
-- errors on the first line and changes nothing.

-- A keyed SHA-256 of the applicant's IP (first 16 hex), enough to count
-- applications per address per day. The IP itself is not written.
ALTER TABLE listers ADD COLUMN ip_hash TEXT;

-- JSON array of the checks a confirmed applicant failed, e.g.
-- ["disposable email domain","phone is not a Thai number and no LINE ID"].
-- NULL when every check passed. A row with reasons stays 'confirmed' until
-- Nan taps INVITE or DECLINE.
ALTER TABLE listers ADD COLUMN held_reasons TEXT;

-- 'auto' (LISTER_INVITE="auto" and the checks passed) or 'operator' (her tap).
ALTER TABLE listers ADD COLUMN invited_by TEXT;

CREATE INDEX IF NOT EXISTS idx_listers_ip ON listers (ip_hash, created_at);
