"""Ground truth per place: how much of it someone has seen, the way backlinks once weighed a page.

Nan, 2026-10-12: "Ground truth is the new backlinks", "yes, rank places by ground truth too", and
"ground truth and user intent". A reader's words, shelf, place and choices decide which places
answer; among those, ground truth orders them.

A place's ground truth is the sightings on disk, weighed by who saw it:

    own          her own photographs of it (build.OWN_BY_PLACE), each, up to 6   × 3
    own street   her street-level photograph (streetphoto_layer, own)            × 3
    photo        a curated photograph (assets/photos/<id>, build.PHOTO_FILES)    × 2
    confirmed    the business confirmed its record (claims, confirmedAt)        × 2
    street       a Mapillary street-level photograph                            × 1
    commons      a Wikimedia Commons photograph matched to it                    × 1

score(r, …) is the weighted sum; level(score) folds it to 0–9 for the search index.
"""
import math

W = {"own": 3, "own_street": 3, "photo": 2, "confirmed": 2, "street": 1, "commons": 1}
OWN_MAX = 6
_CACHE = {}


def score(r, own_by_place, street_photos, commons_images, photo_files, claims):
    rid = r["id"]
    got = _CACHE.get(rid)
    if got is not None:
        return got
    sp = street_photos.get(rid) or {}
    s = (W["own"] * min(OWN_MAX, len(own_by_place.get(rid) or ()))
         + (W["own_street"] if sp and sp.get("own") else W["street"] if sp else 0)
         + (W["photo"] if rid in photo_files else 0)
         + (W["confirmed"] if (claims.get(rid) or {}).get("confirmedAt") else 0)
         + (W["commons"] if rid in commons_images else 0))
    _CACHE[rid] = s
    return s


def level(s):
    """0 for nothing seen, then 2·log₂(1 + s) rounded, up to 9."""
    return 0 if s <= 0 else min(9, max(1, round(2 * math.log2(1 + s))))
