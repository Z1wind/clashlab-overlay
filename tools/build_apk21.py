# -*- coding: utf-8 -*-
"""构建 APK v0.2.1（四角可拖动 + 全中文类型）。"""
import os, shutil, subprocess, sys, zipfile
PROJ = r"E:\ClashLab\android"; JDK = r"E:\tools\jdk17"; SDK = r"E:\tools\android-sdk"
BT = os.path.join(SDK, "build-tools", "34.0.0"); AJAR = os.path.join(SDK, "platforms", "android-34", "android.jar")
BUILD = os.path.join(PROJ, "build"); DIST = os.path.join(PROJ, "dist")
env = dict(os.environ); env["JAVA_HOME"] = JDK; env["PATH"] = os.path.join(JDK, "bin") + ";" + env.get("PATH", "")
def run(cmd, cwd=None):
    print("$", " ".join(cmd[:3]), "...", flush=True)
    p = subprocess.run(cmd, cwd=cwd or PROJ, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout[-1500:]); print(p.stderr[-1500:]); raise SystemExit("FAILED")
    return p
for d in (BUILD, DIST): os.makedirs(d, exist_ok=True)
classes = os.path.join(BUILD, "classes21"); dexdir = os.path.join(BUILD, "dex21")
for d in (classes, dexdir): shutil.rmtree(d, ignore_errors=True); os.makedirs(d, exist_ok=True)
run([os.path.join(JDK, "bin", "javac.exe"), "-source", "8", "-target", "8", "-bootclasspath", AJAR,
     "-encoding", "UTF-8", "-d", classes, os.path.join(PROJ, "java", "com", "clashlab", "annotator", "MainActivity.java")])
cfiles = [os.path.join(dp, f) for dp, dn, fs in os.walk(classes) for f in fs if f.endswith(".class")]
run([os.path.join(BT, "d8.bat"), "--release", "--lib", AJAR, "--output", dexdir] + cfiles)
base = os.path.join(BUILD, "base21.apk")
if os.path.exists(base): os.remove(base)
run([os.path.join(BT, "aapt2.exe"), "link", "-o", base, "-I", AJAR,
     "--manifest", os.path.join(PROJ, "AndroidManifest.xml"), "-A", os.path.join(PROJ, "assets"),
     "--min-sdk-version", "24", "--target-sdk-version", "28",
     "--version-code", "3", "--version-name", "0.2.1", "--auto-add-overlay"])
with zipfile.ZipFile(base, "a", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(dexdir, "classes.dex"), "classes.dex")
aligned = os.path.join(BUILD, "aligned21.apk")
run([os.path.join(BT, "zipalign.exe"), "-f", "4", base, aligned])
out = os.path.join(DIST, "ClashLabAnnotator_v21.apk")
if os.path.exists(out): os.remove(out)
run([os.path.join(BT, "apksigner.bat"), "sign", "--ks", os.path.join(PROJ, "debug.keystore"),
     "--ks-pass", "pass:android", "--key-pass", "pass:android", "--out", out, aligned])
print("[APK]", out, os.path.getsize(out), "bytes")
print("BUILD_DONE")
