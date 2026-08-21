#!/usr/bin/env python3
"""เวียนขวา — pick a ride, build it, put it on the phone. One numbered menu.

The three steps behind this each have their own script and their own reasons,
and running them by hand means remembering the order and getting the paths
right with a phone in one hand. This is the front door: it shows what state
things are in, and every action is a number.

  python3 dash/ship.py

WHAT IT WILL NOT DO
It cannot ship a ride that broke the standing rules, because `build_data.py`
refuses to bake one and this only calls it. That refusal is the point of the
whole chain, so it is not worked around here.
"""
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ADB = Path.home() / "Library" / "Android" / "sdk" / "platform-tools" / "adb"
APK = HERE / "out" / "motdang-wiankhwa.apk"
RIDE_JS = HERE / "www" / "data" / "ride.js"
RIDES = ROOT / "data" / "rides"
PKG = "net.motdang.dash"


def sh(cmd, **kw):
    """Run a tool and capture it, with stdin closed.

    stdin=DEVNULL is not tidiness. `adb shell` inherits this process's stdin and
    reads from it, so without this the device lookup silently ate the menu
    keystroke that had just been typed — the menu redrew as though nothing had
    been pressed. Any child that might read stdin has to be denied it.
    """
    kw.setdefault("stdin", subprocess.DEVNULL)
    return subprocess.run([str(c) for c in cmd], capture_output=True,
                          text=True, **kw)


def devices():
    """Phones adb can see, one entry per PHONE rather than per transport.

    Wireless debugging registers the same handset twice — once as a plain
    ip:port and once as an `_adb-tls-connect._tcp` mDNS service — and adb then
    refuses any command that does not name one, with "more than one
    device/emulator". Installing to a list that holds the same phone twice
    would also install twice. So entries are folded on the hardware serial,
    which is the one thing both transports agree on.

    The ip:port form is preferred when both are present: it is the one a person
    can read back and recognise.
    """
    if not ADB.exists():
        return []
    out = sh([ADB, "devices", "-l"]).stdout
    seen = {}
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line or "offline" in line or "unauthorized" in line:
            continue
        parts = line.split()
        if len(parts) < 2 or parts[1] != "device":
            continue
        serial = parts[0]
        m = re.search(r"model:(\S+)", line)
        model = m.group(1) if m else ""
        hw = sh([ADB, "-s", serial, "shell", "getprop",
                 "ro.serialno"]).stdout.strip() or serial
        prefer = ":" in serial and "_tcp" not in serial
        if hw not in seen or (prefer and "_tcp" in seen[hw][0]):
            seen[hw] = (serial, model)
    return list(seen.values())


def baked():
    if not RIDE_JS.exists():
        return None
    try:
        s = RIDE_JS.read_text()
        d = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
        return d
    except Exception:
        return None


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.0.1", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def rides():
    return sorted(p.stem for p in RIDES.glob("*.json")) if RIDES.exists() else []


def status():
    print("\n" + "─" * 58)
    d = baked()
    if d:
        print(f"  ride in the app   {d.get('name')}  ·  {d.get('km')} km  ·  "
              f"{len(d.get('cues', []))} cues")
    else:
        print("  ride in the app   none baked yet")
    if APK.exists():
        print(f"  apk               {APK.stat().st_size / 1024:.0f} KB")
    else:
        print("  apk               not built")
    devs = devices()
    if devs:
        for serial, model in devs:
            print(f"  phone             {model or 'device'}  ({serial})")
    else:
        print("  phone             none paired")
    print("─" * 58)


def do_bake():
    rs = rides()
    if not rs:
        print("\nno rides planned yet. Make one first:\n"
              "  python3 ride_plan.py --stop LAT,LNG --stop LAT,LNG --name NAME")
        return
    print()
    for i, name in enumerate(rs, 1):
        print(f"  {i}) {name}")
    pick = ask("\nwhich ride? ")
    if not pick.isdigit() or not (1 <= int(pick) <= len(rs)):
        print("  nothing chosen")
        return
    name = rs[int(pick) - 1]
    r = sh([sys.executable, HERE / "build_data.py", "--ride", name], cwd=str(ROOT))
    out = (r.stdout + r.stderr).rstrip()
    print(out)
    # A rule that may be set aside on purpose is offered here rather than only
    # in the shell, so the decision is made at the moment it matters — and it is
    # asked, never assumed. Rules that are not waivable never reach this point.
    m = re.search(r"--waive (\w+)", out)
    if r.returncode != 0 and m:
        rule = m.group(1)
        if ask(f"\nset the '{rule}' rule aside for this ride? (y/N) ").lower() in ("y", "yes"):
            r2 = sh([sys.executable, HERE / "build_data.py", "--ride", name,
                     "--waive", rule], cwd=str(ROOT))
            print((r2.stdout + r2.stderr).rstrip())
        else:
            print("  left alone — nothing baked")


def do_build():
    icon = HERE / "android" / "res" / "mipmap-mdpi" / "ic_launcher.png"
    if not icon.exists():
        print("\nmaking the launcher icon first")
        r = sh([sys.executable, HERE / "make_icon.py"], cwd=str(ROOT))
        print((r.stdout + r.stderr).rstrip())
    print("\nbuilding")
    r = sh([sys.executable, HERE / "build_apk.py"], cwd=str(ROOT))
    tail = (r.stdout + r.stderr).rstrip().splitlines()
    print("\n".join("  " + t for t in tail[-6:]))


def do_install():
    if not APK.exists():
        print("\nnothing built yet — option 2 first")
        return
    devs = devices()
    if not devs:
        print("\nno phone paired. On the vivo:")
        print("  Settings → search 'developer' → Developer options")
        print("  → Wireless debugging → on → Pair device with pairing code")
        print("Then on this Mac, with the code and the port it shows:")
        print(f"  '{ADB}' pair 192.168.0.NN:PORT")
        print("\nOr take option 4 and download it in the phone's browser instead.")
        return
    for serial, model in devs:
        print(f"\ninstalling to {model or 'device'} ({serial})")
        r = sh([ADB, "-s", serial, "install", "-r", APK])
        out = (r.stdout + r.stderr).strip()
        print("  " + (out.splitlines()[-1] if out else "no output"))
        if "Success" in out:
            print("  installed. It appears as เวียนขวา, an amber arrow on black.")


def do_serve():
    """The no-pairing path: hand the phone a URL on the same wifi."""
    if not APK.exists():
        print("\nnothing built yet — option 2 first")
        return
    ip, port = lan_ip(), 8796
    print(f"\nOn the phone's browser, with both on the same wifi:\n"
          f"\n    http://{ip}:{port}/{APK.name}\n"
          f"\nThe phone will ask to allow installing from the browser — that is\n"
          f"expected for an app that is not from a store. Ctrl-C when done.\n")
    os.chdir(APK.parent)
    import http.server
    import socketserver
    socketserver.TCPServer.allow_reuse_address = True
    try:
        socketserver.TCPServer(("", port),
                               http.server.SimpleHTTPRequestHandler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped serving")


def do_all():
    do_bake()
    if baked():
        do_build()
        if APK.exists():
            do_install()


MENU = [
    ("choose a ride and bake it in", do_bake),
    ("build the app", do_build),
    ("install it on the phone", do_install),
    ("serve it for the phone's browser instead", do_serve),
    ("all three: bake, build, install", do_all),
]


def ask(prompt):
    """Read a line, treating a closed stdin as "quit" rather than a traceback.

    This gets piped and it gets run with the terminal closing under it, and a
    stack trace is a poor way to say "nothing more was typed".
    """
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "q"


def main():
    while True:
        status()
        print()
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i}) {label}")
        print("  q) quit")
        pick = ask("\n> ").lower()
        if pick in ("q", "quit", ""):
            return 0
        if pick.isdigit() and 1 <= int(pick) <= len(MENU):
            MENU[int(pick) - 1][1]()
        else:
            print("  pick a number")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
