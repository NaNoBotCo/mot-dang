# "You've heard of motdang.net?" — the recognition plan

*2026-08-20. Nan: "I want to start telling people 'you've heard of motdang.net? then you've seen my work.' Plan this so it works." This note is the plan. Read with `MARCHING-ORDERS.md` — the two site-side gaps became **WO-30**, built 2026-08-21. Survey behind it: repo + live site + pitch kit, 2026-08-20; counts refreshed from the 08-21 build.*

**The goal.** Nan says the line — and the other person nods. The plan makes the nod common in the rooms she is actually in by the end of January.

## What "works" means — measured, staged

- **Now → Sep 8:** baseline. Log every attempt (any gear, see below). Expect near-zero; that is the starting line, not a verdict.
- **End of October** (after the party + กินเจ): **1 nod in 4.**
- **Mid-December** (after ยี่เป็ง + newsletter/CityLife coverage): **1 in 3.**
- **Jan 30, 2027** (CMIRC ball drop): **1 in 2** — the line gets said straight, no setup.

Strangers city-wide will lag these numbers. The rooms come first on purpose — narrow, then widen.

## Say it in three gears (the line is spoken, not read)

- **Gear 0 — show first.** Their actual question, answered on the phone in front of them (open-now, toilets, muay thai tonight). Then: *"That's mine."* Strongest form while recognition is low — and it is dogfooding with witnesses. Every Gear-0 conversation is also an asked-loop lead.
- **Gear 1 — prompt.** *"The red-ant site — mot dang?"* The ant does the remembering: มดแดง (mot daeng, "red ant") is the recall hook.
- **Gear 2 — the line itself.** Earned when the ledger says 1-in-2.

Spoken-word insurance: say it spelled once — "M-O-T-D-A-N-G dot net"; the pocket QR card skips spelling entirely; and a Google search for "mot dang chiang mai" must land the site at #1 (item 8).

## Where it stands (survey 2026-08-20)

**Built and working for this goal:** the site live at motdang.net (**19,980 places**, 21,703 pages, Thai-first); ~2,000 share cards (1,900 place, 256 shelf, plus asked); the ถามมด loop — question → page + card + `make_post.py` paste-ready reply; LINE OA @964yxgnk with rich menu; printed A4 handouts + reader sheets + QR assets (`make_handouts.py`, `assets/qr/`); the festival wheel print files (A3/A4, in motdang-pitch/print/); `partners.html` publicly offering cross-promotion to Chiang Mai CityLife and Steve's Chiang Mai Newsletter — published but never emailed; the signed brief at /brief; the party runbook with Pim's standing Algonquin offer; the owned mailing list capturing on the hub pages.

**The two gaps that mattered — BOTH CLOSED 2026-08-21 as WO-30:**
1. ~~The built site never says a person made it.~~ **`/who.html` is built** — ใครเลี้ยงมด · Who keeps the ants, named, footer-linked on every page, in the sitemap and llms.txt, with `meta name=author` + JSON-LD `Person`. The no-desc fallback is now a full sentence in both languages, plus `og:locale:alternate`.
2. ~~There is no way to know who's heard.~~ **`heard.py` is built** — the nod ledger, numbered menu, `data/heard.jsonl`, fenced out of both publish paths. Recognition now has its metric.

Both verified on a scratch build of 21,703 pages; publish gate, alt-text and asked gates all PASS. They ship on the next walk after the current `cache/walk-rest` expires.

## What this plan is made of

Paper cannot be deplatformed — every idea here survives the platform disappearing. So this plan is rooms, paper, answered questions, one newsletter, one press relationship, and the LINE OA. Nothing here breaks if Meta flips a switch.

Mot Dang has no Facebook account. In groups it is Nan answering under her own name, with the site's answer — not a workaround, but the association the line needs.

## The gate, first

The restored Facebook account's first use is the Messenger evidence export (the standing order in the distribution notes). Until that copy exists, no group posting. It protects two live matters and it unblocks everything below.

## The engine — two answered questions a week

The asked loop holds **12 questions, 9 published** (three drafts, which render nowhere by design). Cadence: **2/week** — one carried out of a Facebook/LINE group, one from suggest.html or a Gear-0 conversation. Fleet researches and drafts (`asked_new.py` → research → `asked_check.py` → build); Nan approves and pastes the `make_post.py` reply. Each answer ships a page, a card that unfurls (or the Save-card poster where links get buried), and her name on the reply.

Running total from nine: ~18 by the party, ~32 by ยี่เป็ง, ~44 by the ball drop. The card is the billboard; the reply is the proof of work.

## The calendar

| When | What |
|---|---|
| Sep 1 | Festival Push drip begins (already planned). Ledger running by now. |
| Early Sep | Message Pim: warm yes to the Algonquin, late-Sep/early-Oct dates offered, festival wheel goes along as the gift — before any ask. CityLife's ยี่เป็ง lead time is exactly now. `4-pim.md` governs. |
| Mid Sep | The two partner emails go out (CityLife per the Pim playbook; Steve's newsletter gets the standing linked-page offer already published on partners.html). Email first, citations in, one video call offered. |
| Late Sep / early Oct | **The party** — runbook stands: QR wall, toilet card, wheel on the wall, brief copies, capture via LINE OA + list + my.html. The empathy map calls its personas hypotheses awaiting the first ten QR scans; the party is that test too. |
| Oct 10–18 | กินเจ (kin che, the vegetarian festival): cooking-shelf push, asked questions themed to it. |
| Mid Oct | Marine Corps Ball — not a venue, a room. Pocket cards in the clutch; Gear 0 all night. |
| Nov 24–25 | ยี่เป็ง (Yi Peng): the festivals board + wheel are the city's best festival surface. If the September gift landed, CityLife coverage cites Mot Dang here. |
| Jan 30 | CMIRC ball drop — the 1-in-2 checkpoint. |

## Signed work — BUILT as WO-30, 2026-08-21

`/who.html` — **ใครเลี้ยงมด · Who keeps the ants** — in the ants' own voice: the ants do the walking; one person feeds them — Annika "Nan" Peacock, NaNoBotCo, Chiang Mai. Four modules (who · how the ants walk · what happens when it is wrong), then the channels card that already names the accounts which are NOT us. Footer link on every page, in the sitemap, named in llms.txt as the attribution for anyone summarising the corpus. `/who` resolves too. The persona stays institutional; one page answers the second beat of the conversation ("wait — that's you?").

It deliberately does **not** link /brief: the deck is noindex and investor-facing, and putting it one click from a reader page is Nan's call, not a default.

## Counting the nods

- **The ledger (primary) — BUILT 2026-08-21.** `python3 heard.py` in the mot-dang repo: numbered menu, 1 = didn't know · 2 = knew the site · 3 = knew it was hers, plus an optional coarse room. `--report` prints the monthly rate against the targets above and which rooms earn nods; `--undo` takes back a mis-key. Appends to `data/heard.jsonl` — a diary, never published, no other person's name stored. The monthly rate is THE metric of this plan.
- **Already-built signals:** nanobot-list `/stats` per-source signups (source `motdang`); LINE OA contact count; Ko-fi; suggest.html question inflow.
- **Server-side only:** a monthly glance at Cloudflare's own Worker/R2 request graphs — nothing added to any page, ever.
- **Search Console** (after item 8): which English/Thai queries surface the site.
- **Monthly:** a ten-line review in notes/ — the rate, what moved, one deficiency to fix next.

## GO-LIST — answer with numbers

฿0 unless priced. "Hers" = needs Nan; "fleet" = drafted/built for approval.

1. ~~Ledger live today~~ **DONE 2026-08-21** — `python3 heard.py`. Hers now: one keypress per try. The pre-September baseline is the before/after proof.
2. **Messenger export first** — hers, ~30 careful minutes. Unblocks all group posting; the copy that exists nowhere else.
3. **Message Pim** — hers, from the playbook: warm yes + late-Sep dates + the wheel as gift. If it slides, the ยี่เป็ง press window slides a year.
4. **Two partner emails** — fleet drafts from partners.html + the email-first rules; hers to send. CityLife (via Pim), Steve's newsletter.
5. **Asked ×2/week** — fleet researches + drafts; hers: approve + paste. The weekly heartbeat everything else amplifies.
6. **Print run** — hers, one errand, ~฿300–800: pocket QR cards, krapow/massage/wat handouts, reader sheets, wheel A3 for the party wall. (Driver/housekeeper sheets stay blocked per AGENTS.md until unlisted-by-default ships.)
7. ~~WO-21: who-runs-this page + English description~~ **BUILT as WO-30, 2026-08-21** — on disk, gates PASS; the standing walk ships it once the current `cache/walk-rest` expires.
8. **Search Console** — hers, 10 min with the Google login; fleet stages the verification file and submits the sitemap (8,036 URLs already waiting).
9. **The party** — date from Pim; runbook executes. The autumn's anchor.
10. **Monthly nod review** — fleet compiles the ledger + signals into ten lines in notes/; first one Oct 1.

## Bench — only if the ledger says so

11. `motdaeng.net` defensive redirect (~$13/yr) if spelling misses show up in the ledger.
12. Worker-side aggregate path counts — its own WO; no client change.
13. One "I built this" post from Nan personally (r/chiangmai), timed to ยี่เป็ง week. A spike, not a channel — nothing depends on it, so it passes the platform-disappearing test. reach.html's 47%-dead-official-links finding is the story, ready-made.

## Files

- This plan: `notes/heard-of-it-proposal-2026-08-20.md` (repo) · `~/Desktop/1 — NEXT UP/motdang-heard-of-it-plan.md` (desktop copy)
- Companions: `MARCHING-ORDERS.md` · `motdang-pitch/2-launch-party-runbook.md` · `motdang-pitch/4-pim.md` · `docs/partners.html` · `AGENTS.md`
