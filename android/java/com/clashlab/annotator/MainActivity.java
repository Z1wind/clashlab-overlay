package com.clashlab.annotator;

import android.annotation.SuppressLint;
import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private WebView web;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        web.addJavascriptInterface(new Bridge(), "AndroidBridge");
        web.loadUrl("file:///android_asset/annotate6.html");
        setContentView(web);
        if (Build.VERSION.SDK_INT < 29
                && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1);
        }
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    public class Bridge {
        private Uri lastUri = null;
        @JavascriptInterface
        public String saveFile(String filename, String content) {
            byte[] data = null;
            try {
                data = content.getBytes("UTF-8");
                String where;
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentValues cv = new ContentValues();
                    cv.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
                    cv.put(MediaStore.MediaColumns.MIME_TYPE, "application/json");
                    cv.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                    Uri uri = getContentResolver().insert(
                            MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv);
                    if (uri == null) return "ERR:mediastore null";
                    OutputStream os = getContentResolver().openOutputStream(uri);
                    os.write(data);
                    os.close();
                    lastUri = uri;
                    where = "Downloads/" + filename;
                } else {
                    File dir = Environment.getExternalStoragePublicDirectory(
                            Environment.DIRECTORY_DOWNLOADS);
                    if (!dir.exists()) dir.mkdirs();
                    File f = new File(dir, filename);
                    if (f.exists()) f.delete();
                    FileOutputStream fos = new FileOutputStream(f);
                    fos.write(data);
                    fos.close();
                    where = f.getAbsolutePath();
                }
                return "OK:" + where;
            } catch (Exception e) {
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
                    if (data == null) data = content.getBytes("UTF-8");
                    File dir = new File(getExternalFilesDir(null), "Downloads");
                    if (!dir.exists()) dir.mkdirs();
                    File f = new File(dir, filename);
                    FileOutputStream fos = new FileOutputStream(f);
                    fos.write(data);
                    fos.close();
                    return "OK(private):" + f.getAbsolutePath();
                } catch (Exception e2) {
                    return "ERR:" + e.toString();
                }
            }
        }

        @JavascriptInterface
        public void shareLast() {
            if (lastUri == null) return;
            final Uri uri = lastUri;
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    Intent send = new Intent(Intent.ACTION_SEND);
                    send.setType("application/json");
                    send.putExtra(Intent.EXTRA_STREAM, uri);
                    send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    Intent chooser = Intent.createChooser(send, "把标注数据发给我");
                    startActivity(chooser);
                }
            });
        }

        @JavascriptInterface
        public void toast(final String msg) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    Toast.makeText(MainActivity.this, msg, Toast.LENGTH_SHORT).show();
                }
            });
        }
    }
}
