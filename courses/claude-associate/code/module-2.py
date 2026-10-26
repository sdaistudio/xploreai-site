# Claude Certified Associate – Foundations: study course — Module 2: Output Evaluation and Validation
# https://xploreai.co.in/courses/claude-associate/module-2/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 2.1 — Accuracy and completeness
# ============================================================================

import re

summary = """Decisions
- Launch the WhatsApp reminder pilot at the Andheri clinic first.
- Keep the current SMS reminders running during the pilot.
Actions
- Priya to draft the reminder message templates by 12 March.
- Rahul to get a quote from the WhatsApp Business provider.
- Front-desk team to collect patients' opt-in consent."""

actions = summary.split("Actions")[1].strip().splitlines()
DATE = r"\b(by|before|on)\s+\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*"
for a in actions:
    owner = re.match(r"-\s*([A-Z][\w-]*(?:\s+team)?)\s+to\b", a)
    deadline = re.search(DATE, a)
    flags = [] if deadline else ["no deadline"]
    print(f"{'ok ' if not flags else 'FIX'} {a[2:60]:<58} owner: {owner.group(1) if owner else '?':<16} {', '.join(flags)}")

# ============================================================================
# Session 2.2 — Hallucinations, inconsistencies and bias
# ============================================================================

import re
from collections import Counter

runs = [
    "The policy requires X-ray records to be kept for 10 years, and 5 years for routine notes.",
    "X-ray records must be retained for 10 years; routine clinical notes for 5 years.",
    "Keep X-ray records for 7 years and routine notes for 5 years, per section 4.2.",
]

def facts(text):
    return re.findall(r"\b\d+(?:\.\d+)?\s*(?:years?|%|days?)|section\s+\d+(?:\.\d+)*", text, re.I)

table = [facts(r) for r in runs]
for k, f in enumerate(table, 1):
    print(f"run {k}: {f}")

all_facts = Counter(x.lower() for f in table for x in set(f))
print("\nagree in every run:", [x for x, c in all_facts.items() if c == len(runs)])
print("disagree or appear once:", [x for x, c in all_facts.items() if c < len(runs)])

CODED = {
    "masculine-coded": ["aggressive", "dominant", "competitive", "rockstar", "ninja", "fearless", "assertive"],
    "age-coded":       ["young", "energetic", "digital native", "fresh graduate", "recent graduate"],
}
draft = ("We want a young, energetic front-desk rockstar who thrives in a competitive, "
         "fast-paced clinic and is fearless with difficult patients.")

for kind, words in CODED.items():
    hits = [w for w in words if w in draft.lower()]
    print(f"{kind:<16} {len(hits)} found: {', '.join(hits) or '-'}")

# ============================================================================
# Session 2.3 — Fact-checking techniques
# ============================================================================

import re

source = """Scaling & polishing (full mouth): Rs 1,800
Consultation (any clinic, any day): Rs 500
Root canal treatment (molar): Rs 9,500
X-ray (single, digital): Rs 350"""

claims = [
    "Scaling and polishing costs Rs 1,800.",
    "A molar root canal costs Rs 8,500.",
    "Consultations are free on Sundays.",
    "A digital X-ray is Rs 350.",
]

def words(s):   # lower-case words of 3+ letters, plural "s" dropped, filler removed
    return {w.rstrip("s") for w in re.findall(r"[a-z]{3,}", s.lower())} - {"cost", "the", "are", "and", "any"}
def numbers(s): return set(re.findall(r"\d[\d,]*", s))

for c in claims:
    best = max(source.splitlines(), key=lambda line: len(words(c) & words(line)))
    overlap = words(c) & words(best)
    if not overlap:
        verdict = "NO SOURCE LINE"
    elif numbers(c) and numbers(c) != numbers(best):
        verdict = f"NUMBER MISMATCH (source says {', '.join(numbers(best))})"
    elif not numbers(c) and "free" in c.lower():
        verdict = "CHECK: source gives a price, claim says free"
    else:
        verdict = "supported"
    print(f"{c:<38} -> {verdict}")

# ============================================================================
# Session 2.4 — When a human must review
# ============================================================================

def review_level(stakes, external, irreversible, expert_topic, grounded):
    """stakes: 0 low, 1 medium, 2 high. Other arguments are True/False."""
    if expert_topic and stakes >= 1:
        return "expert sign-off"
    score = stakes * 2 + external * 2 + irreversible + (not grounded)
    if score >= 4:  return "full review"
    if score >= 2:  return "spot-check"
    return "use as is"

tasks = [
    ("Brainstorm team-lunch venues",                   0, False, False, False, False),
    ("Summarise our own meeting notes for the team",   0, False, False, False, True),
    ("Draft a WhatsApp offer to all patients",         1, True,  True,  False, True),
    ("Answer a patient's question about a medicine",   2, True,  True,  True,  False),
    ("Summarise a new tax rule for the finance team",  1, False, False, True,  False),
    ("Turn our price list into a website table",       1, True,  False, False, True),
]
for name, *f in tasks:
    print(f"{name:<48} -> {review_level(*f)}")

# ============================================================================
# Session 2.5 — Editing for the audience
# ============================================================================

import re

def syllables(word):
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups) - (1 if word.endswith("e") and len(groups) > 1 else 0)
    return max(n, 1)

def flesch(text):
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    words = re.findall(r"[A-Za-z']+", text)
    syl = sum(syllables(w) for w in words)
    return 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syl / len(words)), len(words) / sentences

technical = ("The implementation integrates the scheduling application programming interface with the "
             "WhatsApp Business platform, enabling automated appointment confirmation and configurable "
             "reminder notifications.")
patient = ("You can now book on WhatsApp. Send Hi, pick a time, and you are done. "
           "We will remind you the day before.")

for name, text in [("technical", technical), ("patient", patient)]:
    score, wps = flesch(text)
    print(f"{name:<10} reading ease {score:6.1f}   words per sentence {wps:4.1f}")

# ============================================================================
# Session 2.6 — Choosing the output format
# ============================================================================

import json, re

reply = '''[
  {"name": "Anita Desai", "treatment": "cleaning", "preferred_date": "2026-03-14", "urgent": false},
  {"name": null, "treatment": "root canal", "preferred_date": "next week", "urgent": true}
]'''

ALLOWED = {"cleaning", "filling", "root canal", "braces", "other"}
records = json.loads(reply)                       # step 1: is it valid JSON at all?
for k, r in enumerate(records, 1):
    problems = []
    if set(r) != {"name", "treatment", "preferred_date", "urgent"}:
        problems.append(f"unexpected keys {sorted(r)}")
    if r.get("treatment") not in ALLOWED:
        problems.append(f"treatment '{r.get('treatment')}' not allowed")
    d = r.get("preferred_date")
    if d is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        problems.append(f"date '{d}' is not YYYY-MM-DD")
    if not isinstance(r.get("urgent"), bool):
        problems.append("urgent is not true/false")
    print(f"record {k}: " + ("ok" if not problems else "; ".join(problems)))
