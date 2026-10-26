# Claude Certified Associate – Foundations: study course — Module 6: Governance, Risk, and Responsible Use
# https://xploreai.co.in/courses/claude-associate/module-6/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 6.1 — Appropriate and inappropriate uses
# ============================================================================

PROHIBITED = ["impersonate", "fake reviews", "track my employee's personal phone", "phishing", "deepfake"]
HIGH_RISK = {"medical": ["diagnos", "dosage", "treatment plan"], "employment": ["reject candidates", "rank candidates", "promotion"],
             "credit": ["loan", "credit"], "insurance": ["insurance claim"], "legal": ["legal advice", "court"],
             "education": ["grade students", "exam result"]}

def triage(request):
    r = request.lower()
    if any(p in r for p in PROHIBITED):
        return "not allowed"
    areas = [a for a, words in HIGH_RISK.items() if any(w in r for w in words)]
    if areas:
        return f"high-risk ({', '.join(areas)}): qualified human review + disclosure"
    return "allowed: normal review"

for req in ["Draft a job advert for a dental assistant",
            "Rank candidates and reject the bottom half automatically",
            "Write five fake reviews for our clinic",
            "Summarise this patient's symptoms into a draft treatment plan for the dentist",
            "Brainstorm names for our newsletter",
            "Decide whether to approve this patient's EMI loan application"]:
    print(f"{req:<78} -> {triage(req)}")

# ============================================================================
# Session 6.2 — Data sensitivity and privacy
# ============================================================================

import re

rows = [
    "Anita Desai, +91 98200 12345, anita.d@example.com, Aadhaar 4521 8890 1234, missed 3 appointments",
    "Rahul Mehta, 9819011223, rahul@example.in, PAN ABCPM1234K, outstanding balance Rs 4,500",
    "Sara Khan, +91-99300-45678, sara.k@example.com, missed 1 appointment",
]
PATTERNS = [
    ("EMAIL",   r"[\w.+-]+@[\w-]+\.[\w.]+"),
    ("AADHAAR", r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    ("PAN",     r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    ("PHONE",   r"(?:\+91[\s-]?)?\b[6-9]\d{4}[\s-]?\d{5}\b"),
    ("NAME",    r"^[A-Z][a-z]+ [A-Z][a-z]+"),
]
key, counts = {}, {}

def redact(text):
    for label, pattern in PATTERNS:
        def swap(m):
            counts[label] = counts.get(label, 0) + 1
            token = f"[{label}_{counts[label]}]"
            key[token] = m.group(0)
            return token
        text = re.sub(pattern, swap, text)
    return text

safe = [redact(r) for r in rows]
print("\n".join(safe))
print(f"\nreplaced {len(key)} identifiers; the key stays on your machine, e.g. [NAME_2] -> {key['[NAME_2]']}")

# ============================================================================
# Session 6.3 — Following AI policy and governance
# ============================================================================

TOOL_APPROVED_FOR = {   # tool -> highest data class it is approved for (example policy)
    "personal Claude account": "public",
    "company Claude Team workspace": "confidential",
    "company Claude Team, 'Finance' Project (restricted access)": "restricted",
}
ORDER = ["public", "internal", "confidential", "restricted"]

def allowed(tool, data_class, customer_facing=False):
    ok = ORDER.index(data_class) <= ORDER.index(TOOL_APPROVED_FOR[tool])
    verdict = "allowed" if ok else "NOT allowed: use an approved tool or reduce the data"
    if ok and customer_facing:
        verdict += "; needs human review before sending"
    return verdict

requests = [
    ("personal Claude account", "public", False, "Rewrite our published FAQ"),
    ("personal Claude account", "internal", False, "Summarise this week's team meeting notes"),
    ("company Claude Team workspace", "confidential", True, "Draft a reply to a supplier dispute"),
    ("company Claude Team workspace", "restricted", False, "Analyse the payroll file"),
]
for tool, cls, facing, what in requests:
    print(f"{what:<42} [{cls:<12}] via {tool:<31} -> {allowed(tool, cls, facing)}")

# ============================================================================
# Session 6.4 — Ethical implications
# ============================================================================

shortlist = {  # group: (applicants, shortlisted)
    "Group A": (120, 48),
    "Group B": (80, 22),
    "Group C": (40, 15),
}
rates = {g: s / n for g, (n, s) in shortlist.items()}
top = max(rates.values())
for g, r in rates.items():
    ratio = r / top
    flag = "investigate" if ratio < 0.8 else "ok"
    print(f"{g}: {rates[g]:.0%} shortlisted, {ratio:.2f} of the highest rate -> {flag}")
