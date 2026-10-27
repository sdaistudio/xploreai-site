# Claude Certified Architect – Foundations: study course — Module 5: Context Management & Reliability
# https://xploreai.co.in/courses/claude-architect-foundations/module-5/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 5.1 — Preserving critical information
# ============================================================================

import json

order_lookup = {   # what the orders API returns (abridged here: imagine 40+ fields)
    "order_id": "ORD-1182", "status": "delivered", "delivered_at": "2026-10-09", "total": 42.00, "currency": "USD",
    "items": [{"sku": "BLD-200", "name": "Blender", "qty": 1, "price": 42.00, "returnable": True}],
    "warehouse": "PNQ-3", "carrier": "BlueDart", "carrier_events": [{"t": i, "e": "scan"} for i in range(14)],
    "billing_address": "...", "shipping_address": "...", "gift_wrap": False, "loyalty_points": 84,
    "fraud_score": 0.02, "marketing_opt_in": True, "audit": {"created_by": "web", "version": 7},
}
RETURN_FIELDS = ["order_id", "status", "delivered_at", "total", "items"]
trimmed = {k: order_lookup[k] for k in RETURN_FIELDS}
trimmed["items"] = [{k: i[k] for k in ("name", "price", "returnable")} for i in trimmed["items"]]

case_facts = {"issues": [
    {"id": 1, "order": "ORD-1182", "problem": "blender arrived broken", "amount": 42.00, "status": "refund issued"},
    {"id": 2, "order": "ORD-1190", "problem": "charged twice", "amount": 129.00, "status": "awaiting billing review"},
], "promised": "update on issue 2 by email before 17:00 IST, 28 Oct"}

print(f"raw lookup ≈ {len(json.dumps(order_lookup)) // 4} tokens; trimmed ≈ {len(json.dumps(trimmed)) // 4} tokens")
print("trimmed:", trimmed)
print("\n<case_facts>" + json.dumps(case_facts) + "</case_facts>   ← carried verbatim every turn")

# ============================================================================
# Session 5.2 — Escalation and ambiguity
# ============================================================================

def handle(turn):
    if turn.get("asks_for_human"):
        return "ESCALATE now with a structured summary (don't investigate first)"
    if turn.get("policy") == "silent":
        return "ESCALATE: policy gap — a person must decide"
    matches = turn.get("customer_matches", 1)
    if matches > 1:
        return f"ASK for another identifier ({matches} customers match); never guess"
    if turn.get("frustrated") and turn.get("straightforward"):
        if turn.get("reiterated_human"):
            return "ESCALATE: they asked again for a person"
        return "acknowledge frustration, offer the fix, mention a person is available"
    return "resolve"

turns = [
    ("'Just get me a human.'",                                        dict(asks_for_human=True)),
    ("'Match AnyMart's price, it's ₹400 cheaper.'",                   dict(policy="silent")),
    ("'I'm Rahul Shah, refund my order.' (3 Rahul Shahs found)",      dict(customer_matches=3)),
    ("'THIRD TIME asking! Replace my damaged kettle!' (photo attached)", dict(frustrated=True, straightforward=True)),
    ("Same customer: 'No, I want a person.'",                         dict(frustrated=True, straightforward=True, reiterated_human=True)),
    ("Standard damage replacement with photo evidence",               dict(straightforward=True)),
]
for text, t in turns:
    print(f"{handle(t):<74} ← {text}")

# ============================================================================
# Session 5.3 — Error propagation across agents
# ============================================================================

OUTCOMES = {
    "regulation":  {"ok": True,  "findings": 6},
    "case law":    {"ok": False, "failure": "timeout", "attempted": "2 queries", "partial": 2, "alternatives": ["legal DB via analysis agent"]},
    "vendor tools": {"ok": True,  "findings": 0},                               # searched; genuinely nothing
    "worker views": {"ok": False, "failure": "permission", "attempted": "survey archive", "partial": 0, "alternatives": []},
}
def coordinate(outcomes):
    report = []
    for topic, o in outcomes.items():
        if o["ok"] and o["findings"]:   report.append((topic, f"well supported ({o['findings']} sources)"))
        elif o["ok"]:                   report.append((topic, "searched: no relevant sources exist"))
        elif o["alternatives"]:         report.append((topic, f"PARTIAL: {o['partial']} sources; retrying via {o['alternatives'][0]}"))
        else:                           report.append((topic, f"GAP: {o['failure']} on {o['attempted']}; not covered"))
    return report

for topic, note in coordinate(OUTCOMES):
    print(f"{topic:<13} {note}")

# ============================================================================
# Session 5.4 — Exploring large codebases
# ============================================================================

import json, os, tempfile

work = tempfile.mkdtemp()
scratch, manifest = os.path.join(work, "scratchpad.md"), os.path.join(work, "manifest.json")

def note(line):
    with open(scratch, "a") as f: f.write(f"- {line}\n")

def save_state(agent, state):
    m = json.load(open(manifest)) if os.path.exists(manifest) else {}
    m[agent] = state
    json.dump(m, open(manifest, "w"), indent=1)

# Phase 1: exploration (findings persisted as we go)
note("Refund entry point: api/refunds.py:post_refund → services/refunds.py:issue_refund")
note("Money stored as integer paise in models/payment.py (Payment.amount_paise)")
save_state("explorer", {"phase": "trace-refund-flow", "done": ["api", "services"], "next": ["gateway client", "webhooks"]})
save_state("test-mapper", {"phase": "find-tests", "done": ["tests/api"], "next": ["tests/services"]})
# ... process crashes here ...

# Resume: coordinator loads the manifest and scratchpad and injects them
state = json.load(open(manifest))
resume_prompt = "Resuming. Key findings so far:\n" + open(scratch).read() + "\nAgent state:\n" + "\n".join(f"  {a}: {json.dumps(s)}" for a, s in state.items())
print(resume_prompt)

# ============================================================================
# Session 5.5 — Human review and confidence
# ============================================================================

import random
random.seed(9)

RESULTS = {  # (document type, field): (checked, correct)
    ("typed invoice", "total"):    (4_000, 3_964), ("typed invoice", "date"): (4_000, 3_952),
    ("scanned receipt", "total"):  (1_500, 1_455), ("scanned receipt", "date"): (1_500, 1_440),
    ("handwritten note", "total"): (300, 231),     ("handwritten note", "date"): (300, 249),
}
checked = sum(c for c, _ in RESULTS.values()); correct = sum(k for _, k in RESULTS.values())
print(f"overall accuracy: {correct / checked:.1%}\n")
for (doc, field), (c, k) in RESULTS.items():
    acc = k / c
    print(f"{doc:<17}{field:<6} {acc:6.1%}{'  ← below 95%: keep full human review' if acc < 0.95 else ''}")

high_conf = [("typed invoice", i) for i in range(3_000)] + [("scanned receipt", i) for i in range(900)] + [("handwritten note", i) for i in range(40)]
per_stratum = 25
sample = {d: random.sample([x for x in high_conf if x[0] == d], per_stratum) for d in ("typed invoice", "scanned receipt", "handwritten note")}
print("\nweekly audit of high-confidence extractions:", {d: len(s) for d, s in sample.items()}, "(equal per type, not proportional)")

# ============================================================================
# Session 5.6 — Provenance and uncertainty
# ============================================================================

CLAIMS = [
    {"metric": "AI use in hiring (share of firms)", "value": "38%", "source": "EU Labour Survey", "date": "2025-11"},
    {"metric": "AI use in hiring (share of firms)", "value": "41%", "source": "Recruiters Assoc. report", "date": "2025-12"},
    {"metric": "AI use in hiring (share of firms)", "value": "23%", "source": "EU Labour Survey", "date": "2023-06"},
    {"metric": "Candidates told about AI screening", "value": "12%", "source": "Consumer Watch", "date": "2026-02"},
    {"metric": "Candidates told about AI screening", "value": "31%", "source": "HR Tech Index", "date": "2026-03"},
]
from collections import defaultdict
by_metric = defaultdict(list)
for c in CLAIMS: by_metric[c["metric"]].append(c)

for metric, cs in by_metric.items():
    print(f"\n{metric}")
    years = {c["date"][:4] for c in cs}
    recent = [c for c in cs if c["date"][:4] == max(years)] if len(years) > 1 else cs
    older = [c for c in cs if c not in recent]
    for c in older:
        print(f"   trend context: {c['value']} ({c['source']}, {c['date']}) — earlier year, not a contradiction")
    vals = {c["value"] for c in recent}
    spread = max(float(v[:-1]) for v in vals) - min(float(v[:-1]) for v in vals)
    label = "WELL-ESTABLISHED (sources agree within 5 points)" if spread <= 5 else "CONTESTED: show both, with sources"
    print(f"   {label}")
    for c in recent:
        print(f"     {c['value']:<5} {c['source']} ({c['date']})")
