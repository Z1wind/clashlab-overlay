# -*- coding: utf-8 -*-
"""手工构建 Android APK（不依赖 Gradle）：javac -> d8 -> aapt2 -> zipalign -> apksigner。"""
import os, shutil, subprocess, sys, zipfile

PROJ = r"E:\ClashLab\android"
JDK = r"E:\tools\jdk17"
SDK = r"E:\tools\android-sdk"
BT = os.path.join(SDK, "build-tools", "34.0.0")
AJAR = os.path.join(SDK, "platforms", "android-34", "android.jar")
BUILD = os.path.join(PROJ, "build")
DIST = os.path.join(PROJ, "dist")
env = dict(os.environ)
env["JAVA_HOME"] = JDK
env["PATH"] = os.path.join(JDK, "bin") + ";" + env.get("PATH", "")

def run(cmd, cwd=None):
    print("$", " ".join(cmd[:4]), "...", flush=True)
    p = subprocess.run(cmd, cwd=cwd or PROJ, env=env, capture_output=True, text=True)
    if p.stdout.strip():
        print(p.stdout[-2000:])
    if p.stderr.strip():
        print("STDERR:", p.stderr[-3000:])
    if p.returncode != 0:
        raise SystemExit("FAILED (%d): %s" % (p.returncode, " ".join(cmd[:4])))
    return p

def main():
    for d in (BUILD, DIST):
        os.makedirs(d, exist_ok=True)
    classes = os.path.join(BUILD, "classes")
    dexdir = os.path.join(BUILD, "dex")
    for d in (classes, dexdir):
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d, exist_ok=True)

    src = [os.path.join(PROJ, "java", "com", "clashlab", "annotator", "MainActivity.java")]
    run([os.path.join(JDK, "bin", "javac.exe"), "-source", "8", "-target", "8",
         "-bootclasspath", AJAR, "-encoding", "UTF-8", "-d", classes] + src)

    cfiles = []
    for dp, dn, fs in os.walk(classes):
        for f in fs:
            if f.endswith(".class"):
                cfiles.append(os.path.join(dp, f))
    run([os.path.join(BT, "d8.bat"), "--release", "--lib", AJAR, "--output", dexdir] + cfiles)

    base_apk = os.path.join(BUILD, "base.apk")
    if os.path.exists(base_apk):
        os.remove(base_apk)
    run([os.path.join(BT, "aapt2.exe"), "link", "-o", base_apk, "-I", AJAR,
         "--manifest", os.path.join(PROJ, "AndroidManifest.xml"),
         "-A", os.path.join(PROJ, "assets"),
         "--min-sdk-version", "24", "--target-sdk-version", "28",
         "--version-code", "1", "--version-name", "0.1.0", "--auto-add-overlay"])

    dex = os.path.join(dexdir, "classes.dex")
    with zipfile.ZipFile(base_apk, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(dex, "classes.dex")
    print("[added classes.dex]", os.path.getsize(dex), "bytes")

    aligned = os.path.join(BUILD, "aligned.apk")
    run([os.path.join(BT, "zipalign.exe"), "-f", "4", base_apk, aligned])

    ks = os.path.join(PROJ, "debug.keystore")
    if not os.path.exists(ks):
        run([os.path.join(JDK, "bin", "keytool.exe"), "-genkeypair", "-keystore", ks,
             "-storepass", "android", "-alias", "androiddebugkey", "-keypass", "android",
             "-dname", "CN=ClashLab, OU=Dev, O=ClashLab, L=CN, ST=CN, C=CN",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000"])
    out_apk = os.path.join(DIST, "ClashLabAnnotator.apk")
    if os.path.exists(out_apk):
        os.remove(out_apk)
    run([os.path.join(BT, "apksigner.bat"), "sign", "--ks", ks, "--ks-pass", "pass:android",
         "--key-pass", "pass:android", "--out", out_apk, aligned])
    run([os.path.join(BT, "apksigner.bat"), "verify", "--print-certs", out_apk])
    print("[APK]", out_apk, os.path.getsize(out_apk), "bytes")
    print("BUILD_DONE")

if __name__ == "__main__":
    main()
