# xploreai.co.in — Website + AI Weekly Briefing

The XploreAI website, redesigned in the brand system (cream `#F5EFE4` / espresso `#4A4238` / rust `#E2571B`, Quicksand), with a weekly AI Briefing section published straight from this repo via GitHub Pages.

## Structure

```
index.html                  → homepage (all agency sections + latest-issue card)
assets/style.css            → shared brand stylesheet
assets/logo.svg             → wordmark
briefing/index.html         → briefing archive (renders issues.json)
briefing/issues.json        → ⭐ the ONE file that lists all issues
briefing/issue-01/index.html→ Issue #01 (10–17 Aug 2026)
favicon.ico / favicon-32.png / apple-touch-icon.png
CNAME                       → custom domain (xploreai.co.in)
```

The homepage "This Week in AI" card and the archive page both read `briefing/issues.json` — newest issue first. Add an entry there and the whole site updates.

## One-time setup (≈10 minutes)

1. Create a new GitHub repo (e.g. `xploreai-site`), then from this folder:
   ```bash
   git init
   git add .
   git commit -m "XploreAI site v2 — brand redesign + weekly briefing"
   git branch -M main
   git remote add origin https://github.com/<your-username>/xploreai-site.git
   git push -u origin main
   ```
2. On GitHub: **Settings → Pages → Source: Deploy from a branch → main / (root) → Save.**
3. Still in Pages settings, set **Custom domain: xploreai.co.in** (the CNAME file in this repo keeps it locked in).
4. At your domain registrar / current DNS, point the domain to GitHub Pages:
   - `A` records for `xploreai.co.in` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` record for `www` → `<your-username>.github.io`
5. Back in GitHub Pages settings, tick **Enforce HTTPS** once the certificate is issued (can take up to an hour after DNS changes).
6. If you have an existing `learn.html`, copy it into the repo root so `/learn.html` keeps working.

## Weekly publishing workflow (≈5 minutes)

Every Monday:

1. Copy last week's issue folder:
   ```bash
   cp -r briefing/issue-01 briefing/issue-02
   ```
2. Edit `briefing/issue-02/index.html` — replace the issue number, dates, stories, links.
3. Add the new issue to the **top** of `briefing/issues.json`:
   ```json
   {
     "issue": 2,
     "slug": "issue-02",
     "title": "…",
     "dates": "17–24 Aug 2026",
     "summary": "One-sentence summary for the homepage card.",
     "highlights": ["…", "…"]
   }
   ```
4. Commit and push:
   ```bash
   git add . && git commit -m "Briefing Issue #02" && git push
   ```

GitHub Pages redeploys automatically in ~1 minute. The homepage card, the archive, and the new issue page all go live together.

## Notes

- Paths are root-absolute (`/assets/…`, `/briefing/…`) — correct for the custom domain. If you ever preview at `username.github.io/xploreai-site/` *without* the custom domain, links will break; that's expected.
- Fonts load from Google Fonts (Quicksand, OFL-licensed).
- `.nojekyll` disables Jekyll processing so files serve as-is.
