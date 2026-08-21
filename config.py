"""
Personal config for groupsio_digest_public.py — NOT committed to git.
"""

from pathlib import Path

API_KEY = "e68e31d8ea2707d36b05eb5bc2b7f0044c4ef5fa0f1a3dbed642c735916afde"   # From groups.io/settings/apikeys

LOOKBACK_DAYS = 7               # How many days back to check

OUTPUT_DIR = Path.home() / "Documents" / "Groups.io Digests"

GROUPS = [
    # ── General groups ────────────────────────────────────────────────────
    {"name": "SHARI",                 "group": "SHARI",                              "domain": "groups.io"},
    {"name": "FT-891",                "group": "FT-891",                             "domain": "groups.io"},
    {"name": "KM4ACK",                "group": "KM4ACK-PI",                          "domain": "groups.io"},
    {"name": "LinuxHam",              "group": "linuxham",                           "domain": "groups.io"},
    {"name": "NanoVNA",               "group": "nanovna-users",                      "domain": "groups.io"},
    {"name": "Mobilinkd TNC",         "group": "mobilinkd",                          "domain": "groups.io"},
    {"name": "Supermon",              "group": "Supermon",                           "domain": "groups.io"},
    {"name": "Winlink",               "group": "WinLink",                            "domain": "groups.io"},
    {"name": "TinySA",                "group": "tinysa",                             "domain": "groups.io"},
    {"name": "YCAT",                  "group": "ycat",                               "domain": "groups.io"},
    {"name": "Halibut Electronics",   "group": "general",                            "domain": "halibut-electronics.groups.io", "restricted": True},
    # ── ARRL subgroups (format: parentname+subgroupslug) ──────────────────
    # {"name": "ARRL: Groups",          "group": "arrl",                               "domain": "groups.io"},
    # {"name": "ARRL: LoTW",            "group": "arrl+lotw",                          "domain": "groups.io"},
    # {"name": "ARRL: HF Band Planng",  "group": "arrl+hf-band-planning",              "domain": "groups.io"},
    # {"name": "ARRL: New Hams",        "group": "arrl+new-hams",                      "domain": "groups.io"},
    # ── PNW Digital / DMR subgroups (format: parentname+subgroupslug) ─────
    # {"name": "PNW DMR",               "group": "dmr+PNW",                            "domain": "groups.io"},
    # {"name": "PNW CPS / Codeplugs",   "group": "dmr+PNW-CPS-Programming-Codeplugs",  "domain": "groups.io"},
    # {"name": "PNW MeshCore",          "group": "dmr+pnwd-meshcore",                  "domain": "groups.io", "restricted": True},
    # --- Misc Subgroups ----
    {"name": "JS8Call",               "group": "main",                               "domain": "js8call.groups.io",             "restricted": True},
    {"name": "Packtenna",             "group": "main",                               "domain": "packtenna.groups.io",           "restricted": True},
    {"name": "EMComm RatPack",        "group": "main",                               "domain": "sec-emcomm.groups.io",          "restricted": True},
]
