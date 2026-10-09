import json

with open('_incoming/newsletter/2026-10-05.pins.draft.json', 'r') as f:
    pins = json.load(f)['pins']
with open('_incoming/newsletter/2026-10-05.gleanings.json', 'r') as f:
    glean = json.load(f)

venues = glean.get('venues', [])
matched = sum(1 for v in venues if v.get('matched_catalogue_id'))
unmatched = len(venues) - matched
newly_pinned = sum(1 for v in venues if v.get('pin'))

print(f"Pins: {len(pins)}")
print(f"Venues: matched {matched}, unmatched {unmatched}, newly pinned {newly_pinned}")
print(f"Relations: {len(glean.get('relations', []))}")
print(f"Conflicts: {len(glean.get('conflicts', []))}")
