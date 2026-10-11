import json
with open('data/curated/minisite_harvest.json', 'r') as f:
    d = json.load(f)
d['sites']['bayeux-tapestry'] = {"state": "harvested", "doodle": "doodler-site-bayeux-tapestry.js bayeux-tapestry", "date": "2026-10-08"}
with open('data/curated/minisite_harvest.json', 'w') as f:
    json.dump(d, f, indent=1)
