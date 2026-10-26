# Claude Certified Developer – Foundations: study course — Module 3: Claude Code
# https://xploreai.co.in/courses/claude-developer/module-3/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 3.1 — Core components
# ============================================================================

skills = 25
description_tokens = 60          # name + one-line description, always loaded
body_tokens = 2_500              # the full SKILL.md, loaded when used
reference_tokens = 6_000         # optional extra files and scripts, read only if needed
used_per_session = 2

always_on = skills * description_tokens
if_everything_loaded = skills * (description_tokens + body_tokens + reference_tokens)
typical = always_on + used_per_session * body_tokens

print(f"descriptions only (start of every session): {always_on:>7,} tokens")
print(f"typical session using {used_per_session} skills:            {typical:>7,} tokens")
print(f"if all 25 skills were loaded in full:       {if_everything_loaded:>7,} tokens")

def where_does_it_go(need):
    n = need.lower()
    if any(w in n for w in ("must never", "always block", "every time without fail", "after every edit")):
        return "hook (or a permission rule)"
    if any(w in n for w in ("allow", "deny", "which model", "environment variable")):
        return "settings.json"
    if any(w in n for w in ("only in", "files under", "for the api folder")):
        return "path-scoped rule"
    if any(w in n for w in ("own context", "independently", "in parallel", "separate reviewer")):
        return "subagent"
    if any(w in n for w in ("step-by-step procedure", "checklist", "workflow with scripts")):
        return "skill"
    if any(w in n for w in ("i type", "shortcut", "on demand")):
        return "custom slash command (or a skill you invoke)"
    return "CLAUDE.md"

needs = [
    "Run the formatter after every edit",
    "The test command is `pytest -q` and the app uses FastAPI",
    "Only in files under app/api/: return errors as RFC 7807 problem JSON",
    "A 9-step release checklist with a changelog script",
    "Review each PR with a separate reviewer that doesn't see the author's reasoning",
    "Must never read .env files",
    "A shortcut I type to summarise today's changes for stand-up",
    "Deny `git push --force` and allow `pytest`",
]
for need in needs:
    print(f"{where_does_it_go(need):<44} ← {need}")

# ============================================================================
# Session 3.2 — CLAUDE.md, settings and commands
# ============================================================================

import posixpath as pp

FILES = {   # every CLAUDE.md-style file that exists on this machine
    "~/.claude/CLAUDE.md": "user: prefer British spelling; explain diffs briefly",
    "/work/CLAUDE.md": "work: all repos use pre-commit",
    "/work/clinic/CLAUDE.md": "project: FastAPI app; run `pytest -q`; dates as 30 Oct 2026",
    "/work/clinic/CLAUDE.local.md": "local (mine): my test DB is on port 5433",
    "/work/clinic/app/api/CLAUDE.md": "api: errors as RFC 7807 problem JSON",
    "/work/clinic/web/CLAUDE.md": "web: React + TypeScript, no default exports",
}

def ancestors(path):
    parts, out = path.strip("/").split("/"), []
    for i in range(len(parts) + 1):
        out.append("/" + "/".join(parts[:i]) if i else "/")
    return out

def loaded(start_dir, touched=()):
    order = ["~/.claude/CLAUDE.md"]
    for d in ancestors(start_dir):                              # root → start folder, at launch
        for name in ("CLAUDE.md", "CLAUDE.local.md"):
            p = pp.join(d, name)
            if p in FILES: order.append(p)
    for f in touched:                                           # subfolders, on demand
        d = pp.dirname(f)
        while d.startswith(start_dir) and d != start_dir:
            p = pp.join(d, "CLAUDE.md")
            if p in FILES and p not in order: order.append(p)
            d = pp.dirname(d)
    return order

print("Started in /work/clinic, nothing opened yet:")
for p in loaded("/work/clinic"): print("  ", FILES[p])
print("\n...then Claude edits app/api/bookings.py:")
for p in loaded("/work/clinic", ["/work/clinic/app/api/bookings.py"])[-1:]: print("  +", FILES[p])

import fnmatch

SETTINGS = {"allow": ["Bash(pytest *)", "Bash(npm run lint)", "Read(./src/**)"],
            "ask":   ["Bash(git push *)", "WebFetch"],
            "deny":  ["Read(.env)", "Bash(rm -rf *)", "Edit(./migrations/**)"]}

def matches(rule, tool, arg):
    name, _, spec = rule.partition("(")
    if name != tool: return False
    if not spec: return True                                   # bare tool name: every use
    spec = spec[:-1]
    if tool == "Bash":
        return arg == spec or (spec.endswith(" *") and arg.startswith(spec[:-1]))
    if "/" not in spec:                                        # bare file name: any depth
        return pp.basename(arg) == spec
    return fnmatch.fnmatch(arg, spec.replace("**", "*"))

def decide(tool, arg=""):
    for verdict in ("deny", "ask", "allow"):
        for rule in SETTINGS[verdict]:
            if matches(rule, tool, arg):
                return verdict, rule
    return "ask", "(no rule: default mode)"

calls = [("Bash", "pytest -q tests/"), ("Bash", "npm run lint"), ("Bash", "npm run deploy"),
         ("Bash", "git push origin main"), ("Bash", "rm -rf build"), ("Read", "./src/app/main.py"),
         ("Read", "./config/.env"), ("Edit", "./migrations/0042_add_index.py")]
for tool, arg in calls:
    verdict, rule = decide(tool, arg)
    print(f"{verdict.upper():<6} {tool}({arg})".ljust(48), "←", rule)

import re

SKILL = """Fix issue #$ARGUMENTS.

1. Read it with `gh issue view $ARGUMENTS`.
2. Write a failing test that reproduces it."""

def expand(body, typed):
    words = typed.split()
    body = body.replace("$ARGUMENTS", typed)
    return re.sub(r"\$(\d+)", lambda m: words[int(m.group(1))] if int(m.group(1)) < len(words) else "", body)

print(expand(SKILL, "214"))
print("\npositional form:", expand("Compare $0 with $1 and list breaking changes.", "v2.3 v3.0"))

# ============================================================================
# Session 3.3 — Headless mode and CI/CD
# ============================================================================

import json

raw = """{"type": "result", "subtype": "success", "is_error": false, "num_turns": 7,
  "session_id": "4f1c2a9e-example", "duration_ms": 48210, "total_cost_usd": 0.21,
  "result": "Found 3 unused functions.",
  "structured_output": {"findings": [
    {"file": "app/services/billing.py", "line": 88, "severity": "high",
     "message": "Refund amount not validated against the original charge"},
    {"file": "app/api/bookings.py", "line": 41, "severity": "medium",
     "message": "No 409 when the slot was taken between check and hold"},
    {"file": "app/utils/dates.py", "line": 12, "severity": "low",
     "message": "Unused helper `to_local_time`"}]}}"""

def ci_gate(raw, fail_on=("high",)):
    r = json.loads(raw)
    if r["is_error"] or r["subtype"] != "success":
        print(f"Claude run failed ({r['subtype']}): treat as a pipeline error, not a pass")
        return 2
    findings = r["structured_output"]["findings"]
    for f in findings:                    # each becomes an inline PR comment
        print(f"comment → {f['file']}:{f['line']}  [{f['severity']}] {f['message']}")
    blocking = [f for f in findings if f["severity"] in fail_on]
    print(f"\n{len(findings)} findings, {len(blocking)} blocking · {r['num_turns']} turns · "
          f"~${r['total_cost_usd']:.2f} (client-side estimate) · session {r['session_id']}")
    return 1 if blocking else 0

print("exit code:", ci_gate(raw))
print("exit code:", ci_gate('{"type": "result", "subtype": "error_max_turns", "is_error": true, "num_turns": 15}'))
