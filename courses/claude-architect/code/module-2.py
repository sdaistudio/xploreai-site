# Claude Certified Architect – Professional: study course — Module 2: Claude Models, Prompting & Context Engineering
# https://xploreai.co.in/courses/claude-architect/module-2/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 2.1 — Model selection trade-offs
# ============================================================================

WEIGHTS = {"quality": 0.40, "latency": 0.25, "cost": 0.25, "platform fit": 0.10}
SCORES = {   # 1–5, from evals, load tests and procurement (illustrative)
    "Haiku 5.5":  {"quality": 3, "latency": 5, "cost": 5, "platform fit": 5},
    "Sonnet 5.5": {"quality": 4, "latency": 4, "cost": 4, "platform fit": 5},
    "Opus 5.5":   {"quality": 5, "latency": 3, "cost": 3, "platform fit": 5},
}
MIN_QUALITY = 4     # the eval floor this workload must clear

for model, s in SCORES.items():
    total = sum(WEIGHTS[k] * v for k, v in s.items())
    note = "" if s["quality"] >= MIN_QUALITY else "  ✗ below the quality floor: excluded whatever its score"
    print(f"{model:<11} weighted {total:.2f}{note}")

eligible = {m: sum(WEIGHTS[k] * v for k, v in s.items()) for m, s in SCORES.items() if s["quality"] >= MIN_QUALITY}
print("\nchoice:", max(eligible, key=eligible.get))

def timings(prompt_tokens, cached_tokens, output_tokens, prefill_per_1k=0.06, overhead=0.35, out_tps=70):
    """Illustrative latency model: prefill time grows with uncached prompt tokens."""
    ttft = overhead + (prompt_tokens - cached_tokens) / 1000 * prefill_per_1k
    return ttft, ttft + output_tokens / out_tps

cases = [("40K prompt, no cache, not streamed", 40_000, 0, 500, False),
         ("40K prompt, no cache, streamed",     40_000, 0, 500, True),
         ("40K prompt, 38K cached, streamed",   40_000, 38_000, 500, True)]
for label, p, c, o, streamed in cases:
    ttft, total = timings(p, c, o)
    seen = ttft if streamed else total
    print(f"{label:<36} first words after {seen:4.1f}s   complete after {total:4.1f}s")

# ============================================================================
# Session 2.2 — System prompts, templates and guardrails
# ============================================================================

import hashlib, re

TEMPLATES = {
    "claims-assistant@v7": """You are the claims assistant for {insurer}. You help claims staff, not policyholders.
Handle outpatient claims only; for anything else reply "Route to senior adjuster" with a reason.
If a needed fact is missing, list it under "Missing" instead of assuming.
If documents contradict each other, quote both and mark the clause "unclear".
Return: Summary, Eligibility, Missing, Recommended next step.""",
}
GUARDRAIL_CHECKS = {
    "scope stated":            r"\bonly\b",
    "out-of-scope behaviour":  r"for anything else|out of scope|route to",
    "missing-information rule": r"missing",
    "conflict rule":           r"contradict",
    "output format":           r"\breturn\b|format",
}

def render(template_id, variables, user_docs):
    tpl = TEMPLATES[template_id]
    needed = set(re.findall(r"{(\w+)}", tpl))
    missing = needed - set(variables)
    if missing:
        raise ValueError(f"refusing to send: missing variables {sorted(missing)}")
    system = tpl.format(**variables)
    user = "\n".join(f'<document name="{n}">\n{t}\n</document>' for n, t in user_docs.items())
    return {"system": system, "user": user,
            "_log": {"template": template_id, "sha": hashlib.sha256(tpl.encode()).hexdigest()[:8]}}

tpl = TEMPLATES["claims-assistant@v7"]
for check, pattern in GUARDRAIL_CHECKS.items():
    print(f"{'✓' if re.search(pattern, tpl, re.I) else '✗'} {check}")

req = render("claims-assistant@v7", {"insurer": "Sahyadri Health Insurance"}, {"bill.pdf": "OPD consult ₹1,200"})
print("\nlogged with the call:", req["_log"])
try:
    render("claims-assistant@v7", {}, {})
except ValueError as e:
    print("blocked:", e)

# ============================================================================
# Session 2.3 — Prompting techniques
# ============================================================================

FAILURE_MODES = {"citation inline", "citation in bibliography", "date as words", "two claims in one letter", "no amount stated"}
POOL = {   # candidate example → failure modes it demonstrates
    "ex01 simple bill, all fields clean":          set(),
    "ex02 inline citation of policy clause":       {"citation inline"},
    "ex03 clause cited only in bibliography":      {"citation in bibliography"},
    "ex04 'fifth of March', two claims in one":    {"date as words", "two claims in one letter"},
    "ex05 estimate letter with no amount":         {"no amount stated"},
    "ex06 inline citation, date as words":         {"citation inline", "date as words"},
}

chosen, uncovered = [], set(FAILURE_MODES)
while uncovered:
    best = max(POOL, key=lambda e: len(POOL[e] & uncovered))
    if not POOL[best] & uncovered: break
    chosen.append(best); uncovered -= POOL[best]
print(f"{len(chosen)} examples cover all {len(FAILURE_MODES)} failure modes:")
for c in chosen: print("  ", c, sorted(POOL[c]))
print("never chosen (adds nothing new):", [e for e in POOL if e not in chosen])

reply = """<thinking>
Order date 2 Oct, request 20 Oct: within 30 days. Category: footwear, eligible.
Opened: yes, but footwear allows opened returns. Discount: 40%, and the policy excludes items over 30% off.
</thinking>
<answer>{"eligible": false, "reason": "discount over 30% (40%)"}</answer>"""

def answer_only(text):
    m = re.search(r"<answer>\s*(.*?)\s*</answer>", text, re.S)
    if not m:
        raise ValueError("no <answer> block: treat as a failed response, don't parse the reasoning")
    return m.group(1)

print("app reads:   ", answer_only(reply))
print("audit keeps: ", len(re.search(r"<thinking>(.*?)</thinking>", reply, re.S).group(1).split()), "words of reasoning")

# ============================================================================
# Session 2.4 — Engineering the context window
# ============================================================================

history = "Customer Meera Iyer, policy SHI-77120. Agreed refund ₹8,999.50 on 14 Jan 2026 for claim CLM-40417, to be paid by 21 Jan."

def lossy_summary(text):
    """Stand-in for repeated summarisation: each pass keeps the gist and drops precision."""
    text = re.sub(r"₹([\d,]+)\.\d\d", lambda m: "about ₹" + format(round(int(m.group(1).replace(",", "")), -3), ","), text)
    text = re.sub(r"on \d{1,2} Jan 2026", "in mid-January", text)
    text = re.sub(r"by \d{1,2} Jan", "by late January", text)
    return text.replace("claim CLM-40417", "the claim").replace("policy SHI-77120", "her policy")

CASE_FACTS = {"customer": "Meera Iyer", "policy": "SHI-77120", "claim": "CLM-40417",
              "refund_amount": "₹8,999.50", "agreed_on": "2026-01-14", "pay_by": "2026-01-21"}

after = lossy_summary(history)
print("summary after compression:\n ", after)
print("\ncase facts block carried every turn:")
print("  <case_facts>" + "; ".join(f"{k}={v}" for k, v in CASE_FACTS.items()) + "</case_facts>")

import json

raw = {"status": 200, "request_id": "a8f3-77c1", "pagination": {"page": 1, "pages": 1, "per_page": 50},
       "data": {"member": {"id": "SHI-77120", "name": "Meera Iyer", "dob": "1979-03-05", "address": {"line1": "12 Palm Grove", "city": "Pune", "pin": "411001"},
                "plan": {"code": "OPD-GOLD", "opd_limit": 25000, "opd_used": 17800, "copay_pct": 10, "network": ["Ruby Hall", "Jehangir"],
                         "riders": [{"code": "DENTAL", "limit": 5000}, {"code": "VISION", "limit": 3000}]},
                "claims_history": [{"id": f"CLM-{40000 + i}", "amount": 900 + i * 37, "status": "settled"} for i in range(40)],
                "audit": {"created": "2019-04-01", "updated": "2026-10-20", "by": "sys"}}}}

def trim_for_eligibility(r):
    m = r["data"]["member"]; p = m["plan"]
    return {"member_id": m["id"], "plan": p["code"], "opd_remaining": p["opd_limit"] - p["opd_used"],
            "copay_pct": p["copay_pct"], "recent_claims": [c["id"] for c in m["claims_history"][-3:]]}

def approx_tokens(obj): return len(json.dumps(obj)) // 4
trimmed = trim_for_eligibility(raw)
print(f"raw result:     ~{approx_tokens(raw):,} tokens")
print(f"trimmed result: ~{approx_tokens(trimmed):,} tokens  {trimmed}")

# ============================================================================
# Session 2.5 — Prompt reuse: caching, modules and Skills
# ============================================================================

p_in = 2.00                                  # Claude Sonnet 5.5 input, $/MTok
TOOLS, POLICY, QUESTION = 3_000, 8_000, 150  # tokens

def run(layout, n=1_000):
    """Return (cost of input tokens, cache hit rate) for n requests with this layout."""
    cost, hits = 0.0, 0
    for i in range(n):
        if layout == "timestamp in system prompt":
            cached = 0                                         # prefix differs every request
        elif layout == "tools edited per request":
            cached = 0                                         # first block changes: nothing after it survives
        else:                                                  # stable tools + system first, question last
            cached = TOOLS + POLICY if i > 0 else 0
        uncached = TOOLS + POLICY + QUESTION - cached
        write = (TOOLS + POLICY) * 0.25 if (layout == "stable prefix, question last" and i == 0) else 0
        cost += (uncached + write + cached * 0.10) * p_in / 1e6
        hits += cached > 0
    return cost, hits / n

for layout in ["timestamp in system prompt", "tools edited per request", "stable prefix, question last"]:
    cost, rate = run(layout)
    print(f"{layout:<32} input cost for 1,000 requests ${cost:6.2f}   cache hits {rate:.0%}")

MODULES = {"role.claims": 350, "format.eligibility": 180, "policy.outpatient": 8_000, "policy.dental": 2_400,
           "policy.vision": 1_900, "examples.extraction": 1_200, "examples.letters": 900}
NEEDS = {"outpatient eligibility": ["role.claims", "format.eligibility", "policy.outpatient", "examples.extraction"],
         "dental eligibility":     ["role.claims", "format.eligibility", "policy.dental", "examples.extraction"],
         "missing-document letter": ["role.claims", "examples.letters"]}

everything = sum(MODULES.values())
for task, mods in NEEDS.items():
    print(f"{task:<25} assembled {sum(MODULES[m] for m in mods):>6,} tokens   vs send-everything {everything:,}")
skills_baseline = 7 * 100
print(f"\nas Skills: ~{skills_baseline} tokens of descriptions always loaded; each task loads only its own bodies")
