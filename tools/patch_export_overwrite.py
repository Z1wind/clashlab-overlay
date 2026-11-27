# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
# 1) 公开目录写入前先删旧文件
old1 = """                    File f = new File(dir, filename);
                    FileOutputStream fos = new FileOutputStream(f);"""
new1 = """                    File f = new File(dir, filename);
                    if (f.exists()) f.delete();
                    FileOutputStream fos = new FileOutputStream(f);"""
if old1 in t:
    t = t.replace(old1, new1, 1)
else:
    print("old1 miss")
# 2) catch 里先尝试带时间戳的公开目录写入
old2 = """            } catch (Exception e) {
                // API<29 兜底：用 MediaStore 兼容方式写入「下载」"""
new2 = """            } catch (Exception e) {
                // 先尝试「下载」目录 + 时间戳文件名，避开旧文件占位
                try {
                    File dir = Environment.getExternalStoragePublicDirectory(
                            Environment.DIRECTORY_DOWNLOADS);
                    if (!dir.exists()) dir.mkdirs();
                    String alt = (System.currentTimeMillis() / 1000) + "_" + filename;
                    File f = new File(dir, alt);
                    FileOutputStream fos = new FileOutputStream(f);
                    fos.write(data);
                    fos.close();
                    return "OK:" + f.getAbsolutePath();
                } catch (Exception e4) {
                    // 继续 MediaStore 兜底
                }
                // API<29 兜底：用 MediaStore 兼容方式写入「下载」"""
if old2 in t:
    t = t.replace(old2, new2, 1)
else:
    print("old2 miss")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("java patched")
