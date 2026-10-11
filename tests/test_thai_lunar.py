#!/usr/bin/env python3
"""Hold importers/thai_lunar.py to myhora.com's วันพระ lists for พ.ศ. 2540–2570
(tests/wan_phra_myhora.txt): the same days, the same ขึ้น/แรม and ค่ำ, the same
month, and no วันพระ myhora does not list."""
import datetime as dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
import thai_lunar as T  # noqa: E402


def myhora():
    rows = {}
    for line in open(os.path.join(ROOT, "tests", "wan_phra_myhora.txt"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        year, *toks = line.split()
        for t in toks:
            md, sign, day, month = re.fullmatch(r"(\d{4})([+-])(\d+)/(\d+)", t).groups()
            d = dt.date(int(year), int(md[:2]), int(md[2:]))
            rows[d] = (sign == "+", int(day), int(month))
    return rows


def test_every_listed_day_matches():
    for d, (waxing, day, month) in myhora().items():
        got = T.lunar_day(d)
        assert (got["waxing"], got["day"], got["month"]) == (waxing, day, month), (d, got)
        assert got["wan_phra"] == (day != 1), (d, got)   # the -1 rows are วันเข้าพรรษา


def test_no_extra_wan_phra():
    listed = {d for d, (_, day, _) in myhora().items() if day != 1}
    d = dt.date(1997, 1, 1)
    while d <= dt.date(2027, 12, 31):
        assert T.lunar_day(d)["wan_phra"] == (d in listed), d
        d += dt.timedelta(days=1)


def test_2569_thai_pbs():
    # Thai PBS news 558354: วันพระ 4, 11, 19 and 26 Oct 2569.
    for iso, waxing, day, month in [("2026-09-26", True, 15, 10), ("2026-10-04", False, 8, 10),
                                    ("2026-10-11", False, 15, 10), ("2026-10-19", True, 8, 11),
                                    ("2026-10-26", True, 15, 11)]:
        got = T.lunar_day(dt.date.fromisoformat(iso))
        assert (got["waxing"], got["day"], got["month"], got["wan_phra"]) == (waxing, day, month, True)


if __name__ == "__main__":
    test_every_listed_day_matches()
    test_no_extra_wan_phra()
    test_2569_thai_pbs()
    print("ok")
