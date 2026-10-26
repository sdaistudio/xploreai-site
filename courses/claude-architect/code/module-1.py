# Claude Certified Architect – Professional: study course — Module 1: Solution Design & Architecture
# https://xploreai.co.in/courses/claude-architect/module-1/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 1.1 — From business problem to Claude solution
# ============================================================================

REQUIREMENTS = {
    "R1": "Extract 14 fields from each claim pack with ≥97% accuracy",
    "R2": "Flag missing mandatory documents",
    "R3": "Every payout decision approved by a licensed adjuster",
    "R4": "Audit trail of inputs, model version, prompt version and outputs",
    "R5": "Median end-to-end time under 5 days",
    "R6": "Patient health data never leaves the India region",
}
COMPONENTS = {   # component → requirements it implements
    "extractor (Claude Sonnet, structured outputs)": ["R1"],
    "document checklist (rules in code)":           ["R2"],
    "approval queue (adjuster UI)":                  ["R3"],
    "trace store":                                   ["R4"],
    "claims dashboard":                              [],
}
TESTS = {        # test → requirements it verifies
    "eval: 300 labelled claim packs":     ["R1"],
    "unit: checklist rules":              ["R2"],
    "integration: payout blocked without approval": ["R3"],
    "load test: 2,000 packs/day":         ["R5"],
}

implemented = {r for rs in COMPONENTS.values() for r in rs}
verified = {r for rs in TESTS.values() for r in rs}
for rid, text in REQUIREMENTS.items():
    gaps = [g for g, ok in (("no component", rid in implemented), ("no test", rid in verified)) if not ok]
    print(f"{rid} {'OK ' if not gaps else 'GAP'} {text[:58]:<58} {', '.join(gaps)}")
orphans = [c for c, rs in COMPONENTS.items() if not rs]
print("\ncomponents serving no requirement:", orphans)

# ============================================================================
# Session 1.2 — End-to-end architecture and feedback loops
# ============================================================================

SLA_P95_MS = 8_000
stages = [  # stage, budget ms, measured p95 ms
    ("gateway + auth",          200,   140),
    ("retrieval (vector + rerank)", 900, 1_350),
    ("Claude first token",     1_500, 1_200),
    ("Claude full answer",     4_000, 3_900),
    ("output checks",           600,   420),
    ("delivery",                300,   180),
]
budget_total = sum(b for _, b, _ in stages)
measured_total = sum(m for _, _, m in stages)
print(f"{'stage':<30}{'budget':>8}{'p95':>8}")
for name, b, m in stages:
    print(f"{name:<30}{b:>8,}{m:>8,}{'  ← over budget' if m > b else ''}")
print(f"{'total':<30}{budget_total:>8,}{measured_total:>8,}   SLA {SLA_P95_MS:,}")
print(f"headroom vs SLA: {SLA_P95_MS - measured_total:,} ms (summing p95s overstates the true end-to-end p95, so this is conservative)")

# ============================================================================
# Session 1.3 — Choosing the pattern
# ============================================================================

P_IN, P_OUT = 2.00, 10.00            # Claude Sonnet 5.5, $ per million tokens
designs = {   # calls, input tokens per call, output tokens per call, p95 seconds, accuracy on eval (illustrative)
    "augmented LLM (1 call + retrieval)":      (1, 9_000, 900, 6,  0.93),
    "workflow (extract → validate → draft)":   (3, 5_000, 700, 11, 0.97),
    "agent (explores, calls tools as needed)": (9, 14_000, 600, 48, 0.97),
}
runs_per_month = 60_000
print(f"{'design':<42}{'$/run':>8}{'$/month':>10}{'p95 s':>7}{'acc':>6}")
for name, (calls, tin, tout, p95, acc) in designs.items():
    per_run = calls * (tin * P_IN + tout * P_OUT) / 1e6
    print(f"{name:<42}{per_run:>8.3f}{per_run * runs_per_month:>10,.0f}{p95:>7}{acc:>6.0%}")

# ============================================================================
# Session 1.4 — Multi-agent orchestration
# ============================================================================

TASKS = {   # task: (seconds, depends on)
    "fetch Q3 P&L":        (8, []),
    "fetch Q2 P&L":        (7, []),
    "competitor scan":     (9, []),
    "margin analysis":     (6, ["fetch Q3 P&L", "fetch Q2 P&L"]),
    "risk review":         (5, ["competitor scan"]),
    "executive summary":   (4, ["margin analysis", "risk review"]),
}

def waves(tasks):
    done, out = set(), []
    while len(done) < len(tasks):
        ready = [t for t, (_, deps) in tasks.items() if t not in done and all(d in done for d in deps)]
        if not ready: raise ValueError("cycle in dependencies")
        out.append(ready); done.update(ready)
    return out

plan = waves(TASKS)
for i, w in enumerate(plan, 1):
    print(f"wave {i}: {w}  ({max(TASKS[t][0] for t in w)} s)")
sequential = sum(s for s, _ in TASKS.values())
parallel = sum(max(TASKS[t][0] for t in w) for w in plan)
print(f"\nall in sequence: {sequential} s   in dependency-respecting waves: {parallel} s")

REQUIRED = ["revenue", "margins", "competitors", "staffing risk", "regulatory risk"]
ASSIGNED = {"finance": ["revenue", "margins"], "market": ["competitors"], "risk": ["staffing risk"]}
RETURNED = {"finance": {"revenue": "+12% QoQ", "margins": "31% → 29%"},
            "market": {"competitors": "2 openings within 3 km"},
            "risk": {"error": "permission denied reading HR roster"}}
FINAL = {"revenue": "+12% QoQ", "competitors": "2 openings within 3 km"}

for topic in REQUIRED:
    owner = next((a for a, ts in ASSIGNED.items() if topic in ts), None)
    if owner is None:                        stage = "DECOMPOSITION: never assigned"
    elif "error" in RETURNED.get(owner, {}): stage = f"SUBAGENT ERROR ({owner}): {RETURNED[owner]['error']}"
    elif topic not in RETURNED[owner]:       stage = f"CONTEXT/TASK ({owner}): not returned"
    elif topic not in FINAL:                 stage = "AGGREGATION: returned but dropped"
    else:                                    stage = "ok"
    print(f"{topic:<16} {stage}")

# ============================================================================
# Session 1.5 — Decomposition
# ============================================================================

import re

REQS = {"revenue trend", "margin drivers", "staffing risks", "board-ready summary"}
PLAN = [
    {"id": "A", "objective": "Compute revenue trend per clinic", "inputs": ["P&L Q2", "P&L Q3"], "output": "table", "covers": ["revenue trend"], "after": []},
    {"id": "B", "objective": "Explain margin drivers and draft commentary and check compliance", "inputs": ["A.table"], "output": "text", "covers": ["margin drivers"], "after": ["A"]},
    {"id": "C", "objective": "List staffing risks", "inputs": [], "output": "", "covers": ["staffing risks"], "after": ["D"]},
    {"id": "E", "objective": "Write board summary", "inputs": ["A.table", "B.text", "C.list"], "output": "1-page memo", "covers": ["board-ready summary"], "after": ["A", "B", "C"]},
]

ids = {t["id"] for t in PLAN}
for t in PLAN:
    issues = []
    if len(re.findall(r"\band\b", t["objective"])) >= 1: issues.append("more than one objective")
    if not t["inputs"]: issues.append("no inputs: it will have to guess")
    if not t["output"]: issues.append("no defined output")
    issues += [f"depends on missing task {d}" for d in t["after"] if d not in ids]
    print(f"{t['id']}: {t['objective'][:48]:<48} {'; '.join(issues) or 'ok'}")
covered = {c for t in PLAN for c in t["covers"]}
print("\nuncovered requirements:", sorted(REQS - covered) or "none")

# ============================================================================
# Session 1.6 — Business value pillars
# ============================================================================

def business_case(adoption, months=12):
    claims = 6_000                          # claims per month
    minutes_saved_per_claim = 38            # when the assistant is used
    staff_cost_per_hour = 900               # ₹, fully loaded
    review_minutes = 6                      # human checking of each AI draft
    run_cost_per_claim = 9                  # ₹: tokens, retrieval, infra
    build = 4_500_000                       # ₹ one-off: design, build, evals, integration
    ops_per_month = 600_000                 # ₹: monitoring, prompt and eval upkeep, on-call, licences
    used = claims * adoption
    saving = used * (minutes_saved_per_claim - review_minutes) / 60 * staff_cost_per_hour
    run = used * run_cost_per_claim
    net_month = saving - run - ops_per_month
    total = net_month * months - build
    payback = build / net_month if net_month > 0 else float("inf")
    return net_month, total, payback

for adoption in (0.3, 0.6, 0.9):
    net, total, payback = business_case(adoption)
    pb = f"{payback:.1f} months" if payback != float("inf") else "never"
    print(f"adoption {adoption:.0%}: net ₹{net:>10,.0f}/month   12-month ₹{total:>12,.0f}   payback {pb}")
