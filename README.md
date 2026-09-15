# Ge Zhang Academic Hub — Auto-Sync v4

**Identity anchor:** ORCID `0000-0002-3116-3246`

## Automatic maintenance
A GitHub Action runs daily and queries Crossref with the exact ORCID filter. New DOI works are merged into the master publication database, then `publications.html`, `publications.json`, and `sitemap.xml` are rebuilt.

This avoids matching on the common author name **Ge Zhang**.

## ORCID reconciliation
ORCID itself is not polled on a schedule. After manually adding or editing ORCID works, run the GitHub Action **Reconcile with ORCID public works**.

Only works visible as **Everyone/Public** can be read from the public ORCID record.

## Key files
- `data/publications_master.json` — persistent master database
- `scripts/sync_crossref.py` — daily exact-ORCID DOI discovery
- `scripts/sync_orcid.py` — one-click ORCID reconciliation
- `scripts/build_publications.py` — rebuilds website publication outputs
- `.github/workflows/daily-publications.yml` — daily automation
- `.github/workflows/manual-orcid-reconcile.yml` — manual ORCID refresh
