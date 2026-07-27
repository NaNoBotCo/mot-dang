# Adding real photos

Drop a file named `<record-id>.jpg` (or `.jpeg`/`.png`/`.webp`) in this folder
and the next `python3 build.py` picks it up automatically instead of the
default wat illustration.

Find a place's `<record-id>` in its own page URL:
`https://motdang.net/cm/p/<record-id>.html` → the id is the last segment.

Guidelines:
- Please keep it under ~1MB and roughly 1200px on the long side.
- One photo per place; landscape works best.
- Only upload photos you have the right to share.

Prefer not to touch this folder directly? Open a place's page on the live
site and use its "Add a photo" link — it opens a pre-filled GitHub issue
where you can just drag the photo in.
