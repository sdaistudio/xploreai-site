# Claude Certified Architect – Professional: study course — Module 4: Evaluation, Testing & Optimization
# https://xploreai.co.in/courses/claude-architect/module-4/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 4.1 — Evaluation metrics
# ============================================================================

CASES = [  # gold fields, predicted fields, latency_s, cost_inr, retries, is_attack, attack_succeeded, unsafe, wrongly_refused
    ({"amount": "850", "date": "2026-10-14", "doctor": "Rao"},  {"amount": "850", "date": "2026-10-14", "doctor": "Rao"},  3.1, 2.4, 0, False, False, False, False),
    ({"amount": "1200", "date": "2026-10-02", "doctor": "Iyer"}, {"amount": "1200", "date": "2026-10-20", "doctor": "Iyer"}, 4.0, 2.6, 0, False, False, False, False),
    ({"amount": "430", "date": "2026-09-30", "doctor": "Shah"},  {"amount": "430", "date": "2026-09-30"},                   2.8, 2.2, 1, False, False, False, False),
    ({"amount": "9900", "date": "2026-10-11", "doctor": "Rao"},  {},                                                       1.2, 0.9, 0, False, False, False, True),
    ({}, {}, 2.2, 1.8, 0, True, False, False, False),
    ({}, {}, 2.9, 2.0, 0, True, True,  False, False),
    ({"amount": "300", "date": "2026-10-19", "doctor": "Desai"}, {"amount": "300", "date": "2026-10-19", "doctor": "Desai"}, 9.4, 3.9, 2, False, False, False, False),
]

tp = fp = fn = 0
for gold, pred, *_ in CASES:
    for k, v in pred.items():
        if gold.get(k) == v: tp += 1
        else: fp += 1
    fn += sum(1 for k in gold if gold.get(k) != pred.get(k))
precision, recall = tp / (tp + fp), tp / (tp + fn)
f1 = 2 * precision * recall / (precision + recall)

normal = [c for c in CASES if not c[5]]
success = [c for c in normal if c[0] and c[0] == c[1]]
lat = sorted(c[2] for c in CASES)
p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))]
cost_per_success = sum(c[3] for c in normal) / len(success)
attacks = [c for c in CASES if c[5]]

card = [("field F1", f1, 0.97, ">="), ("task success", len(success) / len(normal), 0.95, ">="),
        ("total p95 (s)", p95, 8.0, "<="), ("₹ per successful task", cost_per_success, 4.0, "<="),
        ("over-refusal rate", sum(c[8] for c in normal) / len(normal), 0.01, "<="),
        ("injection success", sum(c[6] for c in attacks) / len(attacks), 0.0, "<=")]
for name, value, target, op in card:
    ok = value >= target if op == ">=" else value <= target
    print(f"{'PASS' if ok else 'FAIL'}  {name:<22} {value:>7.2f}   target {op} {target}")

# ============================================================================
# Session 4.2 — Eval datasets and mixed methods
# ============================================================================

import random
random.seed(3)

POOLS = {"golden": 180, "production": 2_400, "edge": 95, "adversarial": 60, "synthetic": 500, "incidents": 22}
QUOTA = {"golden": 120, "production": 200, "edge": 60, "adversarial": 60, "synthetic": 40, "incidents": 22}
CATEGORIES = ["outpatient", "diagnostics", "pharmacy", "dental", "maternity"]

dataset = []
for source, n in QUOTA.items():
    for i in range(min(n, POOLS[source])):
        dataset.append({"id": f"{source}-{i}", "source": source,
                        "category": random.choice(CATEGORIES if source != "edge" else CATEGORIES[3:])})
print(f"eval set v12: {len(dataset)} items")
for source in QUOTA:
    print(f"  {source:<12} {sum(d['source'] == source for d in dataset):>4}")
by_cat = {c: sum(d["category"] == c for d in dataset if d["source"] != "adversarial") for c in CATEGORIES}
print("by category (excluding adversarial):", by_cat)

GRADERS = {"field accuracy": "code", "output format": "code", "faithful to policy text": "LLM judge (validated vs human labels)",
           "tone for anxious patients": "LLM judge", "payout eligibility decision": "human expert", "injection resisted": "code"}
print("\ngrading plan:")
for criterion, method in GRADERS.items():
    print(f"  {criterion:<28} → {method}")

# ============================================================================
# Session 4.3 — A/B testing and iterative improvement
# ============================================================================

import math

def n_per_arm(p_base, lift_abs, z_a=1.96, z_b=0.84):
    p2 = p_base + lift_abs
    p_bar = (p_base + p2) / 2
    return math.ceil(((z_a * math.sqrt(2 * p_bar * (1 - p_bar)) + z_b * math.sqrt(p_base * (1 - p_base) + p2 * (1 - p2))) / lift_abs) ** 2)

for lift in (0.10, 0.05, 0.02, 0.01):
    print(f"task success 80% → {80 + lift * 100:.0f}%: {n_per_arm(0.80, lift):>7,} conversations per arm")

def two_proportion_test(success_a, n_a, success_b, n_b):
    pa, pb = success_a / n_a, success_b / n_b
    p = (success_a + success_b) / (n_a + n_b)
    z = (pb - pa) / math.sqrt(p * (1 - p) * (1 / n_a + 1 / n_b))
    p_value = math.erfc(abs(z) / math.sqrt(2))
    return pa, pb, z, p_value

results = {"task success (primary)":     (1_640, 2_050, 1_712, 2_048),
           "escalation rate (guardrail)": (287, 2_050, 266, 2_048),
           "complaints (guardrail)":     (31, 2_050, 52, 2_048)}
for metric, (sa, na, sb, nb) in results.items():
    pa, pb, z, pv = two_proportion_test(sa, na, sb, nb)
    verdict = "significant" if pv < 0.05 else "not significant"
    print(f"{metric:<28} A {pa:6.1%}  B {pb:6.1%}  z={z:+.2f}  p={pv:.3f}  {verdict}")

# ============================================================================
# Session 4.4 — Diagnosing system issues
# ============================================================================

from dataclasses import dataclass, field

@dataclass
class SubagentError:
    attempted: str
    category: str              # transient | permission | invalid_input | not_found | business_rule
    retryable: bool
    source_checked: bool       # True: looked and found nothing. False: couldn't look at all.
    partial: list = field(default_factory=list)

def coordinator_decision(e):
    if e.category == "not_found" and e.source_checked:
        return "record genuinely absent: say so in the answer, don't retry"
    if e.retryable:
        return "retry once with backoff, then try the alternative source"
    if e.category == "permission":
        return f"don't retry: use the {len(e.partial)} partial result(s), flag the gap, request access or escalate"
    return "escalate with the full error context"

errors = [
    SubagentError("query claims DB for CLM-40417 (2 tries)", "permission", False, False, partial=["CLM-40417 header"]),
    SubagentError("search policy index for 'dental rider'", "not_found", False, True),
    SubagentError("call pharmacy API", "transient", True, False),
]
for e in errors:
    print(f"{e.attempted:<42} → {coordinator_decision(e)}")

# ============================================================================
# Session 4.5 — Optimising cost and performance
# ============================================================================

N = 100_000
haiku_cost, sonnet_cost = 0.0009, 0.0180          # $ per request (illustrative token mix)
haiku_acc_easy, haiku_acc_hard, sonnet_acc = 0.97, 0.70, 0.96
hard_share = 0.25
gate_catches_hard, gate_false_alarm = 0.85, 0.08  # how well the escalation check works

all_sonnet_cost, all_sonnet_acc = N * sonnet_cost, sonnet_acc
easy, hard = N * (1 - hard_share), N * hard_share
escalated = hard * gate_catches_hard + easy * gate_false_alarm
cascade_cost = N * haiku_cost + escalated * sonnet_cost
correct = (easy * (1 - gate_false_alarm) * haiku_acc_easy + easy * gate_false_alarm * sonnet_acc +
           hard * gate_catches_hard * sonnet_acc + hard * (1 - gate_catches_hard) * haiku_acc_hard)
print(f"all Sonnet: ${all_sonnet_cost:,.0f}   accuracy {all_sonnet_acc:.1%}")
print(f"cascade:    ${cascade_cost:,.0f}   accuracy {correct / N:.1%}   ({escalated / N:.0%} escalated)")
for catch in (0.95, 0.60):
    esc = hard * catch + easy * gate_false_alarm
    acc = (easy * (1 - gate_false_alarm) * haiku_acc_easy + easy * gate_false_alarm * sonnet_acc +
           hard * catch * sonnet_acc + hard * (1 - catch) * haiku_acc_hard) / N
    print(f"  if the gate caught {catch:.0%} of hard cases: ${N * haiku_cost + esc * sonnet_cost:,.0f}, accuracy {acc:.1%}")

# ============================================================================
# Session 4.6 — Monitoring and observability
# ============================================================================

SLO = 0.995
budget = 1 - SLO
hourly = [(12_000, 30), (11_800, 41), (12_400, 35), (12_100, 520), (11_900, 610), (12_300, 44)]  # (requests, failures)

for hour, (req, fail) in enumerate(hourly, 1):
    burn = (fail / req) / budget
    action = "PAGE: budget gone in ~{:.0f} h at this rate".format(30 * 24 / burn) if burn > 14.4 else ("ticket" if burn > 2 else "ok")
    print(f"hour {hour}: failure rate {fail / req:6.2%}  burn rate {burn:5.1f}×  {action}")
