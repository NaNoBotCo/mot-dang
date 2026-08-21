#!/usr/bin/env python3
"""มดแดง Mot Dang → a Hugging Face dataset repo.

The site already hands machines llms-full.txt: every place, one line, nothing
to strip. This does the same job for the other kind of reader — the one that
wants a typed column it can filter on rather than a line it has to split.

Same records, same ant rank, same licence. The helpers come from build.py by
import rather than by reimplementation, so the dataset cannot quietly drift
away from what the pages say.

Writes publish/hf-dataset/ — a complete dataset repo, ready to push. Pushing
is a separate, human step; see the README this leaves behind.

    python3 publish/make_hf_dataset.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402  — the site's own helpers, so the two agree

OUT = ROOT / "publish" / "hf-dataset"
REPO_ID = "NaNoBotCo/mot-dang-chiang-mai-chiang-rai"

# Channels are published exactly as llms-full.txt publishes them — same kinds,
# same values. A place's e-mail is already one fetch away at motdang.net; a
# second copy here that quietly dropped fields would only make the two
# disagree, and disagreeing with yourself is worse than either choice.
CHANNEL_PARITY_WITH = "llms-full.txt"

# attrs carries 101 different keys across the corpus — a wat has a register
# code and a wisung date, a noodle shop has a cuisine and a wifi fee. Forcing
# that into columns would give every row ninety-odd empty ones, so it travels
# as a JSON string and the card says so.
ATTRS_AS_JSON = True


def clean(v):
    """One line, always.

    Two records carry a newline inside a value, straight out of OSM — a hotel
    whose name is split across two lines and a market whose hours are. JSON
    would escape them and survive, but the value is still wrong: the hotel is
    called one thing, not two. Collapsed here rather than in data/canonical/,
    because the fix belongs upstream in the map and this is only a reader.
    """
    if not isinstance(v, str):
        return v
    return " ".join(v.split()) or None


def rows():
    """Every place, in the order the site holds them.

    Through build.load(), not by reading data/canonical/ directly: the loader
    runs enrich() over every record, and skipping it put this export one ant
    behind the site on 89 places. Same door as the pages use, or the two drift.
    """
    data = build.load()
    for prov in ("cm", "cr"):
        for r in data[prov]:
            live, _ = build.channels(r)
            bits = build.ant_bits(r)
            srcs = r.get("sources") or []
            attrs = r.get("attrs") or {}

            yield {
                "id": r["id"],
                "url": f"{build.BASE}{r['province']}/p/{build.place_slug(r)}.html",
                "province": r["province"],

                # Thai first, because that is how the place is called where it
                # stands. name_en is the label for someone who cannot read it.
                "name": clean(r.get("name")),
                "name_th": clean(r.get("nameTh")),
                "name_en": clean(r.get("nameEn")),

                "categories": list(r.get("cat") or []),
                "subcategories": list(r.get("sub") or []),

                "lat": r.get("lat"),
                "lng": r.get("lng"),
                "geo_precision": r.get("geoPrecision") or None,

                "address": clean(r.get("address")),
                "phone": clean(r.get("phone")),
                "website": clean(r.get("website")),
                "hours": clean(r.get("hours")),
                "channels": [{"kind": c["kind"], "value": clean(c["text"]) or ""}
                             for c in live],

                # The whole scoring system, readable: nine things that make a
                # listing useful to someone standing in the street, and which
                # of them this record has. No weighting, nothing hidden.
                "ant_rank": build.ant_rank(r),
                "ant_max": build.ANT_MAX,
                "ant_bits": [k for k, v in bits.items() if v],

                "featured": bool(r.get("featured")),
                "landmark": bool(r.get("landmark")),
                "blurb_th": clean(r.get("blurb_th")),
                "blurb_en": clean(r.get("blurb_en")),

                "confidence": r.get("confidence") or None,
                "source_types": sorted({s.get("type") for s in srcs if s.get("type")}),
                "sources": [{"type": s.get("type") or "",
                             "ref": s.get("ref") or "",
                             "fetched": s.get("fetched") or ""} for s in srcs],

                # The licence line splits on exactly this: fields that came off
                # the map are ODbL, the compilation around them is CC BY. A
                # column beats a paragraph — anyone reusing this can filter on
                # it instead of guessing which rows carry the obligation.
                "osm_derived": any(s.get("type") == "osm" for s in srcs),

                "attrs": json.dumps(attrs, ensure_ascii=False, sort_keys=True) if attrs else None,
                "updated_at": r.get("updatedAt") or None,
            }


def main():
    (OUT / "data").mkdir(parents=True, exist_ok=True)

    recs = list(rows())
    with (OUT / "data" / "places.jsonl").open("w", encoding="utf-8") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    n = len(recs)
    n_osm = sum(1 for r in recs if r["osm_derived"])
    n_pinned = sum(1 for r in recs if r["lat"] is not None)
    n_cm = sum(1 for r in recs if r["province"] == "cm")
    cats = {}
    for r in recs:
        for c in r["categories"]:
            cats[c] = cats.get(c, 0) + 1
    ants = {}
    for r in recs:
        ants[r["ant_rank"]] = ants.get(r["ant_rank"], 0) + 1

    (OUT / "README.md").write_text(card(n, n_cm, n_osm, n_pinned, cats, ants))
    (OUT / "LICENSE").write_text(licence_text())

    print(f"wrote {OUT}")
    print(f"  data/places.jsonl   {n:,} records "
          f"({n_cm:,} Chiang Mai / {n - n_cm:,} Chiang Rai)")
    print(f"  README.md           dataset card")
    print(f"  LICENSE             CC BY 4.0 compilation + ODbL map-derived")
    print()
    print(f"  {n_osm:,} rows carry osm_derived=true; {n_pinned:,} have coordinates")
    print()
    print("  not pushed. to push, from this directory:")
    print(f"    huggingface-cli upload {REPO_ID} . --repo-type=dataset")


def cat_table(cats):
    return "\n".join(f"| `{k}` | {v:,} |" for k, v in
                     sorted(cats.items(), key=lambda kv: -kv[1]))


def ant_table(ants):
    return "\n".join(f"| {k}/9 | {ants.get(k, 0):,} |" for k in range(9, -1, -1))


def licence_text():
    return f"""มดแดง Mot Dang — Chiang Mai & Chiang Rai city directory
{build.BASE}

THE COMPILATION — the selection, the categories, the ant rank, the Thai and
English blurbs, the field-collected fields, and the arrangement of all of it:

    Creative Commons Attribution 4.0 International (CC BY 4.0)
    https://creativecommons.org/licenses/by/4.0/

MAP-DERIVED FIELDS — anything that came out of OpenStreetMap, which is to say
most coordinates, addresses, and OSM tags. Rows carrying these are flagged
`osm_derived = true`:

    © OpenStreetMap contributors, Open Database License (ODbL) 1.0
    https://opendatacommons.org/licenses/odbl/1-0/

    ODbL is share-alike on the database. If you publish a derived database
    built on these rows, that database carries ODbL too.

PHOTOS are not in this dataset. Where a record references an external photo it
does so by URL only, in `attrs.photoRefExternal`; that photo's own licence is
its own affair and is not granted here.

Attribution to {build.BASE} is all we ask.
"""


def card(n, n_cm, n_osm, n_pinned, cats, ants):
    return f"""---
license: other
license_name: cc-by-4.0-compilation-odbl-1.0-map-fields
license_link: LICENSE
language:
  - th
  - en
pretty_name: "มดแดง Mot Dang — Chiang Mai & Chiang Rai City Directory"
size_categories:
  - 10K<n<100K
task_categories:
  - text-retrieval
  - question-answering
tags:
  - thailand
  - chiang-mai
  - chiang-rai
  - lanna
  - geospatial
  - openstreetmap
  - local-search
  - directory
  - thai
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/places.jsonl
---

# มดแดง Mot Dang — Chiang Mai & Chiang Rai city directory

{n:,} places in and around Chiang Mai ({n_cm:,}) and Chiang Rai ({n - n_cm:,}),
in Thai and English, with coordinates, categories, opening hours, and the
channels a place actually answers on — phone, LINE, Facebook, a website that
still resolves.

The name is มดแดง, *mot daeng*, the red ant: the thing that knows every soi
because it has walked all of them. That is the ambition. The directory exists
because mainstream mapping is thin here in ways that matter — a clinic with no
hours, a market under a name nobody local uses, a wat with the wrong spelling
and no Thai at all — and thin data is worst for the person who most needs it
to be good.

Live at {build.BASE} · built {build.BUILD_DATE}

## What is in a row

| field | type | what it is |
|---|---|---|
| `id` | string | stable identifier |
| `url` | string | the place's own page on {build.BASE.rstrip('/').replace('https://', '')} |
| `province` | string | `cm` (Chiang Mai) or `cr` (Chiang Rai) |
| `name` `name_th` `name_en` | string | as called on the ground; Thai is primary |
| `categories` `subcategories` | list[string] | see the table below |
| `lat` `lng` | float | null where the place is known but not yet pinned |
| `geo_precision` | string | `exact`, `block`, `approx`, `needs-pin` |
| `address` `phone` `website` `hours` | string | hours in OSM syntax (`Mo-Sa 09:00-17:30`) |
| `channels` | list[{{kind, value}}] | phone, web, facebook, instagram, email, line, whatsapp |
| `ant_rank` `ant_max` `ant_bits` | int, int, list | completeness — see below |
| `featured` `landmark` | bool | editorial flags |
| `blurb_th` `blurb_en` | string | written where a place needed explaining |
| `confidence` | string | `curated`, `field`, `crawled`, `third-party` |
| `source_types` `sources` | list | provenance per record, with fetch dates |
| `osm_derived` | bool | **true = this row carries ODbL.** See Licence |
| `attrs` | string (JSON) | 101 possible keys; a wat has `watCode`, a shop has `cuisine` |
| `updated_at` | string | ISO date |

`attrs` is a JSON string rather than a column per key, because the key set is
wide and sparse — a temple's register code and a noodle shop's wifi fee do not
belong in the same schema. Parse it if you need it.

## Ant rank

Nine things make a listing useful to someone standing in the street holding a
phone. Each one present earns an ant. The count is the whole scoring system —
no weighting, no secret sauce, nothing an owner cannot read off the page and
go fix themselves:

Thai name · English name · phone · LINE · opening hours · a website that still
answers · a photo · owner-confirmed · recently walked (within 180 days).

`ant_bits` lists which of the nine this record has, so you can filter on the
specific gap rather than the total.

| ant rank | places |
|---|---|
{ant_table(ants)}

A low rank is a to-do, not a judgement. Most of the corpus came off the map
and has never been walked.

## Categories

| category | places |
|---|---|
{cat_table(cats)}

## Where it came from

| confidence | meaning |
|---|---|
| `crawled` | from OpenStreetMap, unwalked |
| `third-party` | from a public directory, credited in `sources` |
| `curated` | written or corrected by hand against a source |
| `field` | someone stood in front of it |

{n_osm:,} of {n:,} rows are OSM-derived. {n_pinned:,} have coordinates; the
rest are known to exist but not yet pinned, and are marked `needs-pin` rather
than dropped — a clinic you cannot yet put on a map is still a clinic.

Every record carries its own `sources` with fetch dates. Provenance is
per-field and per-record, not a blanket statement at the bottom of a page.

## Known limits

- **Coverage is uneven by design.** Food and lodging are dense because that is
  what gets mapped; repair shops, community groups and home services are thin
  because they are not.
- **Most of it is unwalked.** `confidence: crawled` means the map said so and
  nobody has been to check. Opening hours especially go stale.
- **Prices are not in this dataset.** Where the site shows a price it is
  stamped with when it was seen, and that belongs on the page, not in a column
  that would be wrong within a season.
- **Photos are not here** — only external references, by URL, in `attrs`.
- **This is a directory, not a review site.** There are no ratings and no
  ranking by quality, only by completeness of the record.

## Licence

Dual, and the split is mechanical — filter on `osm_derived`:

- **The compilation** — selection, categories, ant rank, blurbs, field-collected
  fields, and the arrangement: **CC BY 4.0**.
- **Map-derived fields**, on rows where `osm_derived = true`: **© OpenStreetMap
  contributors, ODbL 1.0**. ODbL is share-alike on the database — publish a
  derived database from these rows and that database carries ODbL too.

{build.LICENSE_LINE_EN}

Full text in [LICENSE](LICENSE).

## Citation

```bibtex
@misc{{motdang{build.BUILD_DATE[:4]},
  title  = {{{{มดแดง Mot Dang: a Chiang Mai and Chiang Rai city directory}}}},
  author = {{{{Mot Dang}}}},
  year   = {{{build.BUILD_DATE[:4]}}},
  url    = {{{build.BASE}}},
  note   = {{{n:,} places, built {build.BUILD_DATE}}}
}}
```

## Also served directly

- `{build.BASE}llms.txt` — what the site is, for a machine arriving cold
- `{build.BASE}llms-full.txt` — the same {n:,} places as plain lines, one each
- Corrections: every page has a door. If a row here is wrong, the fix goes in
  at the source and lands in the next build.
"""


if __name__ == "__main__":
    main()
