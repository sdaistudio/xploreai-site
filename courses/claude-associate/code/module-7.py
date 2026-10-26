# Claude Certified Associate – Foundations: study course — Module 7: Troubleshooting and Optimization
# https://xploreai.co.in/courses/claude-associate/module-7/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 7.1 — Diagnosing poor outputs
# ============================================================================

from collections import Counter

log = [  # one entry per output a reviewer flagged this week (cause chosen from the table above)
    "missing context", "wrong format", "outdated info", "missing context", "invented fact",
    "missing context", "wrong format", "outdated info", "outdated info", "missing context",
    "too big a task", "outdated info", "missing context", "wrong format", "ignored project rule",
    "missing context", "outdated info", "wrong format", "missing context", "invented fact",
]
counts = Counter(log).most_common()
total, running = len(log), 0
for cause, n in counts:
    running += n
    print(f"{cause:<22} {n:>2} {'█' * n:<9} cumulative {running / total:5.0%}")

# ============================================================================
# Session 7.2 — Adjusting from feedback
# ============================================================================

import difflib

pairs = {  # template: (Claude's draft, what staff actually sent)
    "booking confirmation": ("Your appointment at our Bandra clinic is confirmed for Tue 14 Mar at 11 am. Reply C to cancel.",
                             "Your appointment at our Bandra clinic is confirmed for Tue 14 Mar at 11 am. Reply C to cancel."),
    "reminder":             ("Reminder: your dental appointment is tomorrow at 4 pm at our Andheri clinic.",
                             "Reminder: your dental appointment is tomorrow at 4 pm at our Andheri clinic. Please bring your X-rays."),
    "post-treatment care":  ("Thank you for visiting us today. We hope your experience was pleasant and look forward to seeing you again.",
                             "After your filling today: avoid hot drinks for 2 hours and chew on the other side until tomorrow. Call us if pain lasts beyond 3 days."),
}
for name, (draft, final) in pairs.items():
    ratio = difflib.SequenceMatcher(None, draft, final).ratio()
    verdict = "fine" if ratio > 0.9 else "minor edits: consider a small prompt tweak" if ratio > 0.6 else "rewritten: fix the template's prompt"
    print(f"{name:<22} similarity {ratio:.2f} -> {verdict}")

# ============================================================================
# Session 7.3 — Optimising workflows
# ============================================================================

before = [  # step, minutes
    ("Export feedback from forms; copy into a chat",           25),
    ("Re-explain context and report format",                    15),
    ("Prompt, read, re-prompt (about 4 rounds)",                60),
    ("Reformat themes into the report template by hand",        45),
    ("Fact-check every number against the export",              40),
    ("Owner review and edits",                                  30),
]
after = [
    ("Feedback sheet pulled from Drive via the connector",      5),
    ("'Feedback report' Project: instructions + template",      0),
    ("One prompt from the saved template (1–2 rounds)",         15),
    ("Themes returned as a table, pasted into the template",    10),
    ("Spot-check: verify the top 5 figures against the sheet",  15),
    ("Owner review and edits",                                  20),
]
for name, steps in [("before", before), ("after", after)]:
    total = sum(m for _, m in steps)
    print(f"{name:<7} {total:4d} min/month ({total / 60:.1f} h)   steps: {len(steps)}")
saved = sum(m for _, m in before) - sum(m for _, m in after)
print(f"\nsaved {saved} min a month ({saved / sum(m for _, m in before):.0%}); "
      f"biggest single gain: prompting rounds {60 - 15} min")
