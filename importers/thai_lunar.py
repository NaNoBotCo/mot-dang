"""The Thai lunar calendar (ปฏิทินจันทรคติไทย), day by day, as the official
calendar counts it: fixed-length months, not the Moon's phase on the night.

A lunar year runs ขึ้น ๑ ค่ำ เดือนอ้าย (Nov/Dec) to the end of เดือนสิบสอง.
Odd months (เดือนขาด) have ขึ้น ๑–๑๕ then แรม ๑–๑๔; even months (เดือนเต็ม)
run to แรม ๑๕. Three year types, named by the Buddhist-era year its เดือนแปด
falls in:

  .  ปกติมาส ปกติวาร   354 days
  V  ปกติมาส อธิกวาร   355 — เดือนเจ็ด runs to แรม ๑๕
  M  อธิกมาส ปกติวาร   384 — a second เดือนแปด (๘๘) follows the first

วันพระ is ขึ้น ๘, ขึ้น ๑๕, แรม ๘ and the month's last day (แรม ๑๔ or ๑๕).

YEARS is myhora.com's year type for พ.ศ. 2440–2700 (calendar/thai-07-YYYY.aspx,
read 2026-09-26). The textbook สุริยยาตร leap-month test (ดิถี ≥ 24 or ≤ 5)
agrees with it through 2584 and then splits paired years, so the table is used
rather than the formula. tests/test_thai_lunar.py checks every วันพระ myhora
lists for 2540–2570.
"""
import datetime as dt

FIRST_BE = 2440
YEARS = (".VM.M.VM..MVM..M.VM.VM.M..M.VM.MV.M.VM.VM.M..M.MV.M.VM.VM..MVM..M.VM.M..MV"
         ".MV.M.M.VM..M.M.VM.VM.M..MV.MV.M.M.VM.VM.M..MV.M.VM.M.VM..M.MV.MV.M..MV.M.MV"
         ".M.M.VM.VM.VM..M.M.MV.M.VM.M.VM..M.MV.MV.M..MV.M.MV.M.M.VM..M.V.VM.M.MV.M.VM"
         ".M.VM..M.MV.MV.M..MV.M.MV.M.M.VM..M")
LAST_BE = FIRST_BE + len(YEARS) - 1

# ขึ้น ๑ ค่ำ เดือนอ้าย opening the lunar year of พ.ศ. 2570 (myhora: 17 Dec 2026 is ขึ้น ๘ เดือนอ้าย).
ANCHOR_DATE, ANCHOR_BE = dt.date(2026, 12, 10), 2570

MONTH_TH = {1: "อ้าย", 2: "ยี่", 3: "สาม", 4: "สี่", 5: "ห้า", 6: "หก", 7: "เจ็ด",
            8: "แปด", 88: "แปดหลัง", 9: "เก้า", 10: "สิบ", 11: "สิบเอ็ด", 12: "สิบสอง"}


def year_type(be):
    if not FIRST_BE <= be <= LAST_BE:
        raise ValueError(f"Thai lunar year type for พ.ศ. {be} is outside {FIRST_BE}–{LAST_BE}")
    return YEARS[be - FIRST_BE]


def months(be):
    """[(month, days)] for the lunar year whose เดือนแปด falls in พ.ศ. be."""
    t = year_type(be)
    out = []
    for m in (1, 2, 3, 4, 5, 6, 7, 8, 88, 9, 10, 11, 12):
        if m == 88 and t != "M":
            continue
        full = m % 2 == 0 or (m == 7 and t == "V")
        out.append((m, 30 if full else 29))
    return out


def year_length(be):
    return sum(n for _, n in months(be))


def lunar_day(d):
    """The Thai lunar date of a Gregorian date: month, ค่ำ 1–15, which half, and
    whether it is วันพระ."""
    be, start = ANCHOR_BE, ANCHOR_DATE
    while d < start:
        be -= 1
        start -= dt.timedelta(days=year_length(be))
    while d >= start + dt.timedelta(days=year_length(be)):
        start += dt.timedelta(days=year_length(be))
        be += 1
    k = (d - start).days
    for m, n in months(be):
        if k < n:
            break
        k -= n
    waxing = k < 15
    day = k + 1 if waxing else k - 14
    wan_phra = day == 8 or (waxing and day == 15) or (not waxing and k == n - 1)
    return {"be": be, "month": m, "month_days": n, "waxing": waxing,
            "day": day, "wan_phra": wan_phra}
