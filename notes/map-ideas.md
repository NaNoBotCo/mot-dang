# What else the map data can do

Drawn 2026-07-31, the day after `data/road_graph.json` landed. The graph — 9,767
junctions, 12,280 edges, foot and ride flags with the one-way asymmetry — feeds
exactly one page (`plan.html`). Most of this list is the rest of what it can
carry, plus the analyses the 10,463 place records already support.

Ranked. Nothing here is committed except what the tasks say is in progress. Each
entry names the data it stands on, so a future ant can tell a cheap idea from an
expensive one without re-deriving it.

**One constraint binds everything below** — and the other one is gone.

~~The site publishes no external scripts, fonts or tiles, so every map is either
an inline SVG drawn in Python at build time or client JS over a baked JSON file
— no Leaflet, no tile server, ever.~~ **Superseded 2026-08-12.** The site now
ships a real basemap: one 116 MB `.pmtiles` archive covering both provinces at
z0–15, served from our own bucket, rendered by vendored MapLibre. `map_shell.py`
is the only place a map is constructed or a tile configured. The drawn SVGs all
survive as the layer that prints, works with scripting off, and fills the box
before the tiles arrive — so ideas below that assume a drawn map still hold;
they simply get ground underneath them now. Ideas that were **ranked low purely
because a basemap was impossible are worth re-reading** — that was the binding
constraint on half this list, not a judgement about the idea.

The real constraint that remains: the road crawl covers the CM old city plus roughly a 2 km ring
(18.7567–18.8253 N, 98.9533–99.0170 E), which holds **5,676 of 10,463 places,
54%, all of them cm**. Chiang Rai has no road network at all yet. Anything that
routes is bounded by that box until somebody says crawl more.

---

## Tier 1 — the road graph, nothing new to fetch

**1. Walk-time bands on every place page.** Dijkstra out from each place's
snapped node, cut at 5 / 10 / 15 minutes on foot and by scooter, rendered as the
set of reachable edges. Deliberately not a radius: the moat and the one-way ring
are exactly what make a circle lie, and showing the true shape is the argument
for having built the graph. Turns 10,463 pages that each end in themselves into
a network. Bounded to the box; outside it, straight-line with the fact stated.

**2. ซอย pages.** *In progress — see tasks 2–4.* The tagline is รู้ทุกซอย and
there is no soi tier. The rung between ตำบล and place.

**3. ไหว้พระ ๙ วัด — generated merit routes.** The wat shelf, plus
`data/curated/honours.json` royal grades, plus the graph, plus `fortune.json`'s
พระประจำวันเกิด. Walkable and rideable nine-wat loops per district, and a
variant keyed to the reader's birth weekday. A practice people already do at new
year and Songkran, shareable to LINE as a poster. Aimed at ป้าร้านกะเพรา and the
temple steward, not at the farang reader. From the empathy map: the page does
not rank temples against each other — a route is an order of walking, not a
ranking, and the page has to make that plain.

**4. One-trip errand solver.** `plan.html` routes stops that are already chosen.
The version nobody else offers: give it *categories* — ร้านยา, ตู้เอทีเอ็ม,
ส้มตำ — and let it choose which instances make the shortest single loop, rather
than the nearest of each picked independently.

**5. "Thirty metres behind you is a lap away."** Shade the ring road by ride-cost
to a point you can see from where you stand. The one-way asymmetry made visible;
the graph already encodes it as `flags`. Small, and the kind of thing that gets
shared.

## Tier 2 — analysis over the catalog

**6. Ant rank by ตำบล.** Mean completeness per subdistrict, shaded. Gives
claiming a geographic pull — "ซอยนี้ 2/9" — and pairs with `next_ant()`, which
already turns a score into an instruction. Needs subdistrict on the records,
which task 2 supplies.

**7. Coverage map.** Grid both provinces, count records per cell, show where the
ants have not walked yet. Self-audit, crawl-request targeting, and a picture
worth publishing, in one. Label it in the existing 🐜 มดกำลังไปเก็บ register —
this is where the site is growing, not where it is empty.

**8. The geography of the 47%.** `data/linkhealth.json` already establishes that
278 of 594 real websites do not answer. Nobody has mapped *where* businesses stop
answering. Same genre as `/reach.html`, and a finding about these two cities that
does not exist elsewhere.

**9. Emergent areas.** Cluster the points by density and let Nimman, Santitham,
Chang Klan, Wualai fall out as discovered areas with measured edges, instead of
asserting boundaries. Desire-path folksonomy, same method as the category tree.

**10. What clusters with what.** Category adjacency across 10,463 points — where
tattoo actually concentrates, whether ร้านยา really sit near clinics. Produces
"the massage strip" as a measurement rather than a claim.

**11. The year as a map.** 33 festivals × month × province, plus the events
layer: where the city's attention moves through the year. Yi Peng on the water,
Songkran on the ring, Inthakhin at Chedi Luang.

**12. Printable soi sheets.** `make_handouts.py` already renders PDFs through
headless Chrome. One page, one tambon or one soi, numbered pins, a QR per place —
something a guesthouse counter or a wat notice board can hold. Check the embedded
font before printing: the sheets take whatever face the rendering machine has,
and a Mac without Noto Sans Thai silently drops to Arial Unicode MS.

## Needs a small crawl first (ask before fetching)

- Roads for Chiang Rai, and for CM beyond the 2 km ring. Everything in Tier 1 is
  capped at 54% of the catalog until this happens.
- Songthaew and red-truck corridors — worth checking what OSM actually holds
  before assuming.
- ATMs, public toilets, drinking water as their own layer.
- OSM `sidewalk` and `surface` tags are already in `cache/roads` (5,609 ways
  carry `surface`, 527 carry `sidewalk`) — no new crawl needed to let walk times
  reflect whether there is anywhere to walk. Cheaper than it looks.

## Needs data we do not have

Elevation for the Doi Suthep gradients (SRTM), flood extents, bus timetables. A
source would have to be found and verified before any of these is designed —
none should be guessed at.
