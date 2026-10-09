-- 0002_listers.sql — listing agents, in the SAME database as the mailing list
-- (motdang-subscribers, binding SUBSCRIBERS). Joining the newsletter is the
-- condition of listing, so a lister row sits beside its subscriber row and
-- the two join on email.
--
-- Applied once, by Nan, after 0001:
--   npx wrangler d1 execute motdang-subscribers --file=migrations/0002_listers.sql --remote
--
-- Column names follow the RESO Data Dictionary's Member resource where one
-- fits (MemberKey, MemberEmail, MemberFullName, OfficeName, OfficeKey,
-- MemberPreferredPhone, MemberStatus, OriginalEntryTimestamp,
-- ModificationTimestamp), snake-cased.
--
-- status:  applied   → sent the join form, email not yet confirmed
--          confirmed → clicked the link in their own inbox; waiting on Nan
--          invited   → Nan tapped INVITE (or LISTER_INVITE="auto"); may sign in
--          declined  → Nan tapped DECLINE before inviting
--          revoked   → DECLINE tapped after the invite; sign-in stops working

CREATE TABLE IF NOT EXISTS listers (
  member_key       TEXT PRIMARY KEY,               -- MemberKey: 128-bit random hex
  email            TEXT NOT NULL UNIQUE,           -- MemberEmail; = subscribers.email
  full_name        TEXT NOT NULL,                  -- MemberFullName
  office_name      TEXT NOT NULL,                  -- OfficeName, as typed
  office_key       TEXT NOT NULL,                  -- OfficeKey: slug, same fold as listing-sheet/agencies.py
  phone            TEXT,                           -- MemberPreferredPhone
  line_id          TEXT,                           -- LINE ID
  provinces        TEXT NOT NULL,                  -- 'cm' | 'cr' | 'cm,cr'
  status           TEXT NOT NULL DEFAULT 'applied' -- MemberStatus
                     CHECK (status IN ('applied','confirmed','invited','declined','revoked')),
  lang             TEXT DEFAULT 'both',            -- 'th' | 'en' | 'both'
  reuse_consent    INTEGER NOT NULL DEFAULT 0,     -- 1 = ticked the CC BY 4.0 reuse box
  consent_version  TEXT,                           -- which wording they ticked
  created_at       TEXT NOT NULL,                  -- OriginalEntryTimestamp (ISO 8601)
  modified_at      TEXT NOT NULL,                  -- ModificationTimestamp
  confirmed_at     TEXT,
  invited_at       TEXT,
  declined_at      TEXT,
  revoked_at       TEXT,
  last_signin_at   TEXT,

  -- Capability tokens (128-bit hex) and their expiry (ISO 8601).
  invite_token     TEXT,                           -- Nan's one-tap INVITE
  invite_expires   TEXT,
  decline_token    TEXT,                           -- Nan's one-tap DECLINE (revoke after invite)
  decline_expires  TEXT,
  signin_token     TEXT,                           -- single-use sign-in link
  signin_expires   TEXT,
  signin_sent_at   TEXT                            -- throttles repeat sign-in mail
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_listers_invite  ON listers (invite_token);
CREATE UNIQUE INDEX IF NOT EXISTS idx_listers_decline ON listers (decline_token);
CREATE UNIQUE INDEX IF NOT EXISTS idx_listers_signin  ON listers (signin_token);
CREATE INDEX IF NOT EXISTS idx_listers_status ON listers (status);
