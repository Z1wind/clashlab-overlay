# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
import os
import shutil

LDPLAYER_DIRS = [
    r"E:\leidian\LDPlayer9",
    r"D:\leidian\LDPlayer9",
    r"C:\leidian\LDPlayer9",
    r"C:\LDPlayer\LDPlayer9",
    r"C:\Program Files\LDPlayer\LDPlayer9",
]

COC_PACKAGES = [
    "com.supercell.clashofclans",
    "com.supercell.clashofclans.uc",
    "com.supercell.clashofclans.huawei",
    "com.supercell.clashofclans.oppo",
    "com.supercell.clashofclans.vivo",
    "com.tencent.tmgp.supercell.clashofclans",
]


def find_adb() -> str:
    env = os.environ.get("CLASHLAB_ADB")
    if env and os.path.exists(env):
        return env
    for d in LDPLAYER_DIRS:
        p = os.path.join(d, "adb.exe")
        if os.path.exists(p):
            return p
    which = shutil.which("adb")
    return which or ""


def find_ldconsole() -> str:
    for d in LDPLAYER_DIRS:
        p = os.path.join(d, "ldconsole.exe")
        if os.path.exists(p):
            return p
    return ""


@dataclass
class Config:
    adb: str = field(default_factory=find_adb)
    ldconsole: str = field(default_factory=find_ldconsole)
    serial: str = ""
    grid_n: int = 44
    wall_cost: float = 8.0
    dry_run: bool = True
    out_dir: str = "out"

    def resolved(self) -> "Config":
        if not self.adb:
            self.adb = find_adb()
        return self
