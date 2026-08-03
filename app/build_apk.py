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

# The certificate every published copy of the app carries. Safe to keep in a
# public repo — it is readable off any APK ever shipped (`apksigner verify
# --print-certs`). It is here so the build can prove it signed with the right
# key rather than merely with *a* key: sign with a different one and phones
# refuse the update, which is discovered by a reader failing to install, long
# after the release. Checked at the end of every build.
CERT_SHA256 = "7e69294fb9fb7c8cefed8b7658671b507aa476359345a52564f416cfce448200"

BACKUP_HINT = """
Restore it before building anything. Backups made 2026-08-03:
  ~/Desktop/Mot Dang app signing key/       (keystore + password + notes)
  iCloud Drive/Mot Dang app signing key/    (keystore only, by design)
  the password should also be in your password manager

  cp "<backup>/mot-dang-app.keystore" ~/.mot-dang-app.keystore
  chmod 600 ~/.mot-dang-app.keystore

A NEW key is not a fix. Android identifies an app by its signature, so a
fresh key makes a stranger of every copy already installed: no update will
apply, and each reader would have to uninstall — losing the private visit
log the app promises to keep — before installing again.
If the key is truly gone and you accept that, pass --new-key deliberately.
"""


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd[:4]), "...")
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def ensure_keystore():
    if KEYSTORE.exists() and PASSFILE.exists():
        return PASSFILE.read_text().strip()
    if KEYSTORE.exists():
        sys.exit(f"{KEYSTORE} exists but {PASSFILE} is missing — "
                 "the password went somewhere; find it before rebuilding, "
                 "or updates will stop installing over old versions."
                 + BACKUP_HINT)
    # An app is published under this key now, so a missing keystore is a
    # thing to recover, never a thing to replace on the way past.
    if "--new-key" not in sys.argv:
        sys.exit(f"no signing key at {KEYSTORE}." + BACKUP_HINT)
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
    certs = subprocess.run(
        [str(BT / "apksigner"), "verify", "--print-certs", str(final)],
        check=True, capture_output=True, text=True).stdout
    print(certs.strip())
    if CERT_SHA256 not in certs.lower():
        final.unlink()
        sys.exit(f"\nSIGNED WITH THE WRONG KEY — expected certificate\n"
                 f"  {CERT_SHA256}\nand got something else. This APK would "
                 f"not install over the published app, so it has been "
                 f"deleted rather than left lying about looking finished."
                 + BACKUP_HINT)
    print(f"\nAPK: {final}  ({final.stat().st_size / 1e6:.1f} MB)"
          f"\n     signed with the published key — phones will take it as "
          f"an update.")


if __name__ == "__main__":
    main()
