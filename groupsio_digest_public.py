#!/usr/bin/env python3
"""
Groups.io Digest
Fetches recent activity from your Groups.io mailing lists and produces
an HTML report (opened in your browser) and a plain-text summary file.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import os
import webbrowser
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — edit these values
# ---------------------------------------------------------------------------

API_KEY = "648b455bac3c15d9069f51ed23ea8412aff4f9cdcf6d56957c0f5fa8582d4aea"   # From groups.io/settings/apikeys

LOOKBACK_DAYS = 7               # How many days back to check

OUTPUT_DIR = Path.home() / "Documents" / "GroupsIO_Digest"

GROUPS = [
    # ── General groups ────────────────────────────────────────────────────
    {"name": "SHARI",                 "group": "SHARI",                              "domain": "groups.io"},
    {"name": "FT-891",                "group": "FT-891",                             "domain": "groups.io"},
    {"name": "KM4ACK",                "group": "KM4ACK",                             "domain": "groups.io"},
    {"name": "LinuxHam",              "group": "linuxham",                           "domain": "groups.io"},
    {"name": "NanoVNA",               "group": "nanovna-users",                      "domain": "groups.io"},
    {"name": "Mobilinkd TNC",         "group": "mobilinkd",                          "domain": "groups.io"},
    {"name": "Supermon",              "group": "Supermon",                           "domain": "groups.io"},
    {"name": "Winlink",               "group": "WinLink",                            "domain": "groups.io"},
    {"name": "TinySA",                "group": "tinysa",                             "domain": "groups.io"},
    {"name": "YCAT",                  "group": "ycat",                               "domain": "groups.io"},
    {"name": "Halibut Electronics",   "group": "general",                            "domain": "halibut-electronics.groups.io", "restricted": True},
    # ── ARRL subgroups (format: parentname+subgroupslug) ──────────────────
    {"name": "ARRL: Groups",          "group": "arrl",                               "domain": "groups.io"},
    {"name": "ARRL: LoTW",            "group": "arrl+lotw",                          "domain": "groups.io"},
    {"name": "ARRL: HF Band Planng",  "group": "arrl+hf-band-planning",              "domain": "groups.io"},
    {"name": "ARRL: New Hams",        "group": "arrl+new-hams",                      "domain": "groups.io"},
    # ── PNW Digital / DMR subgroups (format: parentname+subgroupslug) ─────
    # {"name": "PNW DMR",               "group": "dmr+PNW",                            "domain": "groups.io"},
    # {"name": "PNW CPS / Codeplugs",   "group": "dmr+PNW-CPS-Programming-Codeplugs",  "domain": "groups.io"},
    # {"name": "PNW MeshCore",          "group": "dmr+pnwd-meshcore",                  "domain": "groups.io", "restricted": True},
    # --- Misc Subgroups ----
    {"name": "JS8Call",               "group": "main",                               "domain": "js8call.groups.io"},
    {"name": "Packtenna",             "group": "main",                               "domain": "packtenna.groups.io"},
    {"name": "EMComm RatPack",        "group": "main",                               "domain": "sec-emcomm.groups.io"},
]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def make_auth_header(api_key):
    return {"Authorization": f"Bearer {api_key}"}


def api_get(url, api_key):
    """Make a GET request to the Groups.io API. Returns parsed JSON or raises."""
    req = urllib.request.Request(url, headers=make_auth_header(api_key))
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            raise RuntimeError(err.get("extra_message") or err.get("type") or f"HTTP {e.code}")
        except json.JSONDecodeError:
            raise RuntimeError(f"HTTP {e.code}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def verify_api_key(api_key):
    """Quick check that the API key works."""
    url = "https://groups.io/api/v1/getsubs?limit=1"
    data = api_get(url, api_key)
    if data.get("object") == "error":
        raise RuntimeError(data.get("extra_message") or "Invalid API key")
    return True


def fetch_group_topics(group_info, api_key, lookback_days):
    """Fetch recent topics for a single group. Returns dict with total, topics, error."""
    domain = group_info["domain"]
    group = group_info["group"]

    if domain == "groups.io":
        base = "https://groups.io"
    else:
        base = f"https://{domain}"

    params = urllib.parse.urlencode({
        "group_name": group,
        "limit": 100,
        "sort_field": "activity",
    })
    url = f"{base}/api/v1/gettopics?{params}"

    data = api_get(url, api_key)

    if data.get("object") == "error":
        raise RuntimeError(data.get("extra_message") or data.get("type") or "Unknown error")

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)
    recent = []
    for topic in data.get("data") or []:
        updated_str = topic.get("updated", "")
        try:
            # Groups.io returns RFC3339 timestamps
            updated_str = updated_str.replace("Z", "+00:00")
            updated = datetime.datetime.fromisoformat(updated_str)
            if updated >= cutoff:
                recent.append(topic)
        except (ValueError, AttributeError):
            pass

    total_msgs = sum(t.get("num_messages", 1) for t in recent)
    topics = [
        {
            "subject": t.get("subject") or "(no subject)",
            "count": t.get("num_messages", 1),
            "id": t.get("id"),
        }
        for t in recent[:10]
    ]

    return {"total": total_msgs, "topics": topics}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def group_url(group_info):
    domain = group_info["domain"]
    group = group_info["group"]
    if domain == "groups.io":
        return f"https://groups.io/g/{group}"
    return f"https://{domain}/g/{group}"


def build_html_report(results, lookback_days, generated_at):
    active   = [r for r in results if r.get("data") and r["data"]["total"] > 0]
    quiet    = [r for r in results if r.get("data") and r["data"]["total"] == 0]
    errors   = [r for r in results if r.get("error")]

    # Sort active groups by message count descending
    active.sort(key=lambda r: r["data"]["total"], reverse=True)

    date_str = generated_at.strftime("%B %d, %Y at %I:%M %p")
    window_str = f"Past {lookback_days} day{'s' if lookback_days != 1 else ''}"

    active_rows = ""
    for r in active:
        name = r["group"]["name"]
        url  = group_url(r["group"])
        total = r["data"]["total"]
        topics = r["data"]["topics"]
        base = group_url(r["group"])
        topic_items = "".join(
            (f'<li><a href="{base}/topic/{t["id"]}" target="_blank" rel="noopener noreferrer">{t["subject"]}</a> <span class="msg-count">({t["count"]})</span></li>'
             if t.get("id") else
             f'<li>{t["subject"]} <span class="msg-count">({t["count"]})</span></li>')
            for t in topics[:5]
        )
        active_rows += f"""
        <div class="group-card active">
          <div class="group-header">
            <a class="group-name" href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>
            <span class="badge">{total} msg{'s' if total != 1 else ''}</span>
          </div>
          <ul class="topic-list">{topic_items}</ul>
        </div>"""

    quiet_names = " &middot; ".join(r["group"]["name"] for r in quiet) if quiet else ""
    quiet_section = f"""
        <div class="group-card quiet">
          <div class="group-header">
            <span class="group-name muted">No activity ({len(quiet)} group{'s' if len(quiet) != 1 else ''})</span>
          </div>
          <p class="quiet-list">{quiet_names}</p>
        </div>""" if quiet else ""

    error_rows = ""
    for r in errors:
        error_rows += f'<div class="error-row"><strong>{r["group"]["name"]}</strong>: {r["error"]}</div>'
    error_section = f"""
        <div class="group-card error-card">
          <div class="group-header"><span class="group-name err">Fetch errors ({len(errors)})</span></div>
          {error_rows}
        </div>""" if errors else ""

    total_groups = len(results)
    total_msgs   = sum(r["data"]["total"] for r in active)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Groups.io Digest &mdash; {date_str}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #f5f5f0; color: #1a1a1a; padding: 2rem 1rem; font-size: 15px; }}
  .container {{ max-width: 740px; margin: 0 auto; }}
  h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 4px; }}
  .meta {{ font-size: 13px; color: #777; margin-bottom: 1.5rem; }}
  .stats {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
  .stat {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 8px;
           padding: .6rem 1rem; font-size: 13px; color: #555; }}
  .stat strong {{ font-size: 20px; font-weight: 600; color: #1a1a1a; display: block; }}
  .group-card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 10px;
                 padding: 1rem 1.25rem; margin-bottom: .75rem; }}
  .group-card.quiet {{ background: #fafafa; }}
  .group-card.error-card {{ border-color: #f5c6c6; background: #fff8f8; }}
  .group-header {{ display: flex; align-items: baseline; gap: .75rem; margin-bottom: .5rem; flex-wrap: wrap; }}
  .group-name {{ font-size: 15px; font-weight: 600; color: #1a1a1a; text-decoration: none; }}
  .group-name:hover {{ text-decoration: underline; }}
  .group-name.muted {{ color: #888; font-weight: 500; }}
  .group-name.err {{ color: #c0392b; }}
  .badge {{ font-size: 11px; background: #e8f5e9; color: #2e7d32;
            padding: 2px 8px; border-radius: 20px; font-weight: 500; white-space: nowrap; }}
  .topic-list {{ list-style: none; padding: 0; }}
  .topic-list li {{ font-size: 13px; color: #444; padding: 3px 0;
                    border-bottom: 1px solid #f0f0f0; }}
  .topic-list li:last-child {{ border-bottom: none; }}
  .msg-count {{ color: #aaa; font-size: 12px; }}
  .topic-list a {{ color: #2563ab; text-decoration: none; }}
  .topic-list a:hover {{ text-decoration: underline; }}
  .quiet-list {{ font-size: 13px; color: #999; line-height: 1.7; }}
  .error-row {{ font-size: 13px; color: #c0392b; margin-top: 4px; }}
  .footer {{ font-size: 12px; color: #aaa; text-align: center; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>&#128243; Groups.io Digest</h1>
  <p class="meta">{window_str} &nbsp;&middot;&nbsp; Generated {date_str}</p>
  <div class="stats">
    <div class="stat"><strong>{total_groups}</strong> groups checked</div>
    <div class="stat"><strong>{len(active)}</strong> active</div>
    <div class="stat"><strong>{total_msgs}</strong> total messages</div>
    <div class="stat"><strong>{len(quiet)}</strong> quiet</div>
  </div>
  {active_rows}
  {quiet_section}
  {error_section}
  <p class="footer">groupsio_digest.py &nbsp;&middot;&nbsp; {date_str}</p>
</div>
</body>
</html>"""
    return html


def build_text_report(results, lookback_days, generated_at):
    active = [r for r in results if r.get("data") and r["data"]["total"] > 0]
    quiet  = [r for r in results if r.get("data") and r["data"]["total"] == 0]
    errors = [r for r in results if r.get("error")]
    active.sort(key=lambda r: r["data"]["total"], reverse=True)

    date_str   = generated_at.strftime("%Y-%m-%d %H:%M")
    window_str = f"Past {lookback_days} day{'s' if lookback_days != 1 else ''}"
    total_msgs = sum(r["data"]["total"] for r in active)

    lines = [
        "=" * 60,
        "  GROUPS.IO DIGEST",
        f"  {window_str}  |  Generated {date_str}",
        "=" * 60,
        f"  {len(results)} groups checked  |  {len(active)} active  |  {total_msgs} messages",
        "",
    ]

    for r in active:
        name  = r["group"]["name"]
        total = r["data"]["total"]
        topics = r["data"]["topics"]
        lines.append(f"{'─' * 60}")
        lines.append(f"  {name}  [{total} message{'s' if total != 1 else ''}]")
        lines.append(f"  {group_url(r['group'])}")
        for t in topics[:5]:
            lines.append(f"    • {t['subject']}  ({t['count']})")
        lines.append("")

    if quiet:
        lines.append("─" * 60)
        lines.append("  QUIET (no activity):")
        lines.append("  " + ", ".join(r["group"]["name"] for r in quiet))
        lines.append("")

    restricted = [r for r in results if r.get("restricted")]
    if restricted:
        lines += [chr(9472) * 60, "  RESTRICTED (owner disabled API access):"]
        lines.append("  " + ", ".join(r["group"]["name"] for r in restricted))
        lines.append("")
    if errors:
        lines.append("─" * 60)
        lines.append("  ERRORS:")
        for r in errors:
            lines.append(f"  {r['group']['name']}: {r['error']}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("Groups.io Digest")
    print("=" * 40)

    # Check API key is configured
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\nERROR: Please open groupsio_digest.py in a text editor")
        print("       and replace YOUR_API_KEY_HERE with your actual API key.")
        print("       Get one at: https://groups.io/settings/apikeys")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Verify key
    print(f"\nVerifying API key...", end=" ", flush=True)
    try:
        verify_api_key(API_KEY)
        print("OK")
    except RuntimeError as e:
        print(f"FAILED\n\nError: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch each group
    print(f"\nFetching {len(GROUPS)} groups (past {LOOKBACK_DAYS} days)...\n")
    results = []
    pad = max(len(g["name"]) for g in GROUPS) + 2

    for g in GROUPS:
        label = g["name"].ljust(pad)
        print(f"  {label}", end="", flush=True)
        if g.get("restricted"):
            print("access restricted by group owner")
            results.append({"group": g, "data": None, "restricted": True})
            continue
        try:
            data = fetch_group_topics(g, API_KEY, LOOKBACK_DAYS)
            if data["total"] > 0:
                print(f"{data['total']} messages, {len(data['topics'])} topics")
            else:
                print("quiet")
            results.append({"group": g, "data": data})
        except RuntimeError as e:
            print(f"ERROR: {e}")
            results.append({"group": g, "data": None, "error": str(e)})

    # Generate reports
    now = datetime.datetime.now()
    date_slug = now.strftime("%Y-%m-%d_%H%M")

    html_path = OUTPUT_DIR / f"digest_{date_slug}.html"
    txt_path  = OUTPUT_DIR / f"digest_{date_slug}.txt"

    print(f"\nWriting reports to {OUTPUT_DIR} ...", end=" ", flush=True)

    html_content = build_html_report(results, LOOKBACK_DAYS, now)
    html_path.write_text(html_content, encoding="utf-8")

    txt_content = build_text_report(results, LOOKBACK_DAYS, now)
    txt_path.write_text(txt_content, encoding="utf-8")

    print("done")

    # Print text summary to console too
    print()
    print(txt_content)

    # Open HTML in browser
    print(f"\nOpening HTML report in browser...")
    webbrowser.open(html_path.as_uri())

    print(f"\nFiles saved:")
    print(f"  HTML: {html_path}")
    print(f"  Text: {txt_path}")
    print()
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
