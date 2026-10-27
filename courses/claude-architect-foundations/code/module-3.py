# Claude Certified Architect – Foundations: study course — Module 3: Claude Code Configuration & Workflows
# https://xploreai.co.in/courses/claude-architect-foundations/module-3/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 3.1 — The CLAUDE.md hierarchy
# ============================================================================

import re

FILES = {
    "~/.claude/CLAUDE.md": "- Prefer early returns.\n- Team rule: run `make lint` before committing.",
    "CLAUDE.md": "# Monorepo\n- Python 3.12, pytest.\n@docs/standards/testing.md",
    "docs/standards/testing.md": "- Tests use factories in tests/factories.\n@docs/standards/fixtures.md",
    "docs/standards/fixtures.md": "- Fixtures live in conftest.py at package level.",
    "packages/billing/CLAUDE.md": "@docs/standards/money-handling.md\n- Amounts in paise.",
    "docs/standards/money-handling.md": "- Use Decimal for display only; integers internally.\n@docs/standards/testing.md",
}

def expand(path, seen=None):
    seen = seen or set()
    if path in seen: return [f"(skipped repeat import of {path})"]
    seen.add(path)
    out = []
    for line in FILES[path].splitlines():
        m = re.match(r"@(\S+)", line)
        out += expand(m.group(1), seen) if m else [line]
    return out

for dev, has_user_file in [("Asha (wrote the team rule in her user file)", True), ("Ravi (new teammate)", False)]:
    sources = (["~/.claude/CLAUDE.md"] if has_user_file else []) + ["CLAUDE.md", "packages/billing/CLAUDE.md"]
    lines = [l for s in sources for l in expand(s) if l.startswith("-")]
    print(f"{dev}: {len(lines)} instructions; has 'make lint' rule: {any('make lint' in l for l in lines)}")

# ============================================================================
# Session 3.2 — Slash commands and skills
# ============================================================================

def invoke(skill, args, main_context_tokens):
    if skill["argument_hint"] and not args:
        return main_context_tokens, f"prompt user: {skill['argument_hint']}"
    exploration = 46_000                         # files read, searches run while mapping
    summary = 900                                # what the skill returns
    if skill["context"] == "fork":
        return main_context_tokens + summary, "ran in an isolated subagent"
    return main_context_tokens + exploration + summary, "ran inline"

def tool_allowed(skill, tool):
    return tool in skill["allowed_tools"]

forked = {"argument_hint": "<directory or module to map>", "context": "fork", "allowed_tools": {"Read", "Grep", "Glob"}}
inline = dict(forked, context=None)

for label, sk in [("context: fork", forked), ("inline", inline)]:
    tokens, how = invoke(sk, "src/payments", 12_000)
    print(f"{label:<14} main conversation after skill: {tokens:>6,} tokens ({how})")
print("no arguments:", invoke(forked, "", 12_000)[1])
print("skill tries Bash(rm -rf build):", "allowed" if tool_allowed(forked, "Bash") else "blocked by allowed-tools")

# ============================================================================
# Session 3.3 — Path-specific rules
# ============================================================================

import fnmatch

RULES = {
    "react.md":     (["src/components/**/*.tsx"], 900),
    "api.md":       (["src/api/**/*"], 1_200),
    "testing.md":   (["**/*.test.tsx", "**/*.test.ts"], 700),
    "terraform.md": (["terraform/**/*"], 1_600),
    "db.md":        (["src/db/**/*"], 800),
}
def matches(path, pattern):                       # fnmatch's * crosses '/', so '**/' just needs an optional prefix
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.replace("**/", ""))

for edited in [["src/components/Button.tsx", "src/components/Button.test.tsx"], ["src/api/refunds.ts", "src/api/refunds.test.ts"], ["terraform/prod/main.tf"]]:
    loaded = [r for r, (pats, _) in RULES.items() if any(matches(f, p) for f in edited for p in pats)]
    tokens = sum(RULES[r][1] for r in loaded)
    print(f"editing {edited}\n   loads {loaded} ({tokens:,} tokens of {sum(t for _, t in RULES.values()):,})")

# ============================================================================
# Session 3.4 — Plan mode or direct execution
# ============================================================================

def mode_for(task):
    signals = []
    if task["files"] > 10:            signals.append(f"{task['files']} files")
    if task["approaches"] > 1:        signals.append(f"{task['approaches']} valid approaches")
    if task["architectural"]:         signals.append("architectural decision")
    if signals:
        return "plan mode", signals
    return "direct execution", ["small, clear scope"]

tasks = [
    ("Split the monolith into services",                 dict(files=60, approaches=3, architectural=True)),
    ("Fix the KeyError in invoice.py (stack trace given)", dict(files=1, approaches=1, architectural=False)),
    ("Migrate from requests to httpx (45 files)",          dict(files=45, approaches=1, architectural=False)),
    ("Add a date-range check to create_booking()",         dict(files=1, approaches=1, architectural=False)),
    ("Webhooks or a queue for partner notifications?",     dict(files=6, approaches=2, architectural=True)),
]
for name, t in tasks:
    mode, why = mode_for(t)
    print(f"{mode:<17} {name:<50} ({', '.join(why)})")

# ============================================================================
# Session 3.5 — Iterative refinement
# ============================================================================

TESTS = [  # (input row, expected output) for normalising legacy phone numbers
    ({"phone": "98200 12345"},  "+919820012345"),
    ({"phone": "+91-98200-12345"}, "+919820012345"),
    ({"phone": None},           None),                 # edge case: missing value
    ({"phone": "022 2345 6789"}, "+912223456789"),     # landline with STD code
]

def v1(row):
    digits = "".join(c for c in row["phone"] if c.isdigit())
    return "+91" + digits[-10:]

def v2(row):
    if row["phone"] is None:
        return None
    digits = "".join(c for c in row["phone"] if c.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    return "+91" + digits

def run_tests(fn):
    failures = []
    for row, want in TESTS:
        try:
            got = fn(row)
        except Exception as e:
            got = f"{type(e).__name__}"
        if got != want: failures.append(f"input {row} → got {got!r}, expected {want!r}")
    return failures

for name, fn in [("v1", v1), ("v2", v2)]:
    f = run_tests(fn)
    print(f"{name}: {len(TESTS) - len(f)}/{len(TESTS)} pass")
    for line in f: print("   ", line)

# ============================================================================
# Session 3.6 — Claude Code in CI/CD
# ============================================================================

import hashlib, json

def fp(f): return hashlib.sha1(f"{f['file']}|{f['rule']}|{f['snippet'].strip()}".encode()).hexdigest()[:10]

prior = [
    {"file": "api/refunds.py", "line": 41, "rule": "missing-authz-check", "snippet": "def refund(req):"},
    {"file": "api/refunds.py", "line": 77, "rule": "float-money", "snippet": "total = price * 1.18"},
    {"file": "db/models.py",   "line": 12, "rule": "n-plus-one", "snippet": "for o in orders: o.items.all()"},
]
current = [   # after the developer's new commit: lines moved, one issue fixed, one new
    {"file": "api/refunds.py", "line": 45, "rule": "missing-authz-check", "snippet": "def refund(req):"},
    {"file": "db/models.py",   "line": 14, "rule": "n-plus-one", "snippet": "for o in orders: o.items.all()"},
    {"file": "api/refunds.py", "line": 90, "rule": "secret-in-log", "snippet": "log(f'card={card}')"},
]
prior_fps = {fp(f): f for f in prior}
for f in current:
    status = "still unaddressed (reply on the existing comment)" if fp(f) in prior_fps else "NEW: post a comment"
    print(f"{f['file']}:{f['line']:<4} {f['rule']:<20} {status}")
resolved = [f for k, f in prior_fps.items() if k not in {fp(c) for c in current}]
print("resolved since last review:", [f"{r['file']}:{r['line']} {r['rule']}" for r in resolved])
