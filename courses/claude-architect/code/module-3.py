# Claude Certified Architect – Professional: study course — Module 3: Integration
# https://xploreai.co.in/courses/claude-architect/module-3/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 3.1 — Capability bloat and tool scoping
# ============================================================================

ROLE = "Help support staff read tickets and draft replies."
REQUIRED_FOR_ROLE = {"read_ticket", "search_kb", "draft_reply", "get_customer"}
CONFIGURED = {   # tool: (risk, calls in the last 30 days)
    "read_ticket":     ("low", 18_420), "search_kb":   ("low", 9_310), "draft_reply":  ("low", 17_980),
    "get_customer":    ("low", 6_200),  "lookup_order": ("low", 4_870), "get_order":   ("low", 12),
    "issue_refund":    ("high", 3),     "delete_account": ("critical", 0), "run_sql":    ("critical", 1),
    "send_sms":        ("medium", 0),
}
SIMILAR = [("lookup_order", "get_order")]

print(f"role: {ROLE}\n{len(CONFIGURED)} tools configured, {len(REQUIRED_FOR_ROLE)} required\n")
for tool, (risk, calls) in sorted(CONFIGURED.items(), key=lambda kv: kv[1][1], reverse=True):
    reasons = []
    if tool not in REQUIRED_FOR_ROLE:
        reasons.append("not required by the role")
    if risk in ("high", "critical") and tool not in REQUIRED_FOR_ROLE:
        reasons.append(f"{risk}-risk capability")
    if calls == 0:
        reasons.append("never used")
    for a, b in SIMILAR:
        if tool == b: reasons.append(f"duplicates {a}")
    verdict = "REMOVE" if reasons and tool not in REQUIRED_FOR_ROLE and tool != "lookup_order" else "keep"
    print(f"{verdict:<7}{tool:<16}{risk:<9}{calls:>7,} calls  {'; '.join(reasons)}")

# ============================================================================
# Session 3.2 — Authentication and authorisation gaps
# ============================================================================

INTEGRATIONS = [
    {"name": "patient records tool", "auth": "service_account", "scope": "all_clinics", "checks_user_rights": False, "key_age_days": 30},
    {"name": "billing API",          "auth": "api_key",         "scope": "billing",     "checks_user_rights": True,  "key_age_days": 410, "shared_across_envs": True},
    {"name": "tickets MCP server",   "auth": "oauth_passthrough", "scope": "user_full", "checks_user_rights": True,  "key_age_days": 0},
    {"name": "scheduling service",   "auth": "none",            "scope": "internal",    "checks_user_rights": False, "key_age_days": 0},
    {"name": "knowledge base",       "auth": "oauth_scoped",    "scope": "kb.read",     "checks_user_rights": True,  "key_age_days": 1},
]

def review(i):
    gaps = []
    if i["auth"] == "none": gaps.append("unauthenticated endpoint")
    if i["auth"] == "service_account" and i["scope"] == "all_clinics" and not i["checks_user_rights"]:
        gaps.append("confused-deputy risk: broad service account, no per-user check")
    if i["auth"] == "oauth_passthrough": gaps.append("token pass-through: exchange for a narrow, audience-bound token")
    if i.get("shared_across_envs"): gaps.append("one key shared across environments")
    if i["key_age_days"] > 90: gaps.append(f"credential {i['key_age_days']} days old: rotate")
    return gaps

for i in INTEGRATIONS:
    gaps = review(i)
    print(f"{'GAP' if gaps else 'OK '} {i['name']:<22} {'; '.join(gaps)}")

# ============================================================================
# Session 3.3 — Accuracy versus latency
# ============================================================================

CONFIGS = [  # name, accuracy on eval, p95 seconds, $ per 1,000 requests (illustrative measurements)
    ("Haiku, k=5",                         0.86, 1.6,  1.1),
    ("Haiku, k=10 + rerank",               0.91, 2.2,  1.9),
    ("Sonnet, k=5",                        0.92, 3.1,  8.0),
    ("Sonnet, k=10 + rerank",              0.95, 3.8,  9.4),
    ("Sonnet, k=20 + rerank",              0.95, 4.9, 12.6),
    ("Opus, k=10 + rerank",                0.96, 6.4, 18.5),
    ("Sonnet, k=10 + rerank + verify",     0.97, 6.9, 15.2),
]
FLOOR, SLA = 0.94, 5.0

def dominated(c, others):
    return any(o[1] >= c[1] and o[2] <= c[2] and o[3] <= c[3] and o != c for o in others)

print(f"{'config':<34}{'acc':>5}{'p95':>6}{'$/1k':>7}  verdict")
for c in CONFIGS:
    if dominated(c, CONFIGS):            verdict = "dominated: another is as good or better on every axis"
    elif c[1] < FLOOR:                   verdict = "below accuracy floor"
    elif c[2] > SLA:                     verdict = "breaks the p95 SLA"
    else:                                verdict = "eligible"
    print(f"{c[0]:<34}{c[1]:>5.0%}{c[2]:>6.1f}{c[3]:>7.1f}  {verdict}")
best = min((c for c in CONFIGS if c[1] >= FLOOR and c[2] <= SLA), key=lambda c: c[3])
print(f"\nchoice: {best[0]}. Cheapest config meeting {FLOOR:.0%} accuracy within {SLA}s p95.")

# ============================================================================
# Session 3.4 — Observability at scale
# ============================================================================

import random

random.seed(7)
N = 1_000_000                                            # requests in a day
requests = [{"error": random.random() < 0.012, "high_risk": random.random() < 0.03,
             "flagged": random.random() < 0.004} for _ in range(N)]

def keep_payload(r, success_rate=0.02):
    return r["error"] or r["high_risk"] or r["flagged"] or random.random() < success_rate

kept = [r for r in requests if keep_payload(r)]
payload_kb = 24                                          # redacted prompt + output + trace, compressed
print(f"requests: {N:,}   payloads kept: {len(kept):,} ({len(kept) / N:.1%})")
print(f"  errors kept:      {sum(r['error'] for r in kept):,} of {sum(r['error'] for r in requests):,}")
print(f"  high-risk kept:   {sum(r['high_risk'] for r in kept):,} of {sum(r['high_risk'] for r in requests):,}")
print(f"storage per day: {len(kept) * payload_kb / 1e6:.1f} GB sampled vs {N * payload_kb / 1e6:.0f} GB keeping everything")

# ============================================================================
# Session 3.5 — Designing a RAG pipeline
# ============================================================================

POLICY = """## 4. Outpatient claims
4.1 Consultations are covered up to ₹1,500 per visit.
4.2 Diagnostics are covered up to ₹10,000 per policy year.
## 5. Exclusions
5.1 Cosmetic procedures are not covered.
5.2 Claims must be filed within 30 days of the visit; later claims are rejected unless the delay was caused by hospitalisation."""

def fixed_chunks(text, size=120, overlap=0):
    return [text[i:i + size] for i in range(0, len(text), size - overlap)]

def heading_chunks(text):
    chunks, current, heading = [], [], ""
    for line in text.splitlines():
        if line.startswith("## "):
            if current: chunks.append(heading + "\n" + "\n".join(current))
            heading, current = line, []
        else:
            current.append(line)
    chunks.append(heading + "\n" + "\n".join(current))
    return chunks

for name, chunks in [("fixed 120 chars", fixed_chunks(POLICY)), ("by heading", heading_chunks(POLICY))]:
    print(f"--- {name}: {len(chunks)} chunks")
    for c in chunks:
        if "30 days" in c or "hospitalisation" in c:
            print(repr(c))

# ============================================================================
# Session 3.6 — Retrieval strategies
# ============================================================================

import math, re
from collections import Counter

DOCS = {
    "d1": "Asthma J45.4: inhaled corticosteroids covered under OPD-GOLD.",
    "d2": "Night-time breathlessness should be assessed by a pulmonologist within 7 days.",
    "d3": "Claims for J45.9 require a spirometry report.",
    "d4": "Cosmetic dermatology is excluded.",
}
tok = lambda s: re.findall(r"[a-z0-9.]+", s.lower())

def bm25_scores(query, k1=1.5, b=0.75):
    docs = {d: tok(t) for d, t in DOCS.items()}
    avg = sum(len(t) for t in docs.values()) / len(docs)
    scores = {}
    for d, terms in docs.items():
        tf, s = Counter(terms), 0.0
        for q in tok(query):
            n = sum(q in t for t in docs.values())
            if n:
                idf = math.log(1 + (len(docs) - n + 0.5) / (n + 0.5))
                s += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(terms) / avg))
        scores[d] = round(s, 2)
    return scores

def bm25(query):
    s = bm25_scores(query); return sorted((d for d in s if s[d] > 0), key=s.get, reverse=True)   # matches only

CONCEPTS = {"breath": "breath", "breathing": "breath", "breathlessness": "breath", "breathless": "breath", "night": "night", "night-time": "night", "dark": "night",
            "nocturnal": "night", "asthma": "asthma", "wheezing": "asthma", "skin": "derm", "dermatology": "derm", "cosmetic": "derm"}
def concepts(s): return {CONCEPTS[w] for w in re.findall(r"[a-z-]+", s.lower()) if w in CONCEPTS}
def semantic(query):
    q = concepts(query)
    return sorted((d for d in DOCS if q & concepts(DOCS[d])), key=lambda d: len(q & concepts(DOCS[d])), reverse=True)

def rrf(*rankings, k=60):
    score = Counter()
    for r in rankings:
        for i, d in enumerate(r): score[d] += 1 / (k + i + 1)
    return [d for d, _ in score.most_common()]

for q in ["J45.4", "short of breath after dark"]:
    kw = bm25_scores(q)
    sem = {d: len(concepts(q) & concepts(DOCS[d])) for d in DOCS}
    print(f"query: {q!r}")
    print(f"  keyword scores  {kw}")
    print(f"  semantic scores {sem}")
    print(f"  hybrid ranking  {rrf(bm25(q), semantic(q))}")

# ============================================================================
# Session 3.7 — MCP, API/CLI or agent-to-agent
# ============================================================================

def choose_mechanism(n):
    if n["counterpart_is_agent"]:                       return "agent-to-agent (A2A)"
    if n["consumers"] > 1 or n["owned_by_other_team"]:  return "MCP server (wrapping the API/CLI)"
    if n["local_tool"]:                                 return "CLI (run as a subprocess)"
    return "direct API call in a custom tool"

needs = [("Inventory REST API used by 3 assistants, owned by ops", dict(counterpart_is_agent=False, consumers=3, owned_by_other_team=True, local_tool=False)),
         ("Run the team's lint and test CLIs during coding",       dict(counterpart_is_agent=False, consumers=1, owned_by_other_team=False, local_tool=True)),
         ("One app calls a payments API for refunds",              dict(counterpart_is_agent=False, consumers=1, owned_by_other_team=False, local_tool=False)),
         ("Delegate freight booking to a logistics partner's agent", dict(counterpart_is_agent=True, consumers=1, owned_by_other_team=True, local_tool=False))]
for name, n in needs:
    print(f"{choose_mechanism(n):<36} ← {name}")

def diagnose(s):
    if not s["declared"]:                 return "not declared in .mcp.json or user config (check the name and scope)"
    if s["transport"] != s["expected"]:   return f"wrong transport: configured {s['transport']}, server speaks {s['expected']}"
    if not s["reachable"]:                return "server not running / URL unreachable: check the process or endpoint, and its logs"
    if not s["approved"]:                 return "declared but not approved: project servers need approval (see /mcp)"
    if s["missing_env"]:                  return f"credential missing: {s['missing_env']} isn't set in the shell running Claude Code"
    if s["tool_disabled"]:                return "server connected, but the tool is denied or filtered by settings"
    return "connected"

cases = {
    "tickets":   dict(declared=True, transport="http", expected="http", reachable=True, approved=False, missing_env=None, tool_disabled=False),
    "inventory": dict(declared=True, transport="http", expected="http", reachable=True, approved=True, missing_env="INVENTORY_TOKEN", tool_disabled=False),
    "local-db":  dict(declared=True, transport="http", expected="stdio", reachable=True, approved=True, missing_env=None, tool_disabled=False),
    "wiki":      dict(declared=False, transport="", expected="http", reachable=True, approved=False, missing_env=None, tool_disabled=False),
}
for name, s in cases.items():
    print(f"{name:<10} → {diagnose(s)}")

# ============================================================================
# Session 3.8 — Progressive discovery vs monolithic context
# ============================================================================

# tools = [
#     {"type": "tool_search_tool_bm25_20251119", "name": "tool_search_tool_bm25"},
#     {"name": "get_customer", "description": "...", "input_schema": {...}},                 # always loaded
#     *[{**t, "defer_loading": True} for t in all_other_tools],                             # 140 tools, found on demand
# ]
# response = client.messages.create(model="claude-sonnet-5-5", max_tokens=4096, tools=tools, messages=messages)

n_tools, tokens_per_def, needed = 140, 350, 3
search_tool_tokens, always_loaded = 400, 2
monolithic = n_tools * tokens_per_def
progressive = search_tool_tokens + always_loaded * tokens_per_def + needed * tokens_per_def
print(f"monolithic:  {monolithic:>7,} tokens of tool definitions on every request; {n_tools} options to choose between")
print(f"progressive: {progressive:>7,} tokens (search tool + {always_loaded} core tools + {needed} found on demand); a short list at each step")
per_month = 2_000_000
saved = (monolithic - progressive) * per_month * 2.00 / 1e6
print(f"at {per_month:,} requests/month on Sonnet 5.5: ≈ ${saved:,.0f} less input before any caching")
