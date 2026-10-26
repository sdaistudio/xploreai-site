# Claude Certified Architect – Professional: study course — Module 6: Stakeholder Communication & Lifecycle Management
# https://xploreai.co.in/courses/claude-architect/module-6/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 6.1 — Structured discovery
# ============================================================================

STAKEHOLDERS = [  # name, power 1–5, interest 1–5, main concern
    ("CFO (sponsor)", 5, 4, "cost per claim, payback"),
    ("Head of claims operations", 4, 5, "cycle time, staffing"),
    ("Claims adjusters", 2, 5, "trust, extra review work"),
    ("CISO", 5, 2, "PHI handling, vendor risk"),
    ("Legal & compliance", 4, 3, "IRDAI rules, audit trail"),
    ("Customer service team", 2, 2, "fewer 'where is my claim' calls"),
]

def quadrant(power, interest):
    if power >= 4 and interest >= 4: return "manage closely"
    if power >= 4:                   return "keep satisfied"
    if interest >= 4:                return "keep informed"
    return "monitor"

for name, p, i, concern in sorted(STAKEHOLDERS, key=lambda s: (-s[1], -s[2])):
    print(f"{quadrant(p, i):<15} {name:<28} {concern}")

QUESTIONS = {  # area: (question, answer or None, critical?)
    "process":     ("Current steps and handoffs for a claim", "7 steps; 3 handoffs; doc review takes 40%", True),
    "volume":      ("Claims per day, peak vs average", "6,000/month; Monday peak 2.3×", True),
    "baseline":    ("Current cycle time and error rate", "9 days median; 6% rework", True),
    "success":     ("Target outcome, in numbers", "median under 5 days; accuracy ≥97% on fields", True),
    "data":        ("Where documents live; formats; languages", "S3 PDFs; English, Hindi, Marathi", True),
    "constraints": ("Regulatory, residency, retention", None, True),
    "decision":    ("Who may approve payouts", "licensed adjusters only", True),
    "exceptions":  ("Which cases must always go to people", None, False),
    "integration": ("Systems to read from / write to", "core claims system (read), document store", False),
}
answered = [k for k, (_, a, _) in QUESTIONS.items() if a]
blocking = [k for k, (_, a, crit) in QUESTIONS.items() if a is None and crit]
print(f"answered {len(answered)}/{len(QUESTIONS)}")
print("blocking design (critical, unanswered):", blocking or "none")
print("open but not blocking:", [k for k, (_, a, c) in QUESTIONS.items() if a is None and not c])

# ============================================================================
# Session 6.2 — Communicating decisions and trade-offs
# ============================================================================

DECISION = {
    "what": "fixed workflow on Claude Sonnet 5.5, adjuster approves every payout",
    "outcome": "median settle time 9 → under 5 days", "cost": "≈ $3,060 a month in model usage",
    "rejected": "autonomous agent: same accuracy, about 6× the cost and 4× slower",
    "risk": "a new claim type needs a code change, about 2 weeks",
    "data": "documents stay in the India region; PHI redacted from logs; no data used for training",
    "controls": "no payout tool; per-user authorisation; audit trail with model and prompt versions",
    "interfaces": "POST /claims/{id}/extract returns the 14-field schema v3; p95 ≤ 11 s; retries 2×",
}
VIEWS = {
    "executive": ["what", "outcome", "cost", "rejected", "risk"],
    "security":  ["what", "data", "controls"],
    "engineering": ["what", "interfaces", "risk", "rejected"],
}
for audience, fields in VIEWS.items():
    print(f"── for {audience}")
    for f in fields:
        print(f"   {f}: {DECISION[f]}")

# ============================================================================
# Session 6.3 — Feedback loops and SLAs
# ============================================================================

DAYS = [  # requests, failures, p95_ms, maintenance_window?
    *[(40_000, 120, 6_200, False)] * 26,
    (40_000, 2_900, 9_800, False),      # incident: provider overload
    (38_000, 140, 6_400, True),         # planned maintenance (excluded)
    (41_000, 110, 6_100, False), (39_500, 135, 7_900, False),
]
SLO_SUCCESS, SLO_P95 = 0.995, 8_000
counted = [d for d in DAYS if not d[3]]
reqs = sum(d[0] for d in counted); fails = sum(d[1] for d in counted)
success = 1 - fails / reqs
p95_breach_days = sum(d[2] > SLO_P95 for d in counted)

print(f"success rate (excl. maintenance): {success:.3%}  target {SLO_SUCCESS:.1%}  → {'MET' if success >= SLO_SUCCESS else 'MISSED'}")
print(f"days with p95 > {SLO_P95:,} ms: {p95_breach_days} of {len(counted)}")
credit = 0.10 if success < SLO_SUCCESS else 0.0
print(f"service credit due: {credit:.0%}")

REPORTS = ["wrong amount", "too long", "wrong amount", "missed hospitalisation exception", "slow", "wrong amount",
           "too long", "missed hospitalisation exception", "missed hospitalisation exception", "slow", "wrong amount",
           "tone too formal", "missed hospitalisation exception", "wrong amount"]
TRAFFIC = 6_000
from collections import Counter
counts = Counter(REPORTS)
for issue, n in counts.most_common():
    action = "add failing cases to eval set; fix" if n >= 4 else ("watch" if n >= 2 else "log")
    print(f"{n:>3}  {issue:<34} {n / TRAFFIC:.2%} of claims   → {action}")

# ============================================================================
# Session 6.4 — Architecture documentation and implementation guidance
# ============================================================================

REQUIRED_SECTIONS = ["components", "request flow", "integrations", "constraints", "model and version",
                     "prompt location and versioning", "context assembly", "eval set and thresholds",
                     "fallback behaviour", "human review points", "owner"]
doc = """# Claims assistant: architecture
## Components ... ## Request flow ... ## Integrations ... ## Constraints ...
## Model and version: claude-sonnet-5-5 ... ## Context assembly ... ## Eval set and thresholds ...
## Human review points ..."""

present = [s for s in REQUIRED_SECTIONS if s in doc.lower()]
missing = [s for s in REQUIRED_SECTIONS if s not in present]
print(f"{len(present)}/{len(REQUIRED_SECTIONS)} sections present")
print("missing before handoff:", missing)

# ============================================================================
# Session 6.5 — The solution life cycle
# ============================================================================

TRIGGERS = [  # metric, current, threshold, direction, action
    ("eval pass rate (monthly re-run)", 0.952, 0.95, "below", "investigate; block releases until restored"),
    ("judge pass rate, live sample", 0.91, 0.93, "below", "pull failing traces; add cases; fix"),
    ("human review load (items/day)", 610, 540, "above", "recalibrate thresholds or add reviewers"),
    ("cost per settled claim (₹)", 3.4, 4.0, "above", "check cache hits and retries"),
    ("days to model deprecation", 75, 90, "below", "start migration: evals on the successor model"),
]
for metric, cur, thr, direction, action in TRIGGERS:
    fired = cur < thr if direction == "below" else cur > thr
    print(f"{'FIRED' if fired else 'ok   '}  {metric:<32} {cur:<7} ({direction} {thr})  {action if fired else ''}")
