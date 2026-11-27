# -*- coding: utf-8 -*-
"""可移植 APK 构建脚本（本地/CI 通用）。

环境变量：
  JAVA_HOME           JDK 17 根目录
  ANDROID_HOME/SDK    Android SDK 根目录（含 build-tools/、platforms/android-34/android.jar）
  CLASHLAB_ANDROID    android 工程目录（默认 <repo>/android）
  CLASHLAB_OUT        输出目录（默认 <repo>/dist）

用法：python tools/build_apk_ci.py [--version-name 0.2.5] [--version-code 7]
"""
import argparse, glob, os, shutil, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WIN = os.name == "nt"

def env_dir(*names):
    for n in names:
        v = os.environ.get(n)
        if v and os.path.isdir(v):
            return v
    return None

def run(cmd, cwd=None):
    print("$", " ".join(str(c) for c in cmd[:3]), "...", flush=True)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace")
    err = (p.stderr or b"").decode("utf-8", "replace")
    if p.returncode != 0:
        print(out[-2000:]); print(err[-3000:])
        raise SystemExit("FAILED (%d)" % p.returncode)
    return p

def latest_build_tools(sdk):
    d = os.path.join(sdk, "build-tools")
    if not os.path.isdir(d):
        raise SystemExit("build-tools not found under " + sdk)
    vers = sorted(os.listdir(d), key=lambda s: [int(x) if x.isdigit() else 0 for x in s.replace("-", ".").split(".")])
    return os.path.join(d, vers[-1])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version-name", default="0.2.5")
    ap.add_argument("--version-code", default="7")
    _proj = env_dir("CLASHLAB_ANDROID")
    if not _proj:
        _cand = os.path.join(os.path.realpath(ROOT), "android")   # junction -> ASCII path
        _proj = _cand if os.path.isdir(_cand) else os.path.join(ROOT, "android")
    ap.add_argument("--proj", default=_proj)
    ap.add_argument("--out-dir", default=env_dir("CLASHLAB_OUT") or os.path.join(ROOT, "dist"))
    a = ap.parse_args()
    jdk = env_dir("JAVA_HOME")
    sdk = env_dir("ANDROID_HOME", "ANDROID_SDK_ROOT")
    if not jdk: raise SystemExit("JAVA_HOME not set")
    if not sdk: raise SystemExit("ANDROID_HOME not set")
    bt = latest_build_tools(sdk)
    ajar = None
    for cand in sorted(glob.glob(os.path.join(sdk, "platforms", "android-*", "android.jar")), reverse=True):
        ajar = cand; break
    if not ajar: raise SystemExit("android.jar not found")
    print("JDK:", jdk); print("SDK:", sdk); print("BT:", bt); print("AJAR:", ajar)
    def exe(name):
        p = os.path.join(bt, name + (".bat" if WIN else ""))
        return p if os.path.exists(p) else os.path.join(bt, name)
    build = os.path.join(a.proj, "build_ci")
    classes = os.path.join(build, "classes"); dexdir = os.path.join(build, "dex")
    shutil.rmtree(build, ignore_errors=True)
    os.makedirs(classes); os.makedirs(dexdir); os.makedirs(a.out_dir, exist_ok=True)
    src = [os.path.join(a.proj, "java", "com", "clashlab", "annotator", "MainActivity.java")]
    run([os.path.join(jdk, "bin", "javac" + (".exe" if WIN else "")), "-source", "8", "-target", "8",
         "-bootclasspath", ajar, "-encoding", "UTF-8", "-d", classes] + src)
    cfiles = [os.path.join(dp, f) for dp, dn, fs in os.walk(classes) for f in fs if f.endswith(".class")]
    run([exe("d8"), "--release", "--lib", ajar, "--output", dexdir] + cfiles)
    base = os.path.join(build, "base.apk")
    run([exe("aapt2"), "link", "-o", base, "-I", ajar,
         "--manifest", os.path.join(a.proj, "AndroidManifest.xml"),
         "-A", os.path.join(a.proj, "assets"),
         "--min-sdk-version", "24", "--target-sdk-version", "28",
         "--version-code", str(a.version_code), "--version-name", a.version_name, "--auto-add-overlay"])
    with zipfile.ZipFile(base, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(dexdir, "classes.dex"), "classes.dex")
    aligned = os.path.join(build, "aligned.apk")
    run([exe("zipalign"), "-f", "4", base, aligned])
    ks = os.path.join(a.proj, "debug.keystore")
    if not os.path.exists(ks):
        run([os.path.join(jdk, "bin", "keytool" + (".exe" if WIN else "")), "-genkeypair", "-keystore", ks,
             "-storepass", "android", "-alias", "androiddebugkey", "-keypass", "android",
             "-dname", "CN=ClashLab, OU=Dev, O=ClashLab, L=CN, ST=CN, C=CN",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000"])
    out = os.path.join(a.out_dir, "ClashLabAnnotator.apk")
    if os.path.exists(out): os.remove(out)
    run([exe("apksigner"), "sign", "--ks", ks, "--ks-pass", "pass:android",
         "--key-pass", "pass:android", "--out", out, aligned])
    run([exe("apksigner"), "verify", out])
    print("[APK]", out, os.path.getsize(out), "bytes")
    print("BUILD_OK")

if __name__ == "__main__":
    main()
