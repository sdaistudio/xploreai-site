# Claude Certified Architect – Professional: study course — Module 5: Governance, Safety & Risk Management
# https://xploreai.co.in/courses/claude-architect/module-5/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 5.1 — Guardrails and safety controls
# ============================================================================

CONTROLS = {   # control: (kind, hard = enforced outside the model?)
    "system-prompt scope rules":       ("directive", False),
    "input screening for injection":   ("preventive", False),
    "read-only claims tool":           ("preventive", True),
    "payout tool removed from agent":  ("preventive", True),
    "adjuster approval for decisions": ("preventive", True),
    "PreToolUse hook: block bulk export": ("preventive", True),
    "output PII check":                ("detective", True),
    "audit log of every tool call":    ("detective", True),
    "kill switch per route":           ("corrective", True),
}
THREATS = {
    "prompt injection via claim documents": ["input screening for injection", "system-prompt scope rules", "payout tool removed from agent"],
    "unauthorised payout":                  ["payout tool removed from agent", "adjuster approval for decisions", "audit log of every tool call"],
    "bulk export of patient data":          ["PreToolUse hook: block bulk export", "output PII check", "audit log of every tool call"],
    "off-topic or harmful replies":         ["system-prompt scope rules"],
    "hallucinated policy clauses":          ["system-prompt scope rules", "input screening for injection"],
}

for threat, used in THREATS.items():
    kinds = {CONTROLS[c][0] for c in used}
    hard_preventive = any(CONTROLS[c] == ("preventive", True) for c in used)
    gaps = []
    if not hard_preventive: gaps.append("no hard preventive control")
    if "detective" not in kinds: gaps.append("no detective control")
    print(f"{'GAP' if gaps else 'OK '} {threat:<38} {'; '.join(gaps)}")

# ============================================================================
# Session 5.2 — Risks and failure modes
# ============================================================================

APPETITE = 6   # residual scores above this need action or a signed acceptance
REGISTER = [  # risk, likelihood 1–5, impact 1–5, control effectiveness 0–1, owner
    ("Prompt injection triggers a payout",    3, 5, 0.85, "Security"),
    ("Hallucinated policy clause in a letter", 4, 4, 0.40, "Claims product"),
    ("PHI written to application logs",       3, 5, 0.70, "Platform"),
    ("Over-reliance: adjusters stop checking", 4, 4, 0.25, "Claims operations"),
    ("Model deprecation breaks the pipeline", 2, 3, 0.80, "Platform"),
    ("Lower accuracy on Marathi documents",   3, 4, 0.20, "Claims product"),
]
rows = []
for risk, l, i, eff, owner in REGISTER:
    inherent = l * i
    residual = round(inherent * (1 - eff), 1)
    rows.append((residual, risk, inherent, owner))
print(f"{'risk':<40}{'inherent':>9}{'residual':>9}  owner")
for residual, risk, inherent, owner in sorted(rows, reverse=True):
    flag = "  ← above appetite" if residual > APPETITE else ""
    print(f"{risk:<40}{inherent:>9}{residual:>9}  {owner}{flag}")

# ============================================================================
# Session 5.3 — Human-in-the-loop validation
# ============================================================================

def should_escalate(case):
    if case.get("asks_for_human"):                        return True,  "explicit request: hand over now, with context"
    if case.get("policy_covers") is False:                return True,  "authority gap: policy silent or ambiguous"
    if case.get("check_failed"):                          return True,  "verification flag: confirm before continuing"
    if case.get("stakes") == "high" and case.get("confidence", 1) < 0.7:
                                                          return True,  "high stakes, low confidence"
    reasons = [r for r, k in (("frustration", "frustrated"), ("complexity", "complex")) if case.get(k)]
    return False, ("not a trigger on its own: " + " and ".join(reasons)) if reasons else "resolve"

cases = [
    ("Angry customer, refund status question",           dict(frustrated=True, policy_covers=True)),
    ("Calm customer: 'can I talk to a person?'",         dict(asks_for_human=True)),
    ("Asks us to match a competitor's price",            dict(policy_covers=False)),
    ("Refactor across 30 files, tests still passing",    dict(complex=True, policy_covers=True)),
    ("Dosage question, model unsure",                    dict(stakes="high", confidence=0.55, policy_covers=True)),
    ("Bank details on file don't match the claim form",  dict(check_failed=True)),
    ("Angry and asks for a manager",                     dict(frustrated=True, asks_for_human=True)),
]
for name, c in cases:
    esc, why = should_escalate(c)
    print(f"{'ESCALATE' if esc else 'resolve ':<8}  {name:<50} {why}")

import random
random.seed(5)
confidences = [min(1.0, max(0.0, random.gauss(0.86, 0.09))) for _ in range(4_000)]   # one day's items
REVIEWERS, PER_REVIEWER = 6, 90          # items each reviewer can check properly per day
AUDIT_RATE = 0.02

for threshold in (0.70, 0.75, 0.80, 0.85):
    flagged = sum(c < threshold for c in confidences)
    audited = round((len(confidences) - flagged) * AUDIT_RATE)
    load = flagged + audited
    fits = "fits" if load <= REVIEWERS * PER_REVIEWER else "over capacity"
    print(f"review below {threshold:.2f}: {flagged:>5} flagged + {audited:>3} audit samples = {load:>5}  ({fits}: capacity {REVIEWERS * PER_REVIEWER})")

# ============================================================================
# Session 5.4 — Regulatory compliance
# ============================================================================

DESIGN = {
    "data_region": "ap-south-1", "model_path": "Claude via cloud platform, India region",
    "vendor_agreements": {"model provider": "DPA", "vector DB": "DPA", "logging SaaS": None},
    "baa_signed_with": [], "phi_in_scope": True, "eu_users": True,
    "log_retention_days": 365, "erasure_covers": ["database"], "human_decides_significant": True,
    "encryption_at_rest": True, "audit_trail": True, "fedramp_needed": False,
}

def check(d):
    gaps = []
    missing = [v for v, a in d["vendor_agreements"].items() if a is None]
    if missing: gaps.append(("GDPR", f"no data processing agreement with: {', '.join(missing)}"))
    if d["eu_users"] and d["data_region"] not in ("eu-west-1", "eu-central-1"):
        gaps.append(("GDPR", "EU personal data stored outside the EU: confirm a valid transfer mechanism"))
    if set(["logs", "vector index"]) - set(d["erasure_covers"]):
        gaps.append(("GDPR", "erasure requests don't reach logs and the vector index"))
    if d["phi_in_scope"] and len(d["baa_signed_with"]) < len(d["vendor_agreements"]):
        gaps.append(("HIPAA", "PHI in scope but BAAs not in place with every vendor that processes it"))
    if d["log_retention_days"] > 180:
        gaps.append(("policy", f"logs kept {d['log_retention_days']} days: justify or shorten (minimisation)"))
    if d["fedramp_needed"]:
        gaps.append(("FedRAMP", "confirm the authorisation level of the whole data path"))
    return gaps

for regime, gap in check(DESIGN):
    print(f"{regime:<8} {gap}")

# ============================================================================
# Session 5.5 — Bias, fairness and transparency
# ============================================================================

RESULTS = {  # language: (cases, eligible per experts, AI said eligible, AI correct on eligible, AI correct on ineligible)
    "English":  (400, 300, 296, 291, 95),
    "Hindi":    (250, 185, 176, 172, 61),
    "Marathi":  (150, 112, 92,  90,  36),
}
print(f"{'language':<9}{'AI approval':>12}{'expert approval':>16}{'missed eligible':>16}{'accuracy':>10}")
for lang, (n, elig, ai_yes, tp, tn) in RESULTS.items():
    missed = (elig - tp) / elig
    print(f"{lang:<9}{ai_yes / n:>12.0%}{elig / n:>16.0%}{missed:>16.1%}{(tp + tn) / n:>10.0%}")
