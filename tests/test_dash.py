#!/usr/bin/env python3
"""The dash view's assets and the promises its manifest makes.

Two of these are guards rather than checks, and they are the reason this file
exists at all:

  * **a refused ride must never reach the screen.** ride_plan.py decides whether
    a route keeps the standing rules, and a rider following the arrow has no way
    to tell that it was built from a route which broke one. So build_data.py has
    to refuse, and this proves it does.
  * **the app must have no way to phone home.** The manifest asks for location
    and nothing else — no INTERNET — and the view fetches nothing over the
    network. That is a promise kept by the package rather than by a privacy
    page, and it is exactly the sort of thing that rots quietly when someone
    adds a font or an analytics snippet later.

Run: python3 tests/test_dash.py
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "dash"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

FAILED = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def ride_asset():
    p = DASH / "www" / "data" / "ride.js"
    if not p.exists():
        return None
    s = p.read_text()
    return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def main():
    print("the baked ride")
    d = ride_asset()
    if d is None:
        print("  no ride baked — run dash/build_data.py first")
        return 1
    check("the asset parses", isinstance(d, dict))
    check("it carries the line", len(d.get("line", [])) > 10, f"{len(d['line'])} points")
    check("it carries cues", len(d.get("cues", [])) > 0, f"{len(d['cues'])}")
    check("the baked ride was an ACCEPTED one", d.get("ok") is True)
    check("cues are bilingual",
          all(c.get("say_th") and c.get("say_en") for c in d["cues"]))
    check("the rider-facing asset drops the report fields",
          "rules" not in d and "legs" not in d,
          "findings and leg breakdown are for a person reading a report")

    print("\na rule set aside on purpose stays visible")
    import importlib.util
    spec = importlib.util.spec_from_file_location("bd", DASH / "build_data.py")
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    check("only 'turning' may ever be set aside", bd.WAIVABLE == ("turning",),
          "where the ride goes is not negotiable; which way round it runs is")
    check("the quarter rule is not waivable", "quarter" not in bd.WAIVABLE)
    check("the gate rule is not waivable", "gate" not in bd.WAIVABLE)
    if d.get("kind") == "lap":
        check("the baked lap records the waiver", d.get("waived") == ["turning"],
              str(d.get("waived")))
        check("and says in words what was set aside",
              bool(d.get("waived_why")) and "เวียนขวา" in " ".join(d["waived_why"]))
        check("and carries its direction for the screen to show",
              d.get("direction") in ("clockwise", "anticlockwise"),
              str(d.get("direction")))

    print("\nthe waiver cannot be widened to the rules that matter")
    r = subprocess.run(
        [sys.executable, str(DASH / "build_data.py"),
         "--stop", "18.7963246,98.9887797",
         "--stop", "18.7807397,98.9791533",     # Suan Prung — southwest
         "--waive", "turning", "--waive", "quarter", "--waive", "gate"],
        capture_output=True, text=True, cwd=str(ROOT))
    check("a southwest stop is still refused with every waiver passed",
          r.returncode != 0, f"exit {r.returncode}")
    check("and refused for the quarter rule specifically",
          "southwest" in (r.stdout + r.stderr).lower())

    print("\na refused ride cannot be baked")
    before = (DASH / "www" / "data" / "ride.js").read_bytes()
    r = subprocess.run(
        [sys.executable, str(DASH / "build_data.py"),
         "--stop", "18.7963246,98.9887797",     # Wat Chiang Yuen
         "--stop", "18.7807397,98.9791533"],    # Suan Prung — southwest
        capture_output=True, text=True, cwd=str(ROOT))
    check("build_data.py exits non-zero", r.returncode != 0, f"exit {r.returncode}")
    check("and says which rule", "southwest" in (r.stdout + r.stderr).lower(),
          (r.stdout + r.stderr).strip().splitlines()[-1][:70] if (r.stdout + r.stderr) else "")
    check("and left the accepted ride untouched",
          (DASH / "www" / "data" / "ride.js").read_bytes() == before)

    print("\nthe view reaches for nothing over the network")
    for name in ("index.html", "dash.js", "dash.css"):
        src = (DASH / "www" / name).read_text()
        urls = re.findall(r'https?://[^\s"\')]+', src)
        check(f"{name} names no remote host", not urls, ", ".join(urls[:3]))
    js = (DASH / "www" / "dash.js").read_text()
    check("dash.js does not fetch",
          "fetch(" not in js and "XMLHttpRequest" not in js
          and "importScripts" not in js)

    print("\nthe manifest promises the same thing")
    man = (DASH / "android" / "AndroidManifest.xml").read_text()
    check("no INTERNET permission", "android.permission.INTERNET" not in man)
    check("location is asked for", "ACCESS_FINE_LOCATION" in man)
    check("its own package, so it installs beside the toilets app",
          'package="net.motdang.dash"' in man)

    print("\nthe screen is kept awake")
    java = (DASH / "android" / "java" / "net" / "motdang" / "dash"
            / "MainActivity.java").read_text()
    check("FLAG_KEEP_SCREEN_ON is set", "FLAG_KEEP_SCREEN_ON" in java,
          "a nav screen that sleeps at a light is not a nav screen")
    check("zoom is off", "setSupportZoom(false)" in java)

    print("\nthe built APK, if there is one")
    apk = DASH / "out" / "motdang-wiankhwa.apk"
    if not apk.exists():
        print("  (none built — run dash/build_apk.py; the checks above stand)")
    else:
        with zipfile.ZipFile(apk) as z:
            names = z.namelist()
        check("the ride is inside", "assets/www/data/ride.js" in names)
        check("the view is inside", "assets/www/index.html" in names)
        check("there is a dex", "classes.dex" in names)
        check("it is small enough to send over LINE",
              apk.stat().st_size < 2_000_000,
              f"{apk.stat().st_size / 1024:.0f} KB")
        bt = Path.home() / "Library" / "Android" / "sdk" / "build-tools" / "35.0.0"
        signer = bt / "apksigner"
        if signer.exists():
            out = subprocess.run([str(signer), "verify", "--print-certs", str(apk)],
                                 capture_output=True, text=True)
            check("the signature verifies", out.returncode == 0)
            check("signed with the published Mot Dang key",
                  "7e69294fb9fb7c8cefed8b7658671b507aa476359345a52564f416cfce448200"
                  in out.stdout.lower())

    print("\nthe shipper reads the world without being run interactively")
    sys.path.insert(0, str(DASH))
    import ship  # noqa: E402
    check("it can list planned rides", isinstance(ship.rides(), list),
          f"{len(ship.rides())} on disk")
    check("it can read the baked ride", (ship.baked() or {}).get("ok") is True)
    check("device discovery returns a list, paired or not",
          isinstance(ship.devices(), list),
          f"{len(ship.devices())} phone(s) visible")
    check("every menu entry has a label and an action",
          all(isinstance(a, str) and callable(f) for a, f in ship.MENU),
          f"{len(ship.MENU)} options")
    check("it never bakes around the refusal",
          "build_data.py" in DASH.joinpath("ship.py").read_text()
          and "--force" not in DASH.joinpath("ship.py").read_text(),
          "it calls build_data.py, which is what refuses")

    print()
    if FAILED:
        print(f"{len(FAILED)} failed: " + "; ".join(FAILED))
        return 1
    print("all dash checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
