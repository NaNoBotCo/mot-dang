# For the next ant

Instructions for whatever agent picks this repo up next. `CLAUDE.md` holds the rules that bite during a build; this file holds the reasons, so you can decide well about things nobody wrote a rule for yet. Read `notes/empathy-map.md` before you build anything user-facing.

Written 2026-07-30, after a week in which the site grew an ant rank, a LINE front door, royal temple grades, per-place share cards and five printed handouts, and in which the founder's Facebook account was disabled overnight with a single appeal.

---

## What this is

A city directory for Chiang Mai and Chiang Rai. Thai first, open data, static HTML, stdlib Python, no tracking, no login, no ratings, no paid placement. It is run by one person and it competes with Google by being structurally different rather than bigger: every fact carries where it came from and when it was read.

It is not a startup, a marketplace, a platform, or an MVP on the way to something. Do not propose growth mechanics, engagement loops, referral schemes, gamified streaks, A/B tests on the copy, or a mobile app. All of those have been considered and none of them fit a project whose entire proposition is that it does not do that.

## Who it is for

Six readers, mapped in `notes/empathy-map.md`. In one line each: a shop owner who assumes the internet will eventually charge her; a temple steward who cares about propriety before reach; a driver running from platform commission; a migrant housekeeper for whom visibility is a risk before it is an opportunity; a therapist whose name is her asset; and a machine that will carry whatever it is given, confidently, forever.

The one you will forget is the fourth. Most product instincts assume the user wants to be found. She does not, by default. Build for her explicitly or you will build something that harms her while looking generous.

---

## What delight means here

Not animation. Not micro-interactions. Not a design system. The site is deliberately 1997 in register and that is load — that is the point, not a limitation to route around. Delight here has four shapes, and all four are already in the codebase to copy from.

**Recognition.** Something a Thai reader sees and knows instantly, that no global platform would ever carry. Day colours (สีประจำวัน) driving the accent. Buddhist Era dates. Royal monastery grades. The lunar disc. Wan phra. These cost almost nothing and they say *this was made by someone who lives here*. When you are choosing between two features, the one a foreigner would not think of is usually the right one.

**The totem doing work.** The red ant is not a logo, it is a unit. One ant per fact held, nine for a complete listing. Ant trails as dividers. The ant standing in where a photo is missing. `wat.svg` for `wat` and `sights` only — a temple illustration on a massage listing was wrong in a way that reads as an accusation, and that fix is the model for this kind of judgement. Extend the totem before you invent a new visual language.

**Auspiciousness as a constraint.** Nine, not eight. No ominous words in nav or labels. The katha in `llms.txt` is sincere. If a number is arbitrary, make it nine. This is not decoration and it is not to be quietly rationalised away by an agent that finds it unscientific.

**Honesty rendered as interface.** The dead-link forensics on `reach.html` — naming a dead link, dating it, linking the archive rather than pretending. The ant rank showing exactly what is missing. Marks that print the year of the edition they were read from. This is the deepest delight the site has, because it is the thing readers cannot get anywhere else, and it converts directly into trust. When you have a choice between hiding an imperfection and dating it, date it.

## What value means here

**Information is power, made visible.** The ant rank exists to turn "your listing is thin" into something an owner can see, count, and fix in five minutes. Any new signal should follow that pattern: legible, countable, unbuyable.

**Nothing is for sale except the ad box.** No paid placement, no boosted listings, no lead fees, no commission, no ranking that money can move. Advertising sits in a marked box and never mixes into a listing. If a proposal quietly breaks this, it is not a proposal, it is the end of the project's reason to exist.

**Provenance beats volume.** Another thousand crawled records with no contact details is worth less than a hundred with a dated source. The 0-to-9 distribution is truthful and unflattering — most places sit at 0 to 2 — and that is fine. Do not inflate a score to make a page look better.

**Marks are dated or they are not published.** Michelin, เชลล์ชวนชิม, royal grade: every entry in `data/curated/honours.json` carries `edition`/`sources`, and the badge prints the year. A mark with a year stays true forever. A mark without one rots into a lie. Nothing goes into the verified lists without a URL that was actually fetched; leads live in `unverified` and never render.

---

## Rules that came from being wrong

These are not style preferences. Each one is a scar.

**A crawl is not a verification.** The freshness ant originally counted `updatedAt`, which meant one bulk OSM import handed the ant to all 10,000 records at once and the signal said nothing. Freshness now requires a human touch — an owner's claim, or a curated/field source. Any signal that everything can earn simultaneously is not a signal.

**Never publish a person's private data to make a page look complete.** No home addresses for individuals, no ID numbers, no plate numbers, nothing about visa or work permit. Do not ask for them either. The ant rank must never reward publishing them.

**Do not write in a language you cannot read back.** The Shan on the housekeeper handout is a machine attempt and the sheet prints a black UNVERIFIED banner across both sides until a Shan speaker signs it off (`shanVerified` in `data/curated/handouts.json`). A wrong handout given to a migrant worker is worse than no handout. The same discipline applies to any Thai legal or administrative claim: search a current source or say plainly that you do not know.

**One source of truth per channel.** `data/config.json` holds the contact email, LINE OA id and QR. A superseded `data/line.json` path survived a refactor, was still being called, and rendered nothing — two sources of truth for the same phone number is how a wrong number eventually ships. Delete the loser.

**Every channel except the domain belongs to someone else.** Facebook proved it on 29 July: disabled overnight, one appeal, permanent if it fails. `OUR_CHANNELS` / `NOT_OUR_CHANNELS` in `build.py` states what is ours and what is not, renders it on `add.html`, publishes `data/channels.json`, and says in `llms.txt` that any Facebook, Instagram, TikTok or X account claiming to be มดแดง is an impostor and that nobody is ever asked for money to be listed. Keep that current. The contact address in `config.json` is still a free third-party mailbox printed on ten thousand pages; moving it to an address on the domain is the outstanding fix.

**Paper cannot be deplatformed.** `make_handouts.py` exists because of the above. The per-place QR, the printed A4, and the sheet handed over in person are the only channels no company can switch off. When a distribution idea comes up, ask whether it survives the platform disappearing.

---

## How to decide what to build next

Four questions, in order. A no at any point means stop.

1. **Which of the six does this serve, and would they recognise the description of their own problem?** If the answer is "users", you have not thought about it yet.
2. **Does it work on a five-year-old Android, on a bad connection, in Thai, for someone who will not install anything?** That is the median reader. Not you, and not the farang expat, who is already won and is not the frontier.
3. **Does it make a fact more legible, or does it make the site louder?** Legible wins. Loud loses.
4. **Would it still be true if nobody maintained it for a year?** Static, dated, sourced things survive. Live integrations, undated marks, and anything that assumes a weekly human rot into wrongness. Prefer the thing that ages into "out of date" over the thing that ages into "wrong".

## The verification bar

Do not report work as done on the strength of having written it.

Run `python3 build.py` and read the page count. Open the actual output and grep for the thing you claimed to add. Render a PDF or PNG deliverable and *look at it* — the share cards were silently cropped by a headless-Chrome viewport quirk for three iterations because nobody looked. Check both the Thai and the English. Check a place page, a category page, and the homepage, because they take different code paths.

Two environment traps that cost real time and will cost you the same time again. Staged file copies can be served stale from cache, so a file you "read" may be an old snapshot — check the byte count against the source before you conclude something has been lost or overwritten. And the Cowork device mount permits writes but forbids unlink, so `shutil.rmtree` fails there; `build.py` now warns and overwrites in place rather than refusing, but a build done that way can leave stale pages behind and must not be published.

## Standing debts

In the order they should be paid.

1. **A person is not a place.** The driver and housekeeper handouts promise a page that the schema cannot yet create — `home-services` holds zero records and `transport` holds fuel stations. Until this exists, those two sheets must not be handed out.
2. **Unlisted by default for people.** URL and QR reachable; absent from the category index, the sitemap, `places.json` and `llms-full.txt`; `noindex`; opt in to indexing separately. See the fourth persona for why this is not optional.
3. **`hello@motdang.net`** on the domain, forwarding wherever, replacing the free mailbox in `config.json`.
4. **The Shan needs a human.** Fifteen minutes of a Shan speaker's time clears the banner.
5. **The 2026 Michelin roster and the เชลล์ชวนชิม holders** need a real browser — the filter pages render client-side and `shellshuanshim.com` serves an expired certificate. The 2022-edition entries currently on the site are dated and say so, but they are four editions stale.
6. **Ask whether a sponsor block belongs on a wat page.**

## Where things live

`build.py` — the whole site generator, stdlib only, `docs/` is the output and is committed. `festivals_layer.py` — festival pages, imported by the build. `make_og_cards.py` — per-place share cards into `assets/og/`, Chrome-rendered because Pillow here cannot shape Thai. `make_shelf_cards.py` — the same for list pages: one card per province, category and sub-shelf, carrying the names on the shelf, so a shared link answers “who does THIS” instead of unfurling as the brand ant. `data/asked.json` + `asked_layer.py` — reader questions as data: each entry renders its ถามมด card, its own page and share card, and `make_post.py <key>` prints the reply to paste back into the group. `asked_new.py` opens a question (draft entry + note); `asked_check.py` checks its records' links and provenance before the draft flag comes off. `make_handouts.py` — the printed A4s into `assets/handouts/`, same reason plus Shan. `importers/` — everything that touches the network, run deliberately, never during a build. `data/curated/` — hand-kept field truth that no importer may overwrite. `data/config.json` — the channels. `worker/` — the Cloudflare Worker that takes claims.

The build makes no external request — keep that true; `importers/` is where the network lives, run deliberately and never during a build. Published pages make no external request either, with one exception: a page carrying a map fetches the basemap (tiles from our own bucket, label glyphs from Protomaps). `map_shell.py` is the only module that may configure that, and adding a second place tiles are set up is the thing to refuse. No page, map or not, ever reports a reader to anybody.
