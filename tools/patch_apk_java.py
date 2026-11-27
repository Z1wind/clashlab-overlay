# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
old = """            } catch (Exception e) {
                try {
                    if (data == null) data = content.getBytes("UTF-8");"""
new = """            } catch (Exception e) {
                // API<29 兜底：用 MediaStore 兼容方式写入「下载」
                if (Build.VERSION.SDK_INT < 29 && data != null) {
                    try {
                        ContentValues mv = new ContentValues();
                        mv.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
                        mv.put(MediaStore.MediaColumns.MIME_TYPE, "application/json");
                        mv.put("_data", Environment.getExternalStoragePublicDirectory(
                                Environment.DIRECTORY_DOWNLOADS).getAbsolutePath() + "/" + filename);
                        Uri mu = getContentResolver().insert(MediaStore.Files.getContentUri("external"), mv);
                        if (mu != null) {
                            OutputStream mos = getContentResolver().openOutputStream(mu);
                            mos.write(data);
                            mos.close();
                            lastUri = mu;
                            return "OK:Download/" + filename;
                        }
                    } catch (Exception e3) {
                        // 继续走私有目录
                    }
                }
                try {
                    if (data == null) data = content.getBytes("UTF-8");"""
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("legacy MediaStore fallback added")
else:
    print("anchor miss")
