# Groups.io Digest

A Python script that checks configured Groups.io mailing lists and produces a daily digest report. Runs automatically every morning via GitHub Actions and publishes the result to a private, access-controlled web page — no laptop, browser, or manual step required.

Forked from [EtherHamRadio/groupsio-digest](https://github.com/EtherHamRadio/groupsio-digest) and customized for KF8BSS.

---

## How it works

Two repos, two services, one daily flow:

```
┌──────────────────────────┐        ┌──────────────────────────────┐
│  kf8bss/groupsio-digest   │        │  kf8bss/groupsio-digest-site  │
│  (this repo)              │        │  (output only)                │
│                           │        │                                │
│  groupsio_digest_public.py│  push  │  index.html                   │
│  .github/workflows/       │───────▶│  digest_*.html (archive,      │
│    digest.yml (schedule)  │        │    last 5 kept)                │
└──────────────────────────┘        │  digest_*.txt                  │
                                      └───────────────┬────────────────┘
                                                       │ Git-connected
                                                       ▼
                                            Cloudflare Worker
                                            (static assets)
                                                       │
                                                       ▼
                                     grpdigest.kf8bss-radio.com
                                     (behind Cloudflare Access —
                                      "Only Me" policy)
```

**Every day at ~7:00 AM Eastern**, GitHub Actions:
1. Checks out this repo
2. Runs `groupsio_digest_public.py`, pulling the API key and group list from GitHub Secrets (not from any file)
3. Pushes the generated `index.html` (plus a dated archive copy) to `groupsio-digest-site`
4. That push triggers Cloudflare to redeploy automatically
5. The updated report is live at `grpdigest.kf8bss-radio.com` within a minute or two

You can also trigger a run manually anytime — see [Run it on demand](#run-it-on-demand) below.

---

## Repos and services involved

| What | Where | Purpose |
|---|---|---|
| Script + workflow | `kf8bss/groupsio-digest` (this repo) | The actual code and the schedule that runs it |
| Generated site | `kf8bss/groupsio-digest-site` | Just the output files; Cloudflare watches this repo directly |
| Secrets | `groupsio-digest` → Settings → Secrets and variables → Actions | `GROUPSIO_API_KEY`, `GROUPSIO_GROUPS_JSON`, `SITE_REPO_TOKEN` |
| Hosting | Cloudflare Workers & Pages, project name `groupsio-digest` | Serves the static files from `groupsio-digest-site` |
| Access control | Cloudflare Zero Trust → Access controls → Applications | Self-hosted app on `grpdigest.kf8bss-radio.com`, "Only Me" policy |
| Groups.io API key | [groups.io/settings/apikeys](https://groups.io/settings/apikeys) | Authenticates the script to fetch group activity |

---

## Local / manual use (laptop)

Local runs still work exactly as before, independent of the scheduled CI runs.

1. Clone the repo (or `cd` into your existing local clone).
2. If you don't already have one, copy `config.example.py` to `config.py` and fill in your real API key and `GROUPS` list. `config.py` is gitignored — it will never be committed, and CI does not use it.
3. Run:
   ```
   python groupsio_digest_public.py
   ```
   This opens the report in your browser and leaves the console window open, same as always.

`config.py` and the GitHub Secrets are two independent, parallel sources of the same information — local runs use the file, CI runs use the secrets. **Keeping a group list change in sync between them is a manual step** — see below.

---

## Maintenance procedures

### Add or remove a Groups.io group

Two places need to be updated — the local file (for your own manual runs) and the GitHub Secret (for the scheduled CI runs). They don't sync automatically.

1. **Update `config.py` locally** — add/remove/edit an entry in the `GROUPS` list, following the existing format:
   ```python
   {"name": "Display Name", "group": "slug", "domain": "groups.io"}
   ```
   Add `"restricted": True` if the group owner has disabled API access, or `"members_only": True` if the archive is closed to non-members. See the comments in `config.example.py` for subgroup slug formatting (`parent+subgroup`).

2. **Regenerate the `GROUPSIO_GROUPS_JSON` secret** — this needs to be your full `GROUPS` list converted to a single-line JSON string with lowercase `true`/`false` (not Python's `True`/`False`). Don't hand-edit this — a python one-liner does it safely:
   ```
   python -c "import json; from config import GROUPS; print(json.dumps(GROUPS))"
   ```
   Run that from your local repo folder (with `config.py` already updated per step 1), copy the single line of output.

3. Go to `groupsio-digest` → **Settings → Secrets and variables → Actions**, click **`GROUPSIO_GROUPS_JSON`** → **Update**, paste the new value, save.

4. Test it with a manual run (see [Run it on demand](#run-it-on-demand)) before waiting for the next scheduled run.

### Rotate the Groups.io API key

Do this any time the key may have been exposed, or on your own schedule as a precaution.

1. Log into [groups.io/settings/apikeys](https://groups.io/settings/apikeys), delete the old key, create a new one, copy it immediately (it's only shown once).
2. Update `config.py` locally with the new key.
3. Go to `groupsio-digest` → **Settings → Secrets and variables → Actions** → **`GROUPSIO_API_KEY`** → **Update**, paste the new key, save.
4. Confirm with a manual run.

**If a key is ever accidentally committed to either repo** (even briefly, even if later removed), treat it as compromised immediately — revoke and reissue at groups.io regardless of whether you've cleaned up the git history, since a public repo's history can be read even after a file is deleted from the current version.

### Rotate `SITE_REPO_TOKEN`

This is a GitHub fine-grained personal access token, scoped only to `groupsio-digest-site` with Contents: Read and write. It has an expiration date set when created — GitHub will warn you by email as it approaches.

1. GitHub → your profile → **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
2. Generate a new token, same scope as before: repository access limited to `groupsio-digest-site` only, Contents permission set to Read and write, nothing else.
3. Copy the new token value.
4. Go to `groupsio-digest` → **Settings → Secrets and variables → Actions** → **`SITE_REPO_TOKEN`** → **Update**, paste it, save.
5. You can delete the old token from GitHub's token list once the new one is confirmed working.

### Change the run schedule

Edit the `cron` line in `.github/workflows/digest.yml`:
```yaml
on:
  schedule:
    - cron: "0 11 * * *"   # UTC time
```
GitHub Actions cron always runs in **UTC**, not local time, and does not auto-adjust for Daylight Saving. `0 11 * * *` is roughly 7:00 AM Eastern during EDT and 6:00 AM during EST — if you want a fixed local time year-round, you'll need to update the cron value twice a year, or accept the hour drift.

After editing, commit and push. No secret changes needed for a schedule change.

### Change how many backup versions are kept

Currently set to keep the 5 most recent dated `digest_*.html` / `digest_*.txt` files in `groupsio-digest-site`, deleting older ones automatically on every run. To change the count, edit both lines in the "Prune old dated backups" step of `digest.yml`:
```yaml
ls -1 digest_*.html 2>/dev/null | sort | head -n -5 | xargs -r rm -f
ls -1 digest_*.txt  2>/dev/null | sort | head -n -5 | xargs -r rm -f
```
Change both `-5` values to the new number you want kept. Commit and push.

### Sync this fork with upstream (EtherHamRadio)

The upstream project occasionally ships fixes or new features (e.g. the `members_only` handling). To pull those in:

```
git fetch upstream
git log --oneline HEAD..upstream/main    # preview what's coming in
git merge upstream/main
```

If upstream has touched the configuration block at the top of `groupsio_digest_public.py` (the section right after the imports), you'll likely get a merge conflict there, since this fork replaced that block with the `config.py`/environment-variable loading logic. Resolve it by keeping this fork's version of that block (the `try/except` import logic) and discarding upstream's hardcoded example values — everything else upstream changed should merge cleanly. Push once resolved.

If `upstream` isn't already set up as a remote in a given local clone:
```
git remote add upstream https://github.com/EtherHamRadio/groupsio-digest.git
```

### Run it on demand

No need to wait for the 7 AM schedule to test a change:

1. Go to `groupsio-digest` → **Actions** tab
2. Click **"Run Groups.io Digest"** in the left sidebar
3. Click **Run workflow** → confirm
4. Watch the run's log; it should complete in under a minute
5. Check `grpdigest.kf8bss-radio.com` afterward (allow a minute or two for Cloudflare to redeploy and the edge cache to catch up — a hard refresh, Ctrl+Shift+R, clears up most "it still shows the old version" confusion)

---

## Troubleshooting

**Workflow fails with `ERROR: config.py not found`**
The env-var config path didn't trigger — almost always means `GROUPSIO_API_KEY` or `GROUPSIO_GROUPS_JSON` is missing or empty in the repo's Actions secrets. Check both exist under **Settings → Secrets and variables → Actions**.

**Workflow fails with `EOFError: EOF when reading a line`**
Something in the script hit an `input()` prompt that isn't guarded by the `if not os.environ.get("CI")` check. This shouldn't happen with the current version, but if a future merge from upstream reintroduces an unguarded prompt, this is the symptom to look for.

**Cloudflare build fails with `Could not detect a directory containing static files`**
`wrangler.jsonc` is missing or malformed in `groupsio-digest-site`. It must exist at the repo root with an `assets.directory` field pointing at `./`.

**Site shows old content right after a successful workflow run**
Almost always just propagation delay — wait a minute or two and hard-refresh. If it's still stale after several minutes, check the Deployments tab on the Cloudflare Worker to confirm a new deployment actually triggered from the latest commit.

**A Groups.io group shows "access restricted by group owner"**
Expected behavior for groups where the owner has disabled API access — not a bug, and there's nothing to fix on this end. This is what `"restricted": True` is for.

---

## Security notes

- `config.py` is gitignored and must never be committed. If it ever shows up in `git status` as staged or committed, stop and fix that before pushing.
- All three GitHub Secrets (`GROUPSIO_API_KEY`, `GROUPSIO_GROUPS_JSON`, `SITE_REPO_TOKEN`) are only ever entered through GitHub's Secrets UI, never written into any file in either repo.
- `SITE_REPO_TOKEN` is scoped as narrowly as GitHub allows — one repo, Contents read/write only — so that if it ever leaked, the blast radius is limited to the output repo, not this one or anything else in the account.
- The live report is behind Cloudflare Access, not public — if you ever want to share a single day's report with someone else, don't disable Access; instead consider a separate mechanism (e.g. manually forwarding the `.txt` file) rather than opening the site itself.

---

## Original upstream documentation

The sections below are preserved from the upstream project for reference — group entry format, subgroup slug conventions, and the underlying report structure — and remain accurate for this fork.

### Adding and removing groups (format reference)

Each `GROUPS` entry is a dictionary:
```python
{"name": "Display Name", "group": "slug", "domain": "groups.io"}
```
- **name** — how it appears in the report
- **group** — the slug from the group's URL
- **domain** — usually `groups.io`; use the subdomain for groups with custom domains

Subgroups use the `parentname+subgroupslug` format, e.g.:
```python
{"name": "ARDC: 44Net", "group": "ardc+44net", "domain": "groups.io"},
```

Groups with API access disabled by the owner: add `"restricted": True`.
Groups with a closed (members-only) archive: add `"members_only": True` — the script still counts messages but omits topic titles/links for these.

### Report format

**HTML report** — sorted by total message count, most active groups first, clickable thread links.
**Text report** — same content, plain text, useful for forwarding.
**Limitations** — the Groups.io API returns up to 100 topics per group per request; the report shows up to 10 topics per group.
