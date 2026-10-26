# Claude Certified Associate – Foundations: study course — Module 5: Configuration and Knowledge Management
# https://xploreai.co.in/courses/claude-associate/module-5/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 5.1 — Configuring a Project
# ============================================================================

import re

instructions = ("You write messages to patients for a three-clinic dental chain in Mumbai. "
                "Use plain English, under 120 words, warm and direct. Use prices and timings only "
                "from the knowledge files; if something isn't there, say 'please confirm with the clinic'.")
knowledge = ["Price sheet - 2026-03.pdf", "Price sheet - 2025-11.pdf", "Clinic timings and addresses.docx",
             "Brand voice guide.pdf", "Message templates (approved).docx", "Staff salaries 2026.xlsx"]

def base_name(f):     # "Price sheet - 2026-03.pdf" -> "price sheet"
    return re.sub(r"[\s\-–]*\d{4}-\d{2}.*$|\.\w+$", "", f).strip().lower()

checks = []
checks.append(("instructions mention the knowledge", "knowledge" in instructions.lower()))
checks.append(("says what to do when unsure", "confirm" in instructions.lower() or "not sure" in instructions.lower()))
names = [base_name(f) for f in knowledge]
dupes = sorted({n for n in names if names.count(n) > 1})
checks.append((f"one version of each file (duplicates: {', '.join(dupes) or 'none'})", not dupes))
sensitive = [f for f in knowledge if re.search(r"salar|payroll|password|aadhaar|pan card", f, re.I)]
checks.append((f"no sensitive files (found: {', '.join(sensitive) or 'none'})", not sensitive))

for label, ok in checks:
    print(("✓ " if ok else "✗ ") + label)

# ============================================================================
# Session 5.2 — Knowledge files and connectors
# ============================================================================

from datetime import date

today = date(2026, 10, 26)
files = [  # name, last updated, pages
    ("Price sheet",                   date(2026, 9, 30),   2),
    ("Price sheet (old)",             date(2025, 11, 1),   2),
    ("Clinic timings and addresses",  date(2026, 6, 15),   1),
    ("Brand voice guide",             date(2024, 2, 10),  14),
    ("Treatment FAQ",                 date(2025, 8, 20),  38),
    ("Annual report 2023 (full)",     date(2024, 4, 5),  220),
]

for name, updated, pages in files:
    age = (today - updated).days
    flags = []
    if "old" in name.lower():
        flags.append("superseded: remove")
    elif age > 365:
        flags.append(f"{age // 30} months old: review")
    if pages > 100:
        flags.append("very large: does the job need all of it?")
    print(f"{name:<30} updated {updated}  {pages:>3} pp  {'; '.join(flags) or 'ok'}")

# ============================================================================
# Session 5.3 — Writing system-level instructions
# ============================================================================

import re

def lint(text):
    issues = []
    vague = [w for w in ("helpful", "professional", "good", "nice", "appropriate", "don't make mistakes")
             if w in text.lower()]
    if vague:
        issues.append(f"vague wording with no action attached: {', '.join(vague)}")
    shouting = re.findall(r"\b[A-Z]{4,}\b", text)
    if shouting or "!!" in text:
        issues.append("capitals/exclamation marks instead of a reason")
    if not re.search(r"\b(if|when)\b.*\b(unsure|not sure|isn't|missing|not listed)\b", text, re.I):
        issues.append("no rule for missing or uncertain information")
    if not re.search(r"\b\d+\s*(words|lines|sentences)\b", text, re.I):
        issues.append("no measurable length")
    if not re.search(r"knowledge|price sheet|attached|file", text, re.I):
        issues.append("doesn't say which sources to use")
    return issues

weak = "Be helpful and professional. Don't make mistakes. NEVER give wrong prices!!! Keep it short."
strong = ("You draft replies for our front desk. Use prices only from the price sheet in the knowledge files. "
          "If a price isn't listed, write [please confirm] instead of estimating, because a wrong price causes "
          "complaints at the counter. Keep replies under 120 words: patients read them on their phones.")
for name, text in [("weak", weak), ("strong", strong)]:
    found = lint(text)
    print(f"{name}: {len(found)} issue(s)")
    for i in found:
        print(f"   - {i}")

# ============================================================================
# Session 5.4 — Maintaining configurations
# ============================================================================

import difflib

old = """Consultation: Rs 500
Scaling & polishing: Rs 1,800
Root canal (molar): Rs 9,500
Teeth whitening: Rs 12,000""".splitlines()

new = """Consultation: Rs 500
Scaling & polishing: Rs 2,000
Root canal (molar): Rs 9,500
Clear aligners (consultation): Rs 1,000""".splitlines()

for line in difflib.unified_diff(old, new, "price-sheet-2026-03", "price-sheet-2026-10", lineterm="", n=0):
    print(line)

tests = {
    "How much is scaling?":                ["2,000"],
    "Are you open on Sunday in Bandra?":   ["10", "4"],
    "Do you do teeth whitening?":          ["please confirm"],
}
answers = {   # pasted back from the Project after the October update (illustrative)
    "How much is scaling?": "Scaling and polishing is Rs 2,000 at all our clinics.",
    "Are you open on Sunday in Bandra?": "Yes, Bandra is open on Sundays from 10 am to 4 pm.",
    "Do you do teeth whitening?": "Teeth whitening is Rs 12,000.",
}
for q, must in tests.items():
    ok = all(m.lower() in answers[q].lower() for m in must)
    print(f"{'pass' if ok else 'FAIL'}  {q:<36} expects {must}")
