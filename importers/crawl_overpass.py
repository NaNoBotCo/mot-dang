#!/usr/bin/env python3
"""Slow, soft-footed Overpass crawl for empty shelves, one province at a time.

Manners first: snapshot-first (nothing is fetched if a cache file exists),
one query at a time, a long pause between queries, generous server timeout,
an identified User-Agent, and rests-with-mirror-rotation on 429/504. Run with
--fetch to (re)download a province; without it, only missing cache files fetch.

  python3 importers/crawl_overpass.py             # CM: fetch only what's missing
  python3 importers/crawl_overpass.py --fetch     # CM: refresh everything (slow, on purpose)
  python3 importers/crawl_overpass.py cr          # CR: fetch only what's missing
  python3 importers/crawl_overpass.py cr --fetch  # CR: refresh everything

Cache: cache/overpass/<province>/<group>.json — import_all.py folds these in.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
# The contact URL is the live site — the repository link it used to carry
# went dead when the account was hidden (the No-GitHub rule reaching the one
# string it had missed), and a server operator who looks a crawler up should
# find a working page.
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle one-off harvest)"
PAUSE = 12                          # seconds between queries — slower and more subtle
RETRY_PAUSE = 45

BBOX = {
    "cm": "18.60,98.80,19.05,99.15",   # Mueang Chiang Mai and the near ring
    "cr": "19.80,99.70,20.00,99.95",   # Mueang Chiang Rai and the near ring
}

# Some things are too few, and too far apart, to be found in a ring round the
# provincial capital. A coach terminal at Mae Sai, the Mekong piers at Chiang
# Saen and Chiang Khong, an airport out past the ring road — each is a real
# destination and there are a handful of them in a whole province, so asking
# province-wide costs a few queries and no manners. Restaurants and
# hairdressers stay in the near ring, where the density would be unkind to
# Overpass and to a reader.
#
# THE AREA, NOT A RECTANGLE. Chiang Rai's bounding box is not Chiang Rai: the
# province is wedged against Laos and Myanmar, and a rectangle drawn round it
# caught Bokeo International Airport and the Houayxay speedboat pier (Laos),
# the Tha Ton boat landing (Mae Ai, which is Chiang Mai), and the pier out to
# Wat Tilok Aram (Kwan Phayao, which is Phayao). Filing any of those under
# "Chiang Rai" would be a plain falsehood about somebody else's province or
# somebody else's country. ISO 3166-2 names the administrative area exactly and
# in no particular language, so that is what we ask for.
PROVINCE_AREA = {
    "cm": "TH-50",   # เชียงใหม่ Chiang Mai
    "cr": "TH-57",   # เชียงราย Chiang Rai
}
# province-wide in EVERY province, Chiang Mai's near ring included.
# `schools` joined them on 2026-08-18: the OBEC register names schools in
# Omkoi, Mae Chaem, Fang and Chiang Dao, all of them far outside the ring, and
# a shelf that carried the state's record for a village school while the crawl
# had never been allowed to look for it would be lopsided in the one direction
# this site cares about most.
# `reading` and `making` joined on 2026-08-18 (WO-10), and for both the near
# ring is exactly the wrong shape:
#   ห้องสมุดประชาชนอำเภอ — the district public library — is ONE PER อำเภอ by
#   construction. A box drawn round the clock tower can only ever hold Mueang's,
#   which is why the shelf reads as Chiang Mai University's internal libraries.
#   The craft villages are villages: บ้านถวาย in Hang Dong, บ่อสร้าง and the silk
#   weavers out past San Kamphaeng, the kilns at Hang Dong. Ban Tawai and Bo
#   Sang sit within a few hundredths of a degree of the CM box edge, which is
#   luck, not coverage, and anything past San Kamphaeng town falls outside it.
# `elephants` joined on 2026-08-20 (WO-19, Nan's go): the camps are in Mae
# Taeng, Mae Wang, Mae Chaem and Chiang Dao — all of them far outside the near
# ring, which is exactly why a directory of 16,268 records held not one of
# them. A near-ring ask for elephant camps would be asking the moat.
# `hotsprings` joined on 2026-08-20 (WO-23, Nan's go): the springs are in Mae
# On, Mae Taeng, Chiang Dao, Fang, Wiang Pa Pao, Mae Chan and Phan — a spring
# is where the ground made it, which is never the near ring. Seven of the
# eight belong to whole districts the box has never seen.
WIDE_GROUPS = {"stations", "cannabis", "medical", "schools", "reading", "making",
               "elephants", "hotsprings", "views",
               # WO-27: all three residential/government doors are province-
               # wide. The Land Office branches are in the amphoes, Mae Jo's
               # dorms are outside Chiang Mai's near ring, and a housing
               # estate is suburban by definition — a ring drawn round the
               # moat would miss the whole point of each.
               "government", "dormitory", "moobaan"}

# Provinces crawled province-wide for every group. Chiang Rai is here on Nan's
# instruction: a directory that only knows Mueang is not a directory for
# Chiang Rai. Mae Sai, Mae Chan, Chiang Saen, Chiang Khong, Thoeng, Phan,
# Wiang Pa Pao and Mae Salong are where much of the province actually lives and
# works, and they were outside a box drawn round the clock tower.
#
# Chiang Mai stays on its near ring for now: it is far denser, the ring already
# holds 9,075 records, and widening it is a much larger crawl that deserves its
# own decision rather than being carried in on Chiang Rai's coat-tails.
WIDE_PROVINCES = {"cr"}


def is_wide(province, group):
    return province in PROVINCE_AREA and (province in WIDE_PROVINCES
                                          or group in WIDE_GROUPS)

QUERIES = {
    "hotels":     ['nwr["tourism"="hotel"]', 'nwr["tourism"="guest_house"]',
                   'nwr["tourism"="hostel"]'],
    "markets":    ['nwr["amenity"="marketplace"]', 'nwr["shop"="mall"]',
                   'nwr["shop"="department_store"]'],
    # Every school, not only the ones a foreigner was expected to want.
    #
    # This group used to read `amenity=school` with a name filter of
    # International|นานาชาติ, and that one regex is why a directory for two
    # provinces held FOURTEEN schools. The census (cache/census/, taken
    # 2026-08-07) counts 469 amenity=school in TH-50 and 301 in TH-57: around
    # 800 ordinary schools were never once asked for. A village school in
    # Omkoi is not less of a place than Prem International, and the register
    # (importers/import_obec.py) names 1,302 of them in these two provinces,
    # so leaving the crawl narrow would have meant importing state records for
    # schools our own crawl was still refusing to see.
    #
    # The name filter is gone. The rest of the education family comes with it:
    # counts in the census are kindergarten 41/18, college 20/8, university
    # 72/5, prep_school 3/8 (กวดวิชา, the tutoring shops), training 46/–,
    # language_school 6/5, music_school 5/5, driving_school 5/3, childcare 6/4,
    # office=educational_institution 21/4.
    #
    # sports_centre and dance are here rather than in `fitness` because that
    # group asks only for leisure=fitness_centre, which left 48 CM sports
    # centres uncrawled — and a ค่ายมวย is tagged sports_centre far more often
    # than it is tagged anything else. sport=muay_thai is asked for on its own
    # because the tag is how a camp says so in its own words; if it comes back
    # empty the false-zero recheck in fetch_wide() will ask a second time
    # before believing it.
    #
    # Libraries are deliberately NOT here. A library is a place to learn and it
    # belongs on this site, but it is not a school, and a shelf that has just
    # gone from 14 records to well over a thousand should not also be the place
    # that quietly decides what a library is. Its own group, its own decision.
    "schools":    ['nwr["amenity"="school"]',
                   'nwr["amenity"="university"]',
                   'nwr["amenity"="college"]',
                   'nwr["amenity"="kindergarten"]',
                   'nwr["amenity"="childcare"]',
                   'nwr["amenity"="prep_school"]',
                   'nwr["amenity"="language_school"]',
                   'nwr["amenity"="music_school"]',
                   'nwr["amenity"="driving_school"]',
                   'nwr["amenity"="training"]',
                   'nwr["office"="educational_institution"]',
                   'nwr["leisure"="sports_centre"]',
                   'nwr["leisure"="dance"]',
                   'nwr["sport"="muay_thai"]'],
    "realestate": ['nwr["office"="estate_agent"]', 'nwr["building"="apartments"]["name"]'],
    "transport":  ['nwr["amenity"="fuel"]', 'nwr["amenity"="car_rental"]',
                   'nwr["shop"="motorcycle_rental"]', 'nwr["amenity"="bus_station"]',
                   'nwr["railway"="station"]'],
    # Terminals, in their own group so it can be fetched without disturbing the
    # rest of `transport`. `transport` asked only for amenity=bus_station and
    # railway=station, which left out every airport in both provinces — the
    # directory's only "Airport" records are a petrol station and a hotel with
    # the word in their names, and a landmark list built by name-matching
    # happily pinned one of them. An aerodrome is also exactly the kind of
    # place /toilets.html is asked about at midnight.
    #
    # Nameless is skipped at import anyway, so ["name"] where a nameless hit
    # would be noise (an aerodrome polygon, a pier) and left off where the
    # feature is worth having even bare (a bus station).
    "stations":   ['nwr["aeroway"="aerodrome"]["name"]',
                   'nwr["aeroway"="terminal"]["name"]',
                   'nwr["amenity"="bus_station"]',
                   'nwr["public_transport"="station"]["name"]',
                   'nwr["railway"="station"]', 'nwr["railway"="halt"]["name"]',
                   'nwr["amenity"="ferry_terminal"]["name"]',
                   'nwr["amenity"="taxi"]["name"]'],
    "repair":     ['nwr["shop"="car_repair"]', 'nwr["shop"="motorcycle_repair"]',
                   'nwr["shop"="computer"]', 'nwr["shop"="mobile_phone"]'],
    # WO-22, widened 2026-08-21 on Nan's go. Two selectors held this group from
    # the first crawl, and between them they cannot see the trades she actually
    # asked after. `hairdresser_supply` is where extensions and wigs are SOLD
    # (a different shop from the one that fits them, and the shop that knows
    # who does); `wig` is its own tag; `craft=hairdresser` is how a stylist
    # working out of their own front room gets mapped, which is the closest
    # thing OSM has to the house-call question. `cosmetics` is queried to close
    # the question rather than in hope — ร้านเครื่องสำอาง is retail, not a chair,
    # and nothing is filed from it unless the answer says otherwise.
    #
    # ANSWERED 2026-08-21, and the answer is worth keeping so nobody re-runs
    # this experiment hoping for a different one:
    #     hairdresser_supply   0 in CM, 0 in CR (asked twice each)
    #     wig                  0 in CM, 0 in CR (asked twice each)
    #     craft=hairdresser    0 in CM, 0 in CR (asked twice each)
    #     cosmetics           33 in CM, 8 in CR — and NOT filed, see below
    # Zero new hair shops of any kind. The extension-and-wig supply trade and
    # the stylist working from her own front room are simply not in
    # OpenStreetMap here, so the house-call and extensions questions cannot be
    # answered by crawling at all — only by a shop stating it or a person
    # asking at a door. That is a question closed, not a crawl that failed.
    #
    # The cosmetics haul is deliberately left in the cache and filed NOWHERE.
    # ร้านเครื่องสำอาง is retail, not a chair, and this shelf is called
    # เสริมสวย-ทำผม; putting 41 shops that sell lipstick on it would break the
    # promise the shelf's own name makes. The answer also came back dirty —
    # more than half unnamed, and several are massage venues wearing a
    # cosmetics tag ("Sense Massage & Spa", "massage by ex-prisoners", "Jera
    # Thai massage school"), which would have arrived as name-duplicates of
    # places the massage group already holds. If a cosmetics shelf is ever
    # wanted it belongs under shopping, as its own decision.
    "beauty":     ['nwr["shop"="hairdresser"]', 'nwr["shop"="beauty"]',
                   'nwr["shop"="hairdresser_supply"]', 'nwr["shop"="wig"]',
                   'nwr["shop"="cosmetics"]', 'nwr["craft"="hairdresser"]'],
    "pets":       ['nwr["amenity"="veterinary"]', 'nwr["shop"="pet"]',
                   'nwr["shop"="pet_grooming"]'],
    "fitness":    ['nwr["leisure"="fitness_centre"]'],
    "essentials": ['nwr["amenity"="bank"]', 'nwr["amenity"="post_office"]',
                   'nwr["shop"="convenience"]', 'nwr["amenity"="townhall"]'],
    # WO-27 door 2. The government offices, and the reason is one of them:
    # the catalogue held ZERO สำนักงานที่ดิน while every chanote transfer in
    # the north walks through one. `amenity=townhall` was the only government
    # selector this crawl ever had, and a Land Office is not a townhall.
    # Province-wide (WIDE_GROUPS) because the branch offices are in the
    # amphoes — a สาขา in Hang Dong or Mae Rim is exactly where the transfer
    # for a house out there happens. Named only: an unnamed government
    # polygon tells a reader nothing and is skipped at import anyway.
    "government": ['nwr["office"="government"]["name"]'],
    # WO-27 door 4. Student housing that OSM tags on the BUILDING rather than
    # in the name — the dorm shelf could otherwise only ever hold the ones
    # that wrote หอพัก on the sign. One selector, one run, and the question
    # is closed either way.
    "dormitory": ['nwr["building"="dormitory"]["name"]'],
    # WO-27 door 3. Named residential areas — the housing estates, IF they
    # are here at all. FENCED HARD at import (import_overpass.moobaan_hit):
    # in this province a named residential area is nearly always a village,
    # and filing somebody's village as a gated development is a falsehood
    # about where they live. Only จัดสรร or a developer's own name files;
    # the rest goes to cache/moobaan_review_<prov>.txt for a person to read.
    "moobaan": ['nwr["landuse"="residential"]["name"]'],
    "culture":    ['nwr["tourism"="museum"]', 'nwr["tourism"="gallery"]',
                   'nwr["tourism"="viewpoint"]', 'nwr["historic"]["name"]'],
    "shopping":   ['nwr["shop"="doityourself"]', 'nwr["shop"="hardware"]',
                   'nwr["shop"="gift"]', 'nwr["shop"="second_hand"]',
                   'nwr["shop"="herbalist"]', 'nwr["healthcare"="alternative"]'],
    "cafes":      ['nwr["amenity"="cafe"]'],
    "restaurants": ['nwr["amenity"="restaurant"]', 'nwr["amenity"="fast_food"]',
                    'nwr["amenity"="food_court"]', 'nwr["amenity"="bar"]',
                    'nwr["amenity"="pub"]', 'nwr["amenity"="biergarten"]',
                    'nwr["shop"="bakery"]', 'nwr["amenity"="ice_cream"]'],
    "whats-on":   ['nwr["amenity"="cinema"]', 'nwr["amenity"="music_venue"]',
                   'nwr["amenity"="events_venue"]', 'nwr["amenity"="theatre"]'],
    # Parks were never queried, which is why the directory had none. The 31
    # "park" hits in the data were all false positives from names — "Royal
    # Orchid Park Hotel", "Near the park Backpack hostel". Named features only:
    # an unnamed patch of grass is not a place anyone looks up.
    "parks":      ['nwr["leisure"="park"]["name"]', 'nwr["leisure"="garden"]["name"]',
                   'nwr["leisure"="nature_reserve"]["name"]',
                   'nwr["boundary"="national_park"]["name"]',
                   'nwr["leisure"="playground"]["name"]', 'nwr["natural"="water"]["name"]'],
    # 41 tattoo records were sitting in 'sights' with no rule; crawl them properly.
    "tattoo":     ['nwr["shop"="tattoo"]', 'nwr["shop"="piercing"]'],
    # WO-21, Nan's go 2026-08-21. The viewpoint shelf read CM 31 / CR 74, and
    # the imbalance was this file's geometry rather than the two provinces:
    # CR is in WIDE_PROVINCES and was asked province-wide, while `culture` —
    # which is where tourism=viewpoint has always lived — has only ever been
    # asked on Chiang Mai's near ring. The views of Chiang Mai are on the doi
    # by construction, so the near ring is the one place they cannot be. Same
    # shape as the elephants: a near-ring ask for a mountain viewpoint is
    # asking the moat.
    #
    # Waterfalls and peaks have NEVER been asked for by any group, in either
    # province. The famous falls only reached the catalogue at all because
    # WO-19's attraction dragnet happened to catch them.
    #
    # Named only, for the two natural features: an unnamed contour bump is
    # not a place anyone looks up, and nameless is skipped at import anyway.
    # tourism=viewpoint keeps its bare form — a จุดชมวิว with no name is still
    # somewhere a mapper stood, and the same rule drops it downstream.
    "views":      ['nwr["tourism"="viewpoint"]',
                   'nwr["waterway"="waterfall"]["name"]',
                   'nwr["natural"="peak"]["name"]'],
    # Fixtures, not destinations. Nobody looks up an ATM by name, so these never
    # become directory records — import_fixtures.py joins them by distance onto
    # the shops they sit at. OSM maps an ATM as its own node beside the store,
    # almost never as a tag on it: of 385 7-Elevens in the snapshot, exactly one
    # carried amenity=atm. The neighbours are where the truth is.
    "fixtures":   ['nwr["amenity"="atm"]', 'nwr["amenity"="toilets"]',
                   'nwr["amenity"="vending_machine"]["vending"~"parcel|drinks"]'],
    # Three whole categories — home-services, community, business — were given
    # shelves at launch and never a query, so they have sat at zero ever since:
    # a reader saw "the ants are still collecting" where the truth was that no
    # ant was ever sent. These are the tags OSM actually uses for them here.
    # Named features only, on the same rule as parks: an unnamed craft=plumber
    # node is a dot on a map, not a tradesman anyone can ring.
    "crafts":     ['nwr["craft"]["name"]', 'nwr["shop"="laundry"]["name"]',
                   'nwr["shop"="dry_cleaning"]["name"]',
                   'nwr["shop"="garden_centre"]["name"]'],
    "community":  ['nwr["amenity"="community_centre"]["name"]',
                   'nwr["office"="ngo"]["name"]', 'nwr["office"="charity"]["name"]',
                   'nwr["office"="association"]["name"]',
                   'nwr["amenity"="social_facility"]["name"]', 'nwr["club"]["name"]'],
    # Doctors, and the shelf that had never been crawled either — which on this
    # site is the one that matters most. The 233 Chiang Mai medical records all
    # arrived from the cm-womens-health import, a women's-health slice rather
    # than a medical directory, and CHIANG RAI HAD THREE RECORDS for a whole
    # province. A person looking for a clinic at night was being shown a
    # directory that had never asked where the clinics are.
    #
    # Province-wide in both (see WIDE_GROUPS), and here that is not a nicety:
    # Chiang Rai's clinics are in Mae Sai, Mae Chan, Chiang Khong and Phan, and
    # Chiang Mai's district hospitals are in Hot, Doi Tao and Mae Taeng. A ring
    # round either clock tower is exactly the wrong shape for this shelf.
    #
    # `healthcare=*` is asked with ["name"] because the tag is also carried by
    # unnamed rooms inside hospitals, which are not places anyone looks up.
    "medical":    ['nwr["amenity"="clinic"]', 'nwr["amenity"="doctors"]',
                   'nwr["amenity"="hospital"]', 'nwr["amenity"="dentist"]',
                   'nwr["amenity"="pharmacy"]', 'nwr["healthcare"]["name"]'],
    # Cannabis and kratom, never asked for until now — which is why the whole
    # trade was invisible. 12,318 records held exactly three, and all three
    # were filed somewhere else: a dispensary under sights/historic, a
    # cannabis cafe under food/thai, a kratom shop under medical/thai-medicine.
    #
    # Province-wide in BOTH provinces (see WIDE_GROUPS). These are a few
    # hundred shops each, not thousands, and the Chiang Mai near-ring box stops
    # short of Mae Rim, Doi Saket, Chiang Dao and most of Hang Dong.
    #
    # `shop=cannabis` is the settled tag and carries most of the dispensaries.
    # The name patterns are here because kratom has no tag of its own at all:
    # a ร้านน้ำกระท่อม is mapped as shop=convenience, shop=yes, or nothing.
    #
    # THE HUT GUARD. Bare กระท่อม is not matched and must never be — it is the
    # ordinary word for a hut or a cottage, and every กระท่อมริมน้ำ resort in
    # two provinces would arrive as a kratom bar. Only the forms that name the
    # leaf or the drink: ใบกระท่อม, น้ำกระท่อม, ร้านกระท่อม, and the Latin
    # spellings. What the patterns still cannot settle — a noodle shop with
    # กัญชา in its name is a restaurant, not a dispensary — is settled at
    # import, in a review file, by a person.
    # `cannabis:cbd=yes` was the second selector here and is now gone: it
    # returned 0 across the whole of Chiang Mai, then spent six escalating
    # retries failing over Chiang Rai — a query nobody's data answers, asked
    # of a server that was already struggling. The tag exists in the wiki and
    # not in the ground here.
    # The trade-name selector is the last one and it earns its place. Shops here
    # are called Stash CDXX, Wake n' Bake, Cloud 9 — names that say cannabis to
    # a customer and nothing to a regex. Those only arrived because they carry
    # shop=cannabis; one tagged shop=yes is in NO group's selectors and is
    # invisible to every query we run.
    #
    # The vocabulary is short on purpose, and the short list was MEASURED, not
    # guessed: a wide net run offline over all 11,620 cached names returned
    # Bud's Ice Cream, Hot Pot Buffet, Green House Cafe, Puff & Pie and 22
    # grams coffee. `green`, `bud`, `high`, `pot`, `herb`, `smoke`, `bake` and
    # `puff` are ordinary words in a city full of cafes and are left out. What
    # is here is what a non-cannabis business would not call itself.
    "cannabis":   ['nwr["shop"="cannabis"]',
                   'nwr[~"^cannabis"~"."]["name"]',
                   'nwr["name"~"กัญชา"]',
                   'nwr["name"~"ใบกระท่อม|น้ำกระท่อม|ร้านกระท่อม"]',
                   'nwr["name"~"cannabis|dispensar|ganja|kratom|krathom|weed",i]',
                   'nwr["name"~"420|kush|sativa|indica|dispensary|stoner|'
                   'weedshop|budtender|pre-roll|preroll",i]'],
    # WO-19, 2026-08-20 (Nan's go). The elephant camps, never once asked for:
    # tourism=zoo, theme_park and attraction were in NO group, which is why the
    # busiest elephant country in the kingdom yielded zero camps from 16,268
    # records and the whole chang shelf had to enter from the venues' own
    # sites. The three tags are how OSM actually files a ปางช้าง — some map as
    # zoo, most as attraction. IMPORT IS FENCED: import_overpass.chang_hit()
    # takes only elephant-declaring names from this file; everything else this
    # dragnet catches (waterfalls, gardens, tiger parks, snake farms…) goes to
    # cache/elephant_review_<prov>.txt for a FUTURE attractions decision, never
    # onto a shelf by accident. attraction carries ["name"]: a nameless
    # attraction node is a mapping artifact, and the volume is in that
    # selector.
    "elephants":  ['nwr["tourism"="zoo"]', 'nwr["tourism"="theme_park"]',
                   'nwr["tourism"="attraction"]["name"]'],
    # WO-23, 2026-08-20 (Nan's go: "BIGLY … the whole north is ok"). The hot
    # springs, never once asked for: natural=hot_spring was in NO group, which
    # is why Chiang Mai — สันกำแพง, โป่งเดือด, เทพพนม, the Fang springs — held
    # zero of them in 12,951 records. amenity=public_bath is how the soaking
    # houses at a developed spring map themselves (fenced at import: a plain
    # public bath is a shower block, and files only when its bath:type or its
    # name says hot water). The name selectors reach springs mapped as
    # attraction or park or nothing at all; bare โป่ง is deliberately NOT in
    # them (บ้านโป่ง and โป่งแยง are villages), and IMPORT IS FENCED —
    # import_overpass.springs_hit() takes only spring-stating elements from
    # this file; schools, temples, villages and bus stops wearing a spring's
    # name go to cache/hotspring_review_<prov>.txt, never onto a shelf by
    # accident. harvest_hotsprings.py asks the SAME selectors across the
    # other fifteen ภาคเหนือ provinces for the register (one copy of both
    # lists — it imports them from here).
    "hotsprings": ['nwr["natural"="hot_spring"]',
                   'nwr["amenity"="public_bath"]["name"]',
                   'nwr["name"~"น้ำพุร้อน|น้ำพร้อน|บ่อน้ำร้อน|โป่งน้ำร้อน|'
                   'โป่งเดือด|ธารน้ำร้อน"]',
                   'nwr["name"~"hot ?spring|onsen",i]'],
    "business":   ['nwr["shop"="wholesale"]["name"]', 'nwr["shop"="trade"]["name"]',
                   'nwr["office"="coworking"]["name"]',
                   'nwr["amenity"="coworking_space"]["name"]',
                   'nwr["office"="lawyer"]["name"]',
                   'nwr["office"="accountant"]["name"]'],
    # WO-10, 2026-08-18. Libraries and bookshops, neither ever asked for.
    #
    # `amenity=library` was in no group, so the only libraries in the directory
    # are 20 lens points inherited from the mueang-map import — 17 of them CMU
    # faculty libraries, none with hours, a phone or a website, and NONE AT ALL
    # in Chiang Rai. `shop=books` and `shop=stationery` were in no group either
    # and the directory holds zero of both. That is the same failure this file
    # already records for home-services, community and business, one step worse:
    # bookshops were never even given the shelf to be empty on.
    #
    # The name selector is here for the reason the cannabis group's is — a shop
    # tagged shop=yes is invisible to every tag query we run — and the audit
    # found three stationery shops already in the corpus filed as a Thai
    # restaurant, a DIY store and a convenience store. Unlike the kratom
    # vocabulary these words need no guard: ร้านหนังสือ, เครื่องเขียน and ห้องสมุด
    # are compounds with no ordinary-word collision to trip over.
    "reading":    ['nwr["amenity"="library"]', 'nwr["shop"="books"]["name"]',
                   'nwr["shop"="stationery"]["name"]',
                   'nwr["shop"="newsagent"]["name"]',
                   'nwr["name"~"ร้านหนังสือ|เครื่องเขียน|ห้องสมุด"]'],
    # WO-10. The crafts, where the existing `crafts` group asks only craft=*
    # plus laundry and garden centres, and the craft itself is recorded nowhere.
    #
    # THE FOUR ZEROS ARE THE ARGUMENT, and they were measured rather than
    # supposed: `importers/audit_culture.py` read all 85 records on the craft
    # shelf and found เครื่องเขิน (lacquer), แกะสลักไม้ (woodcarving), ตุงล้านนา
    # and จักสาน (basketry) at ZERO each — four Lanna crafts this city is known
    # for, and one of them, เครื่องเขิน, has a museum here. Ban Tawai, the
    # woodcarving village, is in the directory as `market/fresh`, a wet market,
    # and that one record is the whole village.
    #
    # Every Thai term below is a compound. Bare ตุง, เงิน, แกะ and ร่ม are all
    # ordinary words and none of them is asked for: ร่ม alone matches
    # รพ.สต. ร่มเกล้า, and วัวลาย is a ROAD as well as the silver quarter, so the
    # health stations along it are not evidence of silverwork. Same discipline
    # as the hut guard on กระท่อม above.
    #
    # shop=jewelry is deliberately NOT asked. It is carried here by the ร้านทอง
    # gold traders, which are on every high street and are a different trade;
    # craft=jeweller already reaches the makers through the `crafts` group.
    "making":     ['nwr["shop"="art"]["name"]', 'nwr["shop"="pottery"]["name"]',
                   'nwr["shop"="fabric"]["name"]',
                   'nwr["shop"="musical_instrument"]["name"]',
                   'nwr["shop"="antiques"]["name"]',
                   'nwr["name"~"เครื่องเขิน|แกะสลัก|จักสาน|ตุงล้านนา|กระดาษสา|'
                   'ศิลาดล|เครื่องเงิน|ผ้าทอ|ร่มบ่อสร้าง|หัตถกรรม"]',
                   'nwr["name"~"handicraft|celadon|lacquer|woodcarv|silversmith",i]'],
}


class OverpassRemark(Exception):
    """Overpass answered 200 with an error in `remark` and no elements.

    This is the failure that matters most here, because it does not look like
    one. A timed-out query returns a perfectly valid JSON document with an
    empty `elements` list, and the crawler used to write it to cache as though
    it were an answer — and since the crawl is snapshot-first, that empty file
    would never be retried. A shelf would simply be empty forever, with a
    cached file standing there as proof it had been asked.
    """


def fetch(group, selectors, scope, timeout=90):
    """`scope` is either a bbox string or ("area", <ISO 3166-2 code>)."""
    if isinstance(scope, tuple):
        pre = f'area["ISO3166-2"="{scope[1]}"]->.a;'
        clip = "(area.a)"
    else:
        pre, clip = "", f"({scope})"
    q = (f"[out:json][timeout:{timeout}];{pre}("
         + "".join(f"{s}{clip};" for s in selectors) + ");out center tags;")
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(6):
        api = APIS[attempt % len(APIS)]
        req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout + 60) as r:
                data = json.load(r)
            remark = data.get("remark") or ""
            if remark and not data.get("elements"):
                raise OverpassRemark(remark.strip())
            return data
        except Exception as e:
            last = e
            rest = RETRY_PAUSE * (attempt + 1)
            print(f"  {group}: {e} on {api.split('/')[2]} — resting {rest}s", flush=True)
            time.sleep(rest)
    raise last


def fetch_wide(group, selectors, scope, timeout=240):
    """One selector at a time, merged.

    A whole province in a single query is what timed out: eight selectors over
    Chiang Rai is more than Overpass will do in 90 seconds, and the answer came
    back empty with the error tucked in a `remark`. Split, each part is small
    and finishes; the pause between them is the same politeness the group loop
    already keeps.

    ONE SELECTOR MAY FAIL WITHOUT COSTING THE OTHERS. This used to raise, which
    meant the last query of a group timing out threw away every element the
    earlier ones had already fetched — an hour of somebody else's server time
    discarded because the sixth question was the expensive one. Now the failure
    is kept as `incomplete` in the returned document, so the data survives AND
    the file says out loud that it is short. Same reasoning as OverpassRemark:
    the thing to fear is not a failure, it is a cache file that looks whole.
    Only a group where EVERY selector failed still raises, because that is a
    group with nothing in it and no reason to be believed.
    """
    merged, seen, incomplete = [], set(), []
    zeros_confirmed, zeros_recovered = [], []
    for i, sel in enumerate(selectors):
        try:
            data = fetch(f"{group}[{i + 1}/{len(selectors)}]", [sel], scope, timeout)
        except Exception as e:
            incomplete.append({"selector": sel, "error": f"{type(e).__name__}: {e}"})
            print(f"    {sel} -> GAVE UP ({type(e).__name__}) — group marked "
                  f"incomplete, the other selectors stand", flush=True)
            if i < len(selectors) - 1:
                time.sleep(PAUSE)
            continue
        # A ZERO IS ASKED TWICE, because a silent zero looks exactly like a
        # real one. Overpass answers HTTP 200 with a valid document, an empty
        # `elements` list and NO `remark` — OverpassRemark cannot see it, and
        # the shrink guard below cannot either on a group's first fetch, since
        # there is nothing yet to compare against. It has now happened twice:
        # `shop=cannabis` over Chiang Mai went 28 -> 0 between two runs an hour
        # apart, and `amenity=clinic` over Chiang Rai returned 0 for a province
        # whose own health office counts 628 clinics.
        #
        # A genuine zero answers zero again and costs one query. A false zero
        # usually answers properly, and we keep the real number instead of
        # writing an empty shelf that would never be retried.
        n = len(data.get("elements", []))
        if n == 0:
            print(f"    {sel} -> 0 — asking once more before believing it",
                  flush=True)
            time.sleep(PAUSE)
            try:
                again = fetch(f"{group}[{i + 1}/{len(selectors)} recheck]",
                              [sel], scope, timeout)
            except Exception as e:
                again = None
                print(f"    recheck failed ({type(e).__name__}) — keeping 0",
                      flush=True)
            if again and again.get("elements"):
                data = again
                n = len(data["elements"])
                print(f"    {sel} -> {n} on the second ask; the first zero was "
                      f"a false one", flush=True)
                zeros_recovered.append(sel)
            else:
                zeros_confirmed.append(sel)
        for el in data.get("elements", []):
            key = (el.get("type"), el.get("id"))
            if key not in seen:
                seen.add(key)
                merged.append(el)
        print(f"    {sel} -> {n}", flush=True)
        if i < len(selectors) - 1:
            time.sleep(PAUSE)
    if len(incomplete) == len(selectors):
        raise RuntimeError(f"{group}: every selector failed over {scope}")
    where = f"area {scope[1]}" if isinstance(scope, tuple) else scope
    out = {"elements": merged,
           "note": f"merged from {len(selectors)} per-selector queries over {where}"}
    if zeros_confirmed:
        out["zero_selectors"] = zeros_confirmed
    if zeros_recovered:
        out["false_zeros_recovered"] = zeros_recovered
    if incomplete:
        out["incomplete"] = incomplete
        out["note"] += (f" — {len(incomplete)} of {len(selectors)} selectors never "
                        f"answered; re-run with --fetch to try them again")
    return out


def main():
    args = sys.argv[1:]
    force = "--fetch" in args
    # `--group NAME` refetches ONE group. Without it, --fetch means all twenty,
    # which is a lot of somebody else's server time to spend when the only
    # thing that changed is one group's selectors.
    only = None
    if "--group" in args:
        i = args.index("--group")
        only = args[i + 1]
        args = args[:i] + args[i + 2:]
    provinces = [a for a in args if a != "--fetch"] or ["cm"]
    for province in provinces:
        if province not in BBOX:
            print(f"unknown province {province!r} — choices: {list(BBOX)}", file=sys.stderr)
            continue
        cache = ROOT / "cache" / "overpass" / province
        cache.mkdir(parents=True, exist_ok=True)
        todo = [(g, s) for g, s in QUERIES.items()
                if (only is None or g == only)
                and (force or not (cache / f"{g}.json").exists())]
        if only and only not in QUERIES:
            print(f"unknown group {only!r} — choices: {sorted(QUERIES)}", file=sys.stderr)
            return
        if not todo:
            print(f"{province}: all cached — nothing to fetch (use --fetch to refresh)")
            continue
        print(f"{province}: {len(todo)} groups to fetch, {PAUSE}s between each — slow on purpose")
        for i, (group, selectors) in enumerate(todo):
            wide = is_wide(province, group)
            if wide:
                data = fetch_wide(group, selectors, ("area", PROVINCE_AREA[province]))
            else:
                data = fetch(group, selectors, BBOX[province])
            # Written the moment a group lands, never at the end: a
            # province-wide run is hours of somebody else's server time, and a
            # crash on group 17 must not throw away the first sixteen. Plain
            # re-run resumes — snapshot-first skips whatever is already cached.
            n = len(data.get("elements", []))
            # A REFETCH MAY NEVER SHRINK A GROUP QUIETLY.
            #
            # Overpass answered `shop=cannabis` over Chiang Mai with 28 shops
            # one hour and with ZERO the next — HTTP 200, valid JSON, empty
            # `elements`, and no `remark` to catch it. OverpassRemark cannot see
            # that one. Had it been written, the shelf would have emptied
            # itself and the cache file would have stood there as proof the
            # crawl had run, which is this crawler's oldest and worst failure.
            #
            # So the previous answer gets a vote. A refetch that comes back
            # with less than half of what we already hold is refused, kept
            # beside the good file for a look, and the operator is told. A
            # genuine collapse — a shelf that really did empty — survives one
            # re-run once somebody has seen the rejected file and agreed.
            prev_f = cache / f"{group}.json"
            if prev_f.exists():
                prev_n = len(json.loads(prev_f.read_text()).get("elements", []))
                if prev_n >= 5 and n < prev_n / 2:
                    # NOT ".json" — records() and load_tags() both glob "*.json" over
                    # this directory, and a rejected answer that ends in
                    # .json would be imported as though it were data.
                    rej = cache / f"{group}.rejected"
                    rej.write_text(json.dumps(data, ensure_ascii=False))
                    print(f"  !! {province}/{group}: refetch returned {n} where "
                          f"{prev_n} are already cached — REFUSED, kept the old "
                          f"file. The new answer is in {rej.name}; if the shelf "
                          f"really did empty, delete {prev_f.name} and re-run.",
                          flush=True)
                    if i < len(todo) - 1:
                        time.sleep(PAUSE)
                    continue
            prev_f.write_text(json.dumps(data, ensure_ascii=False))
            print(f"  {province}/{group}: {n} elements"
                  f"{' (province-wide)' if wide else ''}", flush=True)
            # A short group must never pass for a whole one. The file records
            # it, and so does the operator's screen — an empty shelf with a
            # cache file standing beside it is this crawler's oldest trap.
            if data.get("incomplete"):
                for gap in data["incomplete"]:
                    print(f"    ! never answered: {gap['selector']} "
                          f"({gap['error'][:60]})", flush=True)
                print(f"    ! {province}/{group} is INCOMPLETE — re-run "
                      f"`python3 importers/crawl_overpass.py {province} --fetch` "
                      f"when Overpass is calmer", flush=True)
            if i < len(todo) - 1:
                time.sleep(PAUSE)
        print(f"{province}: done — cache/overpass/{province}/ is the snapshot; import_all.py folds it in")


if __name__ == "__main__":
    main()
