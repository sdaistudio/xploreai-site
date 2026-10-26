# Claude Certified Developer – Foundations: study course — Module 4: Eval, Testing, and Debugging
# https://xploreai.co.in/courses/claude-developer/module-4/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 4.1 — Error types and recovery
# ============================================================================

POLICY = [   # (test, category, strategy), checked in order
    (lambda e: e.get("status") in (429, 500, 529) or e.get("timeout"), "integration/infra (transient)", "retry with backoff, max 3"),
    (lambda e: e.get("status") in (400, 401, 403, 404),                 "integration (permanent)",       "fail fast, alert the team, show a friendly message"),
    (lambda e: e.get("stop_reason") == "refusal",                       "model output",                  "don't retry blindly: rephrase or escalate"),
    (lambda e: e.get("stop_reason") == "max_tokens",                    "model output (truncated)",      "raise max_tokens or split the task, then retry once"),
    (lambda e: e.get("parts_ok") is not None and e["parts_ok"] < e["parts"], "partial failure",          "graceful degradation: return what worked, flag the rest"),
    (lambda e: e.get("stakes") == "high" and e.get("confidence", 1) < 0.7, "low confidence, high stakes", "escalate to a person"),
]

def recover(event):
    for test, category, strategy in POLICY:
        if test(event):
            return category, strategy
    return "none", "proceed"

incidents = [
    ("Monday 9 am burst",                  {"status": 429}),
    ("Key rotated, old one still deployed", {"status": 401}),
    ("Network timeout to the API",          {"timeout": True}),
    ("Summary cut off mid-sentence",        {"stop_reason": "max_tokens"}),
    ("Weekly report: 1 of 4 sources down",  {"parts": 4, "parts_ok": 3}),
    ("Dosage question, model unsure",       {"stakes": "high", "confidence": 0.55}),
    ("Declined a routine billing question", {"stop_reason": "refusal"}),
]
for name, e in incidents:
    category, strategy = recover(e)
    print(f"{name:<37} {category:<30} → {strategy}")

def build_report(sources):
    sections, missing = [], []
    for name, fetch in sources:
        try:
            sections.append(f"## {name}\n{fetch()}")
        except Exception as e:
            missing.append(f"{name} ({type(e).__name__})")
    note = f"\n\n> Not included: {', '.join(missing)}. Retrying automatically in 15 minutes." if missing else ""
    return "\n\n".join(sections) + note, ("partial" if missing else "complete")

def down(): raise TimeoutError("billing service did not respond in 10s")

report, status = build_report([("Appointments", lambda: "412 booked, 31 no-shows"),
                               ("Billing", down),
                               ("Feedback", lambda: "4.6 / 5 from 88 reviews"),
                               ("Staffing", lambda: "2 open shifts on Saturday")])
print(f"status: {status}\n")
print(report)

# ============================================================================
# Session 4.2 — Traces, failure modes and isolating the layer
# ============================================================================

TRACE = [
    {"step": "input",  "ms": 0,    "data": {"user": "What's the refund status for order 4471?"}},
    {"step": "model",  "ms": 820,  "data": {"stop_reason": "tool_use", "tokens_out": 41}},
    {"step": "tool",   "ms": 1010, "data": {"name": "lookup_order", "input": {"order_id": "4471"},
                                            "result": {"error": "order not found"}, "is_error": True}},
    {"step": "model",  "ms": 1790, "data": {"stop_reason": "end_turn", "tokens_out": 36,
                                            "text": "I'm sorry, order 4471 doesn't exist in our system."}},
]
CUSTOMER_ORDERS = ["4417", "3902"]       # what the logged-in customer actually has

def analyse(trace):
    notes = []
    for i, s in enumerate(trace):
        d = s["data"]
        if s["step"] == "tool" and d.get("is_error"):
            notes.append(f"step {i}: {d['name']}({d['input']}) failed: {d['result']['error']}")
            near = [o for o in CUSTOMER_ORDERS if sorted(o) == sorted(d["input"]["order_id"])]
            if near:
                notes.append(f"         likely a typo: the customer owns {near[0]} (same digits, different order)")
        if s["step"] == "model" and d.get("text") and "doesn't exist" in d["text"]:
            notes.append(f"step {i}: model stated a conclusion instead of asking the customer to confirm the number")
    total = trace[-1]["ms"]
    notes.append(f"latency {total} ms: model {820 + (1790 - 1010)} ms, tool {1010 - 820} ms")
    return notes

for n in analyse(TRACE): print(n)

import re

SOURCE = "Revenue rose 12% to ₹4.1 crore. Two clinics opened in Pune. Staff turnover was 18%."

def detect(output):
    found = []
    if re.search(r"\b(can't|cannot|unable to) (help|assist|summari[sz]e)", output, re.I):
        return ["refusal / over-caution"]
    numbers = set(re.findall(r"\d+(?:\.\d+)?%?", output)) - set(re.findall(r"\d+(?:\.\d+)?%?", SOURCE)) - {"3"}
    if numbers:
        found.append(f"hallucination? numbers not in source: {sorted(numbers)}")
    bullets = [l for l in output.splitlines() if l.startswith("- ")]
    if len(bullets) != 3:
        found.append(f"format drift: {len(bullets)} bullets")
    if "Risks:" not in output:
        found.append("instruction breakdown: no 'Risks:' line")
    return found or ["ok"]

outputs = {
    "A": "- Revenue up 12% to ₹4.1 crore\n- Two clinics opened in Pune\n- Turnover 18%\nRisks: staff turnover",
    "B": "- Revenue up 15% to ₹4.1 crore\n- Two clinics opened in Pune\n- Turnover 18%\nRisks: staff turnover",
    "C": "Revenue rose 12% and two clinics opened in Pune, with turnover at 18%.\nRisks: turnover",
    "D": "- Revenue up 12%\n- Two clinics opened in Pune\n- Turnover 18%",
    "E": "I can't summarise documents that may contain financial advice.",
    "F": "- Revenue up 12%\n- Two Pune clinics\n- Turnover 18%, up from 11%\nRisks: hiring",
}
for k, out in outputs.items():
    print(k, "→", "; ".join(detect(out)))

TEMPLATE = "Summarise this report in 3 bullets.\n<report>\n{text}\n</report>"
TRUE_TEXT = {"q3_review.pdf": "Sales grew. Costs fell. Conclusion: expand to Nashik.",
             "audit_2026.pdf": "Audit found 3 billing errors. Conclusion: retrain front desk.",
             "pune_ops.pdf": "Wait times fell. Two nurses hired. Conclusion: extend hours."}

def parse_pdf(name):                       # our integration code: scanned PDFs come back empty
    return "" if name == "audit_2026.pdf" else TRUE_TEXT[name]

def stand_in_model(prompt):
    body = prompt.split("<report>\n")[1].split("\n</report>")[0]
    if not body.strip():
        return "- (no content provided)"
    first, second = body.split(". ")[:2]
    return f"- {first}\n- {second}\n- Overall positive"          # never mentions the conclusion

def show_in_app(reply, doc):               # our integration code: a display bug for one template
    return reply.splitlines()[0] if doc == "pune_ops.pdf" else reply

def isolation_test(doc, complaint, bug_present):
    rendered = TEMPLATE.format(text=parse_pdf(doc))
    input_ok = TRUE_TEXT[doc] in rendered
    replay = stand_in_model(rendered)                     # the exact request, sent directly
    reproduces = bug_present(replay)
    if not input_ok:
        verdict = "integration layer: the input was already wrong (fix the parser)"
    elif reproduces:
        verdict = "model output: correct input, still wrong (fix the prompt)"
    else:
        verdict = "integration layer: fine when replayed, broken in the app (fix code after the call)"
    print(f"{doc}: {complaint}\n   input complete: {input_ok}   reproduces on replay: {reproduces}\n   → {verdict}")

isolation_test("q3_review.pdf", "summary misses the conclusion", lambda out: "Nashik" not in out)
isolation_test("audit_2026.pdf", "summary is empty", lambda out: "no content" in out)
isolation_test("pune_ops.pdf", "summary has only one bullet", lambda out: len(out.splitlines()) < 3)
print("\nwhat the Pune user saw:", repr(show_in_app(stand_in_model(TEMPLATE.format(text=parse_pdf("pune_ops.pdf"))), "pune_ops.pdf")))

# ============================================================================
# Session 4.3 — Evals and monitoring
# ============================================================================

CASES = [  # (id, category, must_mention, reply_v1, reply_v2)
    (1, "refund",   "7 days",       "Refunds take 7 days.",                         "Your refund will arrive within 7 days."),
    (2, "refund",   "7 days",       "We will look into it.",                        "Refunds reach your account within 7 days."),
    (3, "booking",  "reschedule",   "You can reschedule online.",                   "You can reschedule online or by phone."),
    (4, "booking",  "reschedule",   "Please call us.",                              "To reschedule, use the link in your SMS."),
    (5, "angry",    "sorry",        "Calm down, it's being handled.",               "I'm sorry about the wait; it's being handled today."),
    (6, "angry",    "sorry",        "Sorry for the trouble.",                       "I'm sorry for the trouble."),
    (7, "clinical", "nurse",        "Take paracetamol and rest.",                   "A nurse will call you within the hour."),
    (8, "clinical", "nurse",        "A nurse will call you.",                       "A nurse will call you shortly."),
    (9, "billing",  "invoice",      "Your invoice is attached.",                    "Your invoice is attached."),
    (10, "billing", "invoice",      "Check your email.",                            "We've re-sent the invoice to your email."),
    (11, "refund",  "7 days",       "Refunds take 7 days.",                         "Refunds take about a week."),
    (12, "booking", "reschedule",   "You can reschedule online.",                   "You can reschedule online."),
]
BANNED = ["calm down", "paracetamol"]          # tone and safety rules

def grade(reply, must):
    if any(b in reply.lower() for b in BANNED): return False, "banned phrase"
    if must.lower() not in reply.lower():       return False, f"missing '{must}'"
    return True, ""

def run_eval(version):
    col = 3 if version == "v1" else 4
    results = [(c[0], c[1], *grade(c[col], c[2])) for c in CASES]
    return results

def wilson(passes, n, z=1.96):                 # 95% interval for a pass rate
    p = passes / n; d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d; half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return centre - half, centre + half

for v in ("v1", "v2"):
    res = run_eval(v)
    passes = sum(ok for _, _, ok, _ in res)
    lo, hi = wilson(passes, len(res))
    fails = {}
    for _, cat, ok, why in res:
        if not ok: fails.setdefault(cat, []).append(why)
    print(f"{v}: {passes}/{len(res)} pass ({passes / len(res):.0%}, 95% CI {lo:.0%}–{hi:.0%})  failures: {fails}")

human   = "PPFPPFFPPPFPPFPPPFPP"
judge_a = "PPFPPFFPPPFPPPPPPFPP"
judge_b = "PPPPPPPPPPPPPPPPPPPP"            # says "pass" to everything

def kappa(a, b):
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = a.count("P") / n, b.count("P") / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return observed, (observed - expected) / (1 - expected) if expected < 1 else 0.0

for name, j in [("judge A", judge_a), ("judge B", judge_b)]:
    agree, k = kappa(human, j)
    print(f"{name}: agrees on {agree:.0%} of cases, Cohen's kappa = {k:.2f}")

import math

def psi(expected, actual):
    total = 0
    for k in expected:
        e, a = max(expected[k], 1e-4), max(actual.get(k, 0), 1e-4)
        total += (a - e) * math.log(a / e)
    return total

eval_mix   = {"booking": 0.45, "billing": 0.20, "refund": 0.15, "clinical": 0.15, "teleconsult": 0.05}
week_mix   = {"booking": 0.42, "billing": 0.21, "refund": 0.16, "clinical": 0.15, "teleconsult": 0.06}
launch_mix = {"booking": 0.30, "billing": 0.15, "refund": 0.10, "clinical": 0.15, "teleconsult": 0.30}

for label, mix in [("an ordinary week", week_mix), ("week teleconsults launched", launch_mix)]:
    v = psi(eval_mix, mix)
    print(f"{label:<27} PSI = {v:.3f}  → {'DRIFT: refresh the eval set' if v > 0.2 else 'stable'}")
