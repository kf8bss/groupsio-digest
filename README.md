# Groups.io Digest

A Python script that checks your Groups.io mailing lists and produces a daily digest report — an HTML file that opens in your browser with clickable topic links, and a plain-text copy for archiving or forwarding.

No external libraries required. Runs on Windows, macOS, and Linux.

---

## What it does

Each time you run it, the script:

1. Connects to the Groups.io API using your API key
2. Fetches recent topics from every group you've configured
3. Filters to activity within your chosen time window (default: 7 days)
4. Produces a ranked HTML report (most active groups first) with clickable thread titles
5. Saves a plain-text copy
6. Opens the HTML report in your default browser

Groups with no recent activity are collected at the bottom. Groups where the owner has disabled API access are noted separately rather than shown as errors.

---

## Requirements

- Python 3.8 or later
- A Groups.io account with an API key
- Membership in the groups you want to monitor

No `pip install` needed — the script uses only Python's standard library.

---

## Installation

### Windows (ARM or x64)

1. Install Python from the **Microsoft Store** — search for *Python 3.13*. This installs the native ARM64 build on ARM devices automatically.

2. Download `groupsio_digest.py` and save it somewhere convenient, such as your Desktop or Documents folder.

### macOS / Linux

Python 3 is usually already installed. Download `groupsio_digest.py` and you're ready.

---

## Getting your API key

1. Log into [groups.io](https://groups.io) and go to **Settings → API Keys**
   (direct link: https://groups.io/settings/apikeys)
2. Click **+ Create API Key**, give it a name (e.g. *Groups Digest*), and click Create
3. **Copy the key immediately** — Groups.io only shows the full key value once
4. Paste it into the script (see Configuration below)

The API key authenticates as you, so it can only access groups you're already a member of.

---

## Configuration

Open `groupsio_digest.py` in any text editor (Notepad, VSCode, etc.) and edit the values near the top of the file.

### API key

```python
API_KEY = "paste-your-key-here"
```

### Lookback window

```python
LOOKBACK_DAYS = 7    # Change to any number of days
```

### Output folder

```python
OUTPUT_DIR = Path.home() / "Documents" / "GroupsIO_Digest"
```

Reports are saved here as timestamped files, e.g. `digest_2026-06-10_0830.html`.

---

## Adding and removing groups

The `GROUPS` list near the top of the script controls which groups are monitored. Each entry is a dictionary with three fields:

```python
{"name": "Display Name", "group": "slug", "domain": "groups.io"}
```

- **name** — how it appears in the report (your choice)
- **group** — the slug from the group's URL
- **domain** — usually `groups.io`; use the subdomain for groups with custom domains

### Standard groups

For a group at `https://groups.io/g/linuxham`:

```python
{"name": "LinuxHam", "group": "linuxham", "domain": "groups.io"},
```

### Subgroups

Groups.io supports parent groups with subgroups underneath them. These have their own subdomain (e.g. `ardc.groups.io`) but the API uses a `parent+subgroup` slug format:

For a subgroup at `https://ardc.groups.io/g/44net`:

```python
{"name": "ARDC: 44Net", "group": "ardc+44net", "domain": "groups.io"},
```

The pattern is always `parentname+subgroupslug`, all lowercase, pointed at plain `groups.io` as the domain.

More examples:

```python
# https://ardc.groups.io/g/44Net-connect
{"name": "ARDC: 44Net Connect", "group": "ardc+44Net-connect", "domain": "groups.io"},

# https://dmr.groups.io/g/PNW
{"name": "PNW DMR", "group": "dmr+PNW", "domain": "groups.io"},
```

### Groups with restricted API access

Some group owners disable API access to their archive. There's nothing you can do about this from your end — it's a setting they control. Mark these groups with `"restricted": True` to skip them cleanly:

```python
{"name": "Example Group", "group": "example", "domain": "example.groups.io", "restricted": True},
```

They'll appear in a neutral *API access restricted* section rather than the error list.

---

## Running the script

**Windows:** Right-click `groupsio_digest.py` → Open with → Python

**Command line (all platforms):**
```
python groupsio_digest.py
```

The script prints progress to the console as it fetches each group, then opens the HTML report in your browser when done.

---

## Scheduling automatic runs

### Windows — Task Scheduler

1. Press **Win + S**, search for *Task Scheduler*, open it
2. Click **Create Basic Task** on the right
3. Name it *Groups.io Digest*, click Next
4. Choose **Daily**, set your preferred time (e.g. 7:00 AM)
5. Choose **Start a program**
6. Program/script: `python`
7. Add arguments: `"C:\Users\YourName\Desktop\groupsio_digest.py"`
   (adjust path to where you saved the script)
8. Click Finish

### macOS / Linux — cron

```
0 7 * * * /usr/bin/python3 /home/yourname/groupsio_digest.py
```

---

## Authentication notes

Groups.io API keys use HTTP Bearer token authentication. The script sends your key as an `Authorization: Bearer` header on every request. The key is stored only in the script file on your local machine — it is never sent anywhere except directly to the groups.io API.

If you belong to groups under different Groups.io accounts (different email addresses), you can add a second API key for the other account and assign it per-group. See the comments in the script for details.

---

## Troubleshooting

**`unauthorized_error` on startup**
Your API key isn't being accepted. Double-check it matches exactly what's shown at groups.io/settings/apikeys — no extra spaces or missing characters.

**`group_not_found` for a group**
The slug in your GROUPS list doesn't match what Groups.io expects. Visit the group in your browser, copy the URL, and check the slug. For subgroups, make sure you're using the `parent+subgroup` format described above.

**`inadequate_permissions` for a group**
The group owner has restricted API access. Add `"restricted": True` to that group's entry to suppress the error.

**Script window closes immediately on Windows**
Run it from the command prompt instead so you can read any error messages:
```
python "%USERPROFILE%\Desktop\groupsio_digest.py"
```

**All topics show message count of (1)**
You may have an older version of the script. The topic message count field in the Groups.io API is `num_messages`, not `message_count`. Make sure you're running the current version.

---

## Report format

### HTML report
Opens automatically in your browser. Groups are sorted by total message count (most active first). Each topic title is a clickable link that takes you directly to that thread on Groups.io.

### Text report
Saved alongside the HTML file. Same information in plain text — useful for forwarding by email or reading in a terminal.

Both files are named with a timestamp: `digest_YYYY-MM-DD_HHMM.html` / `.txt`

---

## Limitations

- The Groups.io API returns up to 100 topics per group per request. For very high-volume groups this may not capture everything within the lookback window, though it's sufficient for typical amateur radio mailing lists.
- The script shows up to 5 topics per group in the report. Edit the `[:5]` slice in `build_html_report()` and `build_text_report()` to show more.
- Groups where the owner has disabled API access cannot be monitored regardless of your membership status.

---

*Written for amateur radio operators monitoring Groups.io mailing lists, but works for any Groups.io group.*
