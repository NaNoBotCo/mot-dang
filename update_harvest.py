import json
with open('data/curated/minisite_harvest.json', 'r') as f:
    d = json.load(f)
d['sites']['basque-tables'] = {"state": "out", "why": "No drawing worth taking; only fade-ins and static SVG maps"}
with open('data/curated/minisite_harvest.json', 'w') as f:
    json.dump(d, f, indent=1)
