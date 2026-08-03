#!/usr/bin/env python3
"""Build the signed APK with the Android SDK's own tools — no Gradle.

For one Activity and a folder of assets, the whole build is five tool
invocations, and every one of them is on disk already:

  aapt2 compile+link  resources + manifest -> resources apk with R.java
  javac               MainActivity against android.jar
  d8                  .class -> classes.dex
  zip                 dex + assets into the apk
  zipalign+apksigner  align, then sign

The signing key lives at ~/.mot-dang-app.keystore (password beside it in
~/.mot-dang-app.keystore.pass), NEVER in this public repo. Losing that file
means future updates cannot install over old ones — phones will demand an
uninstall (which erases readers' private visit logs). It is worth backing up.

Run build_data.py first if data changed; this script just packages www/.
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
APK_NAME = "motdang-hongnam.apk"


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd[:4]), "...")
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def ensure_keystore():
    if KEYSTORE.exists() and PASSFILE.exists():
        return PASSFILE.read_text().strip()
    if KEYSTORE.exists():
        sys.exit(f"{KEYSTORE} exists but {PASSFILE} is missing — "
                 "the password went somewhere; find it before rebuilding, "
                 "or updates will stop installing over old versions.")
    import secrets
    pw = secrets.token_urlsafe(24)
    PASSFILE.write_text(pw + "\n")
    PASSFILE.chmod(0o600)
    run(["keytool", "-genkeypair", "-v", "-keystore", KEYSTORE,
         "-alias", "motdang", "-keyalg", "RSA", "-keysize", "2048",
         "-validity", "10950",
         "-storepass", pw,
         "-dname", "CN=Mot Dang, O=NaNoBotCo, L=Chiang Mai, C=TH"])
    print(f"  new signing key at {KEYSTORE} (password in {PASSFILE})")
    return pw


def main():
    if not (HERE / "www" / "data" / "basemap.js").exists():
        sys.exit("www/data is empty — run build_data.py first")
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
    pw = ensure_keystore()
    final = OUT / APK_NAME
    run([BT / "apksigner", "sign", "--ks", KEYSTORE,
         "--ks-pass", f"pass:{pw}", "--ks-key-alias", "motdang",
         "--out", final, aligned])
    run([BT / "apksigner", "verify", "--print-certs", final])
    print(f"\nAPK: {final}  ({final.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
