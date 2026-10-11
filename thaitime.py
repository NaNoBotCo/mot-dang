"""Bangkok's date and the Thai calendar's names, in one place for the layers that bake dates
(design: notes/calendar-design-2026-10-11.txt, D). The server's clock is UTC and the Mac's is
Bangkok's; a bake takes its "today" from here. The same day boundary as assets/front/when.js.

  bangkok_today()   the date in Bangkok (shelflife.today)
  day_of(moment)    the Bangkok date a moment belongs to when a day ends at 03:00
  be(year)          the Buddhist-era year
  wan_phra(d)       the Thai lunar date of d and whether it is a wan phra, from importers/thai_lunar.py
"""
import datetime as dt
import sys
from pathlib import Path

import shelflife

sys.path.insert(0, str(Path(__file__).resolve().parent / "importers"))
import thai_lunar  # noqa: E402

BKK = shelflife.BKK
DAY_END_H = 3          # when.js DAY_END_H


def bangkok_today():
    return shelflife.today()


def day_of(moment):
    """The Bangkok date a moment belongs to: a datetime (aware, or naive and taken as Bangkok's)
    or a Unix time in seconds."""
    if not isinstance(moment, dt.datetime):
        moment = dt.datetime.fromtimestamp(moment, BKK)
    elif moment.tzinfo is None:
        moment = moment.replace(tzinfo=BKK)
    return (moment.astimezone(BKK) - dt.timedelta(hours=DAY_END_H)).date()


def be(year):
    return year + 543


def wan_phra(d):
    """thai_lunar.lunar_day(d): be, month, month_days, waxing, day, wan_phra."""
    return thai_lunar.lunar_day(d)
