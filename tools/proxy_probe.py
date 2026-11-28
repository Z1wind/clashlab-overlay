# -*- coding: utf-8 -*-
import sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print("proxies:", urllib.request.getproxies())
import winreg
try:
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
    for name in ("ProxyEnable", "ProxyServer", "AutoConfigURL"):
        try:
            v, _ = winreg.QueryValueEx(k, name); print(name, "=", v)
        except FileNotFoundError:
            print(name, "= (none)")
except Exception as e:
    print("winreg fail", e)
