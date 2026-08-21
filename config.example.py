"""
Example config for groupsio_digest_public.py

Copy this file to config.py and fill in your real values.
config.py is listed in .gitignore and will never be committed.
"""

from pathlib import Path

API_KEY = "YOUR_API_KEY_HERE"   # From groups.io/settings/apikeys

LOOKBACK_DAYS = 7               # How many days back to check

OUTPUT_DIR = Path.home() / "Documents" / "Groups.io Digests"

GROUPS = [
    # ── General groups ────────────────────────────────────────────────────
    {"name": "LinuxHam", "group": "linuxham", "domain": "groups.io"},

    # ── Subgroups (format: parentname+subgroupslug) ────────────────────────
    # {"name": "ARRL: LoTW", "group": "arrl+lotw", "domain": "groups.io"},

    # ── Restricted-access groups (owner disabled API access) ───────────────
    # {"name": "Example", "group": "example", "domain": "example.groups.io", "restricted": True},
]
