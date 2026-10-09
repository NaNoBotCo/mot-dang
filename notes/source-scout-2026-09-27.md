# source-scout — 2026-09-27 (third run)

Measured 3 sources (1 works, 3 blocked or near-empty). Added 7, 5 of them measured `works`.
Raised 3 forks. No importer written, nothing published.

Headline: **the empty `medical/laboratory` shelf has a register.** The Medical
Technology Council's accredited-lab table lists 49 CM+CR labs, about 10 of them
walk-in lab clinics. Four of those are already in the catalogue, but the shelf
matches on `attrs.facilityType`, not `sub`, so they don't show up on it.

## Measured (Step 1)

The five priority sources were all measured in earlier runs. Only two `to-scout`
entries were left (wongnai, lazada-shopee-storefront), so the third slot went to
the MOTS v2 API, which the last note put first.

| source | status | yield |
|---|---|---|
| wongnai | blocked-by-licence | 10/10 pages: phone, tambon, lat/lng, hours all 10/10. Shop's own LINE 1/10, IG 1/10, FB 0/10, site 0/10. Terms ข้อห้าม (3) forbid compiling shop data "for any purpose" |
| lazada-shopee-storefront | partial | Shopee: every shop is the same 202,062-byte shell, 0 facts; API 403 (anti-bot, not bypassed). Lazada: seller name 3/3, location 0/3 |
| mots-tourism-directory | blocked: needs key | Manual read; API live, 401 without APIKey+SecretKey. v2 response has **no phone, email, hours or tambon**, only name/detail/coords/amphoe/IsOpen |

- **Wongnai:** we thought a Wongnai page would usually point to the shop's own Facebook. It does on 0 of 10.
- **Shopee/Lazada:** 175 storefront links on disk, and neither site adds a fact to any of them.

## Added (Step 2 and finds along the way)

| id | status | yield |
|---|---|---|
| mtcouncil-lab-accreditation | works | 1,015 rows national, **49 CM+CR**, ~10 walk-in labs (RS Lab, CM RIA, Caremat, Bangkok RIA CM, N Health ×2, MPlus ×2, NK, Mengrai Lab) |
| chiangrai-blueflag-shop-register | works | **3,511 CR shops**, tambon 3,511, mobile 3,507; 165 personal-title names refused |
| provincial-food-certification-lists | works | 81 named restaurants: CM Thai SELECT 40, CM Q Restaurant 7, CR ธงฟ้า 34 (with tambon) |
| cm-lpg-station-list | works | 28 CM rows with tambon (two datasets, same rows) |
| cm-agrifood-factory-list | works | 83 CM factories with address |
| dmsc-blood-draw-unit-register | to-scout | page shell has no rows; loads another way |
| dmsc-iso15189-accredited-labs | to-scout | Google Apps Script shell, 0 rows without its JS |

Samples: `cache/source_scout/<id>/2026-09-27.json` for the first three added and all three measured.

## Shelves this run

- **`food-drink`** (314 unmatched, the largest gap no earlier run had covered). Licence: food-sale licences are issued by each municipality, and no list has been reached yet. Neither province publishes a Clean Food Good Taste list; other provinces do (ตรัง, อยุธยา). Certification: Thai SELECT, Q Restaurant and ธงฟ้า, all measured above.
- **`medical/laboratory`** (KNOWN_EMPTY). Licensing sits with สบส. (verifier only, already registered). Accreditation: the MT Council table (works) and DMSc's two lists (to-scout). The KNOWN_EMPTY reason should be re-read once `facilityType` is set on the four matched labs. I did not edit `test_facets.py`.

## Refused

- Wongnai bulk and its `/_api/`: terms forbid it; 403 anyway.
- Shopee's API behind its anti-bot gate.
- `mtc-webservices…/members/search`, the MT Council's register of licensed technologists: people, not places. Not called.
- `ชื่อผู้ประกอบการ` in the CR ธงฟ้า restaurant list, and the 165 personal-title shop names: natural persons.
- Blue Flag mobile numbers: not stored in the sample until the fork is answered.

## Forks raised

1. TTD API key in Nan's name. Recommend reading the signup terms first. Default: not done, 2026-10-27.
2. Wongnai: ask permission or leave it blocked. Recommend leaving it. Default: blocked.
3. Blue Flag mobiles on shop records. Recommend name and address only. Default: no mobiles.

## Next week

1. **The two DMSc lab lists**, in a browser tab. They are the last check before the lab importer; measure their overlap with the MT Council table.
2. **เทศบาลนครเชียงใหม่'s ตลาดสด and food-sale licence lists.** Owed since 9/06. `food` is still the biggest gap, and no licence list has been reached for it.
3. **The TTD website's signup terms**, so fork 1 can be decided on facts.
