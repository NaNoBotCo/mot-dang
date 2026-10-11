"""The site's buttons into the Mot Dang LINE account.

Nan, 2026-09-28: reasons to add Mot Dang on LINE — pins and plans kept, the ant
answering in the chat, warnings for your own place, stamp rounds (the nine
wats, the Mae Hong Son passport), shop owners editing by chat, credit for
weather reports, mark safe.

A button opens LINE with the message already typed to the account
(line.me/R/oaMessage); the reader taps send, and that message is the sign-up.
The prefixes are the ones motdang-line's pages.js reads.

ON stays False until motdang-line runs with its PAGES flag on. Until then the
account's own auto-reply answers one-to-one chats, and a button here would
send a reader to it."""

from urllib.parse import quote

ON = False
OA = "@964yxgnk"
ADD = "https://lin.ee/zasnN2u"

PINS = "หมุด · pins "
PLAN = "แผน · plan "
SAFE = "ปลอดภัย · safe"
HELP = "ต้องการความช่วยเหลือ · need help"
OWNER = "เจ้าของ · owner "
HOME = "บ้าน · home"
PASSPORT = "พาสปอร์ต · passport "


def url(text):
    return f"https://line.me/R/oaMessage/{quote(OA)}/?{quote(text)}"


def js_const():
    """What mapfirst.js / obs_layer.js read: null while off."""
    import json
    if not ON:
        return "null"
    return json.dumps({"oa": quote(OA), "pins": PINS, "safe": SAFE, "help": HELP,
                       "home": HOME, "add": ADD}, ensure_ascii=False)
