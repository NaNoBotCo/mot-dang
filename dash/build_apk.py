#!/usr/bin/env python3
"""Build the signed เวียนขวา APK with the Android SDK's own tools — no Gradle.

Same five invocations as `app/build_apk.py`, pointed at this folder:

  aapt2 compile+link  resources + manifest -> resources apk with R.java
  javac               MainActivity against android.jar
  d8                  .class -> classes.dex
  zip                 dex + assets into the apk
  zipalign+apksigner  align, then sign

WHY THIS IS A SECOND SCRIPT AND NOT A FLAG ON THE FIRST
`app/build_apk.py` builds a published, signed app that readers already have
installed, and its certificate gate is the thing standing between a wrong key
and an update nobody can install. Refactoring it into something parameterised —
unasked, while adding a second app — risks that build to save this file. So
this is a sibling rather than a rewrite, and merging the two is a change worth
making deliberately with her rather than as a side effect. If you do merge
them, the certificate gate is the part to keep exactly as it is.

SAME KEY, DIFFERENT APP. Android identifies an app by its package name and its
signature. `net.motdang.dash` is a different package from `net.motdang.app`, so
signing both with the one Mot Dang key is correct and keeps them recognisably
from the same hand. The certificate below is therefore the same certificate the
toilets app checks — it is a property of the key, not of the app.

  python3 dash/make_icon.py       # once, or when the icon changes
  python3 dash/build_data.py …    # bake an accepted ride
  python3 dash/build_apk.py       # this
"""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SDK = pathlib.Path.home() / "Library" / "Android" / "sdk"
BT = SDK / "build-tools" / "35.0.0"
PLATFORM = SDK / "platforms" / "android-35" / "android.jar"
KEYSTORE = pathlib.Path.home() / ".mot-dang-app.keystore"
PASSFILE = pathlib.Path.home() / ".mot-dang-app.keystore.pass"
OUT = HERE / "out"
APK_NAME = "motdang-wiankhwa.apk"

# A property of the signing key, not of this app — the same certificate
# app/build_apk.py checks. Signing with anything else would make a stranger of
# every copy already installed, which is discovered at install time, long after
# the build said it was finished.
CERT_SHA256 = "7e69294fb9fb7c8cefed8b7658671b507aa476359345a52564f416cfce448200"


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd[:4]), "...")
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def main():
    if not (HERE / "www" / "data" / "ride.js").exists():
        sys.exit("no ride baked — run dash/build_data.py first.\n"
                 "The view carries no router, so an app with no ride in it is "
                 "an app with nothing to show.")
    if not (HERE / "android" / "res" / "mipmap-mdpi" / "ic_launcher.png").exists():
        sys.exit("no launcher icon — run dash/make_icon.py first.")
    if not BT.exists():
        sys.exit(f"no build-tools at {BT}")
    if not (KEYSTORE.exists() and PASSFILE.exists()):
        sys.exit(f"no signing key at {KEYSTORE} (and its .pass beside it). "
                 "See app/build_apk.py for where the backups are — a new key "
                 "is not a fix.")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "compiled").mkdir(parents=True)
    (OUT / "classes").mkdir()

    print("aapt2 compile/link")
    res_zip = OUT / "res.zip"
    run([BT / "aapt2", "compile", "--dir", HERE / "android" / "res",
         "-o", res_zip])
    unsigned = OUT / "unsigned.apk"
    run([BT / "aapt2", "link",
         "-I", PLATFORM,
         "--manifest", HERE / "android" / "AndroidManifest.xml",
         "--min-sdk-version", "26", "--target-sdk-version", "35",
         "--java", OUT / "gen",
         "-o", unsigned,
         res_zip], cwd=HERE)

    print("javac + d8")
    java_src = list((HERE / "android" / "java").rglob("*.java"))
    gen_src = list((OUT / "gen").rglob("*.java"))
    run(["javac", "-source", "8", "-target", "8",
         "-classpath", PLATFORM,
         "-d", OUT / "classes"] + java_src + gen_src)
    class_files = list((OUT / "classes").rglob("*.class"))
    run([BT / "d8", "--release", "--lib", PLATFORM,
         "--output", OUT] + class_files)

    print("package")
    import zipfile
    with zipfile.ZipFile(unsigned, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT / "classes.dex", "classes.dex")
        www = HERE / "www"
        for f in sorted(www.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                z.write(f, "assets/www/" + str(f.relative_to(www)))

    print("zipalign + apksigner")
    aligned = OUT / "aligned.apk"
    run([BT / "zipalign", "-f", "4", unsigned, aligned])
    pw = PASSFILE.read_text().strip()
    final = OUT / APK_NAME
    run([BT / "apksigner", "sign", "--ks", KEYSTORE,
         "--ks-pass", f"pass:{pw}", "--ks-key-alias", "motdang",
         "--out", final, aligned])
    certs = subprocess.run(
        [str(BT / "apksigner"), "verify", "--print-certs", str(final)],
        check=True, capture_output=True, text=True).stdout
    print(certs.strip())
    if CERT_SHA256 not in certs.lower():
        final.unlink()
        sys.exit("\nSIGNED WITH THE WRONG KEY — expected\n"
                 f"  {CERT_SHA256}\nand got something else. Deleted rather "
                 "than left lying about looking finished.")
    print(f"\nAPK: {final}  ({final.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
