#!/usr/bin/env python3
"""Fetch the Minecraft Java 26.3 files the Horizon launcher needs, without an
account, from Mojang's public endpoints (the same ones the official launcher
uses). Builds the standard game folder the Horizon launcher reads:

    <game>/versions/26.3/26.3.json   version manifest
    <game>/versions/26.3/26.3.jar     client jar
    <game>/26.3-server.jar            server jar
    <game>/libraries/...              this system's libraries
    <game>/assets/...                 asset index, sounds, panorama, fonts

Cross-platform port of slycat555/horizon-offline-setup. The one thing that made
the original Linux-only -- the game-folder path, the library OS rules and the
`uname -r` probe -- now follows the running system, so the same script works on
Linux (x86-64), Windows (x64) and macOS (x86-64).

The game folder is `--minecraft-dir`, else HORIZON_MINECRAFT_DIR, else the
official launcher's default: ~/.minecraft (Linux), %APPDATA%\\.minecraft
(Windows), ~/Library/Application Support/minecraft (macOS) -- the exact same
resolution Horizon's horizon-prepare (artifacts.rs) and tools/lab.py use.

Every file is verified against the SHA-1 checksums Mojang publishes (and the
ones Horizon's research-lock.json pins). No Minecraft files are stored in this
repository; the script only downloads them on demand.
"""
import concurrent.futures
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

VERSION = "26.3"
# The OS name Mojang's library rules use for this system: "linux", "windows", "osx".
OS_NAME = {"darwin": "osx", "win32": "windows"}.get(sys.platform, "linux")
# x86-64 machine names under which the rules' arch patterns match.
ARCHES = ["x86_64", "amd64", "x64"]
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
# The 26.3 version JSONs Mojang published (Horizon v0.2.32 research-lock.json).
ACCEPTED_JSON_SHA1 = [
    "11f1aefe473eefba0af62e3286c33b692807b2eb",
    "4fe1aa1ef8da1cb95c5bad1fb98890ca56dd8ca3",
    "702fe59163c6ee6578607daa85811d9bc9c7cc40",
    "61fff1316bd50312624a858bbb5eb18fa45208ed",
    "5df1795e16eea19d75b923d66ecca9ce183353c5",
]
CLIENT_SHA1 = "e877b6a07acd633fb3bb475002175cec036e7b87"
SERVER_SHA1 = "33680f5f2ac32864d6d7cf5e56a705fdb3e05f4c"
PANORAMA = ["minecraft/textures/gui/title/background/panorama_%d.png" % i for i in range(6)] + \
           ["minecraft/textures/gui/title/background/panorama_overlay.png"]


def minecraft_dir(override=None):
    """The official launcher's game folder, mirroring horizon-prepare / tools/lab.py."""
    if override or os.environ.get("HORIZON_MINECRAFT_DIR"):
        return Path(override or os.environ["HORIZON_MINECRAFT_DIR"]).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "minecraft"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / ".minecraft"
    return Path.home() / ".minecraft"


def parse_override(argv):
    """`--minecraft-dir PATH` (or `-d PATH`) beats HORIZON_MINECRAFT_DIR."""
    override = None
    for i, a in enumerate(argv):
        if a in ("--minecraft-dir", "-d") and i + 1 < len(argv):
            override = argv[i + 1]
        elif a in ("--help", "-h"):
            print(__doc__.strip())
            sys.exit(0)
    return override


def sha1_file(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, dest, sha1=None, tries=6):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.isfile(dest) and (sha1 is None or sha1_file(dest) == sha1):
        return None
    for a in range(tries):
        tmp = dest + ".part"
        try:
            urllib.request.urlretrieve(url, tmp)
            if sha1 is not None and sha1_file(tmp) != sha1:
                os.remove(tmp)
                continue
            os.replace(tmp, dest)
            return None
        except Exception as e:
            try:
                os.remove(tmp)
            except OSError:
                pass
            if a == tries - 1:
                return "%s: %s" % (url, e)
            time.sleep(1 + a)
    return "%s: checksum mismatch" % url


def ends(c, s):
    return c == s or (c.endswith(s) and c[: -len(s)].endswith("-"))


def library_allowed(lib, os_version):
    """The official launcher's rules, last matching rule decides (this system's OS)."""
    rules = lib.get("rules") or []
    ok = not rules
    for r in rules:
        ros = r.get("os") or {}
        if ros.get("name", OS_NAME) != OS_NAME:
            continue
        if "arch" in ros and not any(re.fullmatch(ros["arch"], x) for x in ARCHES):
            continue
        if "version" in ros and not re.search(ros["version"], os_version):
            continue
        if r.get("features"):
            continue
        ok = r.get("action") == "allow"
    return ok


def native_ok(lib):
    parts = (lib.get("name") or "").split(":")
    cl = parts[3] if len(parts) > 3 else ""
    if any(ends(cl, s) for s in ("arm64", "aarch64", "aarch_64")):
        return False
    return True


def wanted(name):
    return (name == "minecraft/sounds.json" or name.startswith("minecraft/sounds/")
            or name.startswith("minecraft/font/") or name in PANORAMA)


def main():
    override = parse_override(sys.argv[1:])
    mc = minecraft_dir(override)
    os_version = platform.release() or platform.version()
    print("OS: %s  |  game folder: %s" % (OS_NAME, mc))

    print("Fetching the Mojang version manifest ...")
    with urllib.request.urlopen(MANIFEST_URL, timeout=60) as r:
        versions = json.load(r)["versions"]
    entry = next((v for v in versions if v["id"] == VERSION), None)
    if not entry or entry["sha1"] not in ACCEPTED_JSON_SHA1:
        print("26.3 not found or an unknown republish; update the accepted SHA-1 list")
        sys.exit(1)
    manifest = json.load(urllib.request.urlopen(entry["url"], timeout=60))
    assert manifest["downloads"]["client"]["sha1"] == CLIENT_SHA1
    assert manifest["downloads"]["server"]["sha1"] == SERVER_SHA1

    vdir = mc / "versions" / VERSION
    vdir.mkdir(parents=True, exist_ok=True)
    vjson = vdir / (VERSION + ".json")
    if not vjson.is_file():
        with urllib.request.urlopen(entry["url"], timeout=60) as r, open(vjson, "wb") as f:
            shutil.copyfileobj(r, f)
    print("version json in place")

    jobs = [(manifest["downloads"]["client"]["url"], str(vdir / (VERSION + ".jar")), CLIENT_SHA1),
            (manifest["downloads"]["server"]["url"], str(mc / (VERSION + "-server.jar")), SERVER_SHA1)]
    index = manifest["assetIndex"]
    idx_dest = mc / "assets" / "indexes" / (index["id"] + ".json")
    e = fetch(index["url"], str(idx_dest), index["sha1"])
    if e:
        print("asset index failed:", e)
        sys.exit(1)
    print("asset index downloaded")

    n = 0
    for lib in manifest.get("libraries", []):
        art = (lib.get("downloads") or {}).get("artifact")
        if not art or not library_allowed(lib, os_version) or not native_ok(lib):
            continue
        p = art["path"]
        if p.startswith("/") or ".." in p.split("/"):
            continue
        jobs.append((art["url"], str(mc / "libraries" / Path(*p.split("/"))), art["sha1"]))
        n += 1
    print("libraries: %d" % n)

    objects = json.load(open(idx_dest))["objects"]
    m = 0
    for name, info in objects.items():
        if not wanted(name):
            continue
        h = info["hash"]
        jobs.append(("https://resources.download.minecraft.net/%s/%s" % (h[:2], h),
                     str(mc / "assets" / "objects" / h[:2] / h), h))
        m += 1
    print("sound, panorama and font objects: %d" % m)

    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for err in pool.map(lambda j: fetch(*j), jobs):
            if err:
                failures.append(err)
    print("done: %d downloads, %d failures" % (len(jobs), len(failures)))
    for f in failures[:20]:
        print("FAILED:", f)
    if failures:
        sys.exit(1)
    print("""
Next, tell the Horizon launcher about the folder and play offline:
    horizon-launcher settings minecraft-dir "%s"
    horizon-launcher account offline
    horizon-launcher prepare --minecraft "%s"
    horizon-launcher play
The launcher downloads Java 25 and the server jar itself when it prepares.""" % (mc, mc))


if __name__ == "__main__":
    main()