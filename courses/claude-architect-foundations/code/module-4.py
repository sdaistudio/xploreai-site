# Claude Certified Architect – Foundations: study course — Module 4: Prompt Engineering & Structured Output
# https://xploreai.co.in/courses/claude-architect-foundations/module-4/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 4.1 — Explicit criteria
# ============================================================================

FINDINGS = {  # category: (posted, dismissed by developers as wrong)
    "security":        (48, 3),
    "bug":             (160, 22),
    "comment-accuracy": (35, 6),
    "performance":     (120, 71),
    "style":           (310, 236),
}
total_posted = sum(p for p, _ in FINDINGS.values())
total_wrong = sum(d for _, d in FINDINGS.values())
print(f"overall: {total_wrong / total_posted:.0%} of all findings dismissed\n")
keep = {}
for cat, (posted, wrong) in sorted(FINDINGS.items(), key=lambda kv: kv[1][1] / kv[1][0]):
    fp_rate = wrong / posted
    action = "keep" if fp_rate <= 0.25 else "DISABLE while criteria are rewritten"
    if action == "keep": keep[cat] = (posted, wrong)
    print(f"{cat:<17} false-positive rate {fp_rate:>4.0%}  → {action}")
kp = sum(p for p, _ in keep.values()); kw = sum(w for _, w in keep.values())
print(f"\nafter disabling: {kw / kp:.0%} of findings dismissed ({kp} posted instead of {total_posted})")

# ============================================================================
# Session 4.2 — Few-shot examples
# ============================================================================

REQUIRED_FORMAT = {"location", "issue", "severity", "fix"}
EXAMPLES = [
    {"ambiguity": "empty-sequence sum", "finding": None, "reasoning": "sum([]) is 0, the correct total; not a bug"},
    {"ambiguity": "SQL via f-string", "finding": {"location": "db.py:12", "issue": "SQL injection", "severity": "HIGH", "fix": "parameterise"},
     "reasoning": "user input reaches the query string; parameters exist in this codebase"},
    {"ambiguity": "SQL via f-string", "finding": {"location": "db.py:40", "issue": "SQL injection", "severity": "HIGH", "fix": "parameterise"},
     "reasoning": None},
    {"ambiguity": "TODO comment", "finding": {"location": "api.py:7", "issue": "TODO left"}, "reasoning": "style only"},
]
seen = set()
for i, ex in enumerate(EXAMPLES, 1):
    problems = []
    if not ex["reasoning"]: problems.append("no reasoning: teaches the answer, not the judgement")
    if ex["finding"] and not REQUIRED_FORMAT <= set(ex["finding"]): problems.append(f"missing format fields {sorted(REQUIRED_FORMAT - set(ex['finding']))}")
    if ex["ambiguity"] in seen: problems.append("duplicates an ambiguity already covered")
    seen.add(ex["ambiguity"])
    print(f"example {i} ({ex['ambiguity']}): {'; '.join(problems) or 'ok'}")
print(f"\n{len(seen)} distinct ambiguities in {len(EXAMPLES)} examples (target: 2–4 targeted, each different)")

# ============================================================================
# Session 4.3 — Structured output with tool use
# ============================================================================

# extract_invoice = {
#     "name": "extract_invoice",
#     "description": "Record the fields of one supplier invoice.",
#     "input_schema": {
#         "type": "object",
#         "properties": {
#             "invoice_number": {"type": "string"},
#             "invoice_date":   {"type": ["string", "null"], "description": "ISO date; null if not stated"},
#             "po_number":      {"type": ["string", "null"], "description": "Purchase order; null if absent"},
#             "category":       {"type": "string", "enum": ["goods", "services", "freight", "other", "unclear"]},
#             "category_detail": {"type": ["string", "null"], "description": "Required when category is 'other'"},
#             "line_items":     {"type": "array", "items": {"type": "object", "properties": {"amount": {"type": "number"}}}},
#             "stated_total":   {"type": "number"},
#         },
#         "required": ["invoice_number", "category", "line_items", "stated_total"],
#     },
# }
# response = client.messages.create(model="claude-sonnet-5-5", max_tokens=2048, tools=[extract_invoice],
#                                   messages=[{"role": "user", "content": [pdf_block, {"type": "text", "text": "Record this invoice with extract_invoice."}]}])
# data = next(b.input for b in response.content if b.type == "tool_use")

DOC = "Invoice INV-5521 from Kaveri Freight. Items: haulage ₹18,000; loading ₹2,500. Total ₹20,500."

def stand_in_extract(schema_required):
    out = {"invoice_number": "INV-5521", "category": "freight", "line_items": [18000, 2500], "stated_total": 20500}
    for f in ("invoice_date", "po_number"):
        out[f] = ("2026-10-01" if f == "invoice_date" else "PO-0001") if f in schema_required else None
    return out

def validate(record, required, enums=("goods", "services", "freight", "other", "unclear")):
    errs = [f"missing {f}" for f in required if record.get(f) is None]
    if record["category"] not in enums: errs.append("category not in enum")
    if record["category"] == "other" and not record.get("category_detail"): errs.append("'other' needs category_detail")
    return errs or ["schema-valid"]

for label, required in [("date and PO required", ["invoice_number", "invoice_date", "po_number"]),
                        ("date and PO nullable", ["invoice_number"])]:
    rec = stand_in_extract(required)
    invented = [f for f in ("invoice_date", "po_number") if rec[f] is not None and rec[f] not in DOC]
    print(f"{label:<22} {validate(rec, required)}  invented values: {invented or 'none'}")

# ============================================================================
# Session 4.4 — Validation, retry and feedback
# ============================================================================

import re

def check(rec):
    errs = []
    if rec.get("invoice_date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rec["invoice_date"]):
        errs.append(f"invoice_date {rec['invoice_date']!r} is not ISO YYYY-MM-DD")
    calc = sum(rec["line_items"])
    if calc != rec["stated_total"] and not rec.get("conflict_detected"):
        errs.append(f"line items sum to {calc} but stated_total is {rec['stated_total']}; set conflict_detected if the document itself disagrees")
    if rec.get("gst_number") is None and rec.get("_gst_only_in_attachment"):
        errs.append("gst_number missing")
    return errs

ATTEMPTS = [  # what a stand-in model returns on each try
    {"invoice_date": "14/10/26", "line_items": [18000, 2500], "stated_total": 21500, "gst_number": None, "_gst_only_in_attachment": True},
    {"invoice_date": "2026-10-14", "line_items": [18000, 2500], "stated_total": 21500, "conflict_detected": True, "gst_number": None, "_gst_only_in_attachment": True},
]
for i, rec in enumerate(ATTEMPTS, 1):
    errs = check(rec)
    print(f"attempt {i}: {errs or 'valid'}")
    fixable = [e for e in errs if "gst_number" not in e]
    if errs and not fixable:
        print("   remaining error is about information that isn't in this document → stop retrying; leave gst_number null and flag for review")
        break

# ============================================================================
# Session 4.5 — Batch processing
# ============================================================================

def worst_case_hours(submit_every, batch_max=24):
    return submit_every + batch_max            # a document arriving just after a submission waits a full interval

SLA = 30
for every in (2, 4, 6, 8, 12):
    w = worst_case_hours(every)
    print(f"submit every {every:>2} h → worst case {w} h  {'meets' if w <= SLA else 'BREAKS'} the {SLA} h SLA" + ("  (margin for one resubmission cycle)" if SLA - w >= 2 else ""))

results = {"doc-001": "succeeded", "doc-002": "errored: prompt too long", "doc-003": "succeeded", "doc-004": "expired"}
resubmit = {cid: ("split into chunks" if "too long" in r else "resubmit unchanged") for cid, r in results.items() if r != "succeeded"}
print("\nresubmit only failures, by custom_id:", resubmit)

# ============================================================================
# Session 4.6 — Multi-instance and multi-pass review
# ============================================================================

LABELLED = [  # (reviewer's self-reported confidence, was it a real issue?)
    *[(0.9, True)] * 46, *[(0.9, False)] * 4,
    *[(0.7, True)] * 30, *[(0.7, False)] * 20,
    *[(0.5, True)] * 12, *[(0.5, False)] * 38,
]
for c in (0.9, 0.7, 0.5):
    bucket = [real for conf, real in LABELLED if conf == c]
    precision = sum(bucket) / len(bucket)
    route = "post to PR" if precision >= 0.85 else ("human triage" if precision >= 0.5 else "drop (log for pattern analysis)")
    print(f"confidence {c}: {len(bucket)} findings, {precision:.0%} real → {route}")
