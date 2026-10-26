# Claude Certified Architect – Professional: study course — Module 7: Developer Productivity & Operational Enablement
# https://xploreai.co.in/courses/claude-architect/module-7/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 7.1 — Configuring Claude Code for teams
# ============================================================================

import fnmatch

SECTIONS = {  # instruction set: (tokens, paths it applies to; None = everywhere)
    "core standards":        (900,   None),
    "API conventions":       (1_400, ["services/*/api/*.py"]),
    "test conventions":      (1_100, ["*.test.ts", "*.spec.ts"]),
    "Terraform checklist":   (2_600, ["infra/*.tf"]),
    "React components":      (1_800, ["web/src/components/*.tsx"]),
    "SQL migrations":        (1_200, ["db/migrations/*.sql"]),
}
touched = ["web/src/components/Button.tsx", "web/src/components/Button.test.ts", "web/src/styles.css"]

monolithic = sum(t for t, _ in SECTIONS.values())
scoped = 0
for name, (tokens, paths) in SECTIONS.items():
    if paths is None or any(fnmatch.fnmatch(f, p) or fnmatch.fnmatch(f.split("/")[-1], p) for f in touched for p in paths):
        scoped += tokens
        print(f"loaded   {name:<20} {tokens:>6,}")
    else:
        print(f"skipped  {name:<20} {tokens:>6,}")
print(f"\none big CLAUDE.md: {monolithic:,} tokens every session   path-scoped rules: {scoped:,} this session")

# ============================================================================
# Session 7.2 — AI-assisted developer workflows
# ============================================================================

BEFORE = {"PR cycle time (h, median)": 31.0, "review wait (h, median)": 14.0, "escaped defects / 100 PRs": 4.2, "PRs per dev-week": 3.1}
AFTER  = {"PR cycle time (h, median)": 22.5, "review wait (h, median)": 6.5,  "escaped defects / 100 PRs": 4.6, "PRs per dev-week": 3.6}
LOWER_IS_BETTER = {"PR cycle time (h, median)", "review wait (h, median)", "escaped defects / 100 PRs"}

for metric in BEFORE:
    b, a = BEFORE[metric], AFTER[metric]
    change = (a - b) / b
    better = (change < 0) == (metric in LOWER_IS_BETTER)
    print(f"{metric:<28} {b:>6} → {a:<6} {change:+.0%}  {'better' if better else 'WORSE'}")

findings = {"accepted by humans": 312, "dismissed as wrong": 141, "dismissed as noise/nit": 210}
total = sum(findings.values())
print(f"\nAI review findings: {findings['accepted by humans'] / total:.0%} accepted, "
      f"{findings['dismissed as wrong'] / total:.0%} wrong, {findings['dismissed as noise/nit'] / total:.0%} noise")

# ============================================================================
# Session 7.3 — Debugging and operations
# ============================================================================

import re
from collections import Counter, defaultdict

LOGS = [
    "14:01:12 INFO checkout ok order=88121 ms=412",
    "14:03:40 WARN payments slow ms=2210 order=88140",
    "14:05:03 DEPLOY checkout v2.31.0 (commit 7f3c2e1: 'switch tax service client to async')",
    *[f"14:{5 + i // 6:02d}:{10 + (i * 7) % 50:02d} ERROR checkout TaxClientTimeout after 3000ms order={88200 + i}" for i in range(42)],
    *[f"14:{6 + i // 3:02d}:{10 + (i * 11) % 50:02d} ERROR checkout NullPointer in CartTotal line 118 cart={5500 + i}" for i in range(9)],
    "14:09:44 WARN payments slow ms=2050 order=88310",
    "14:12:30 ERROR auth TokenExpired user=1201",
]

def secs(t): h, m, s = map(int, t.split(":")); return h * 3600 + m * 60 + s

def signature(line):
    msg = line.split(" ", 2)[2]
    return re.sub(r"\b\d+(ms)?\b", "<n>", re.sub(r"=\S+", "=<id>", msg))

deploys = [(l[:8], l[16:]) for l in LOGS if " DEPLOY " in l]
errors = sorted((l for l in LOGS if " ERROR " in l), key=lambda l: secs(l[:8]))
groups, first_seen = Counter(), {}
for l in errors:
    sig = signature(l)
    groups[sig] += 1
    first_seen.setdefault(sig, l[:8])

print("deploys:", deploys)
for sig, n in groups.most_common():
    near = [d for t, d in deploys if 0 <= secs(first_seen[sig]) - secs(t) <= 300]   # began within 5 min of a deploy
    print(f"{n:>3}×  first {first_seen[sig]}  {sig}")
    if near: print(f"       began within 5 min of deploy: {near[-1]}")
