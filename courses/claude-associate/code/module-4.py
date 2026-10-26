# Claude Certified Associate – Foundations: study course — Module 4: Workflow Integration and Solution Design
# https://xploreai.co.in/courses/claude-associate/module-4/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 4.1 — Analysing requirements and use cases
# ============================================================================

use_cases = [
    # name,                         times/week, minutes each, checkable output?, sensitive data?, needs live system access?
    ("Draft replies to booking queries",  120,  4, True,  False, False),
    ("Weekly operations report",            1, 180, True,  False, False),
    ("Summarise patient feedback monthly",  0.25, 300, True, False, False),
    ("Answer clinical questions",          40,  6, False, True,  False),
    ("Auto-update the booking system",    150,  2, True,  False, True),
]

rows = []
for name, per_week, minutes, checkable, sensitive, live in use_cases:
    hours_month = per_week * minutes * 4.3 / 60
    fit = 3 + (1 if checkable else -2) - (2 if sensitive else 0) - (2 if live else 0)
    rows.append((hours_month * max(fit, 0), name, hours_month, fit, live))

for score, name, hours, fit, live in sorted(rows, reverse=True):
    note = " (needs integration: escalate to a developer)" if live else ""
    print(f"{name:<36} {hours:5.1f} h/month  fit {fit:+d}  priority {score:6.1f}{note}")

# ============================================================================
# Session 4.2 — Research, planning and process optimisation
# ============================================================================

current = [  # step, minutes of work, minutes the patient waits after it
    ("Read WhatsApp enquiry",        2,   0),
    ("Check dentist availability",   5,  30),
    ("Write reply with slots",       6, 120),
    ("Patient picks slot",           0, 180),
    ("Confirm and send forms",       8,  60),
]
redesigned = [
    ("Read WhatsApp enquiry",        2,   0),
    ("Check dentist availability",   5,   0),
    ("Claude drafts reply; staff review", 2, 10),
    ("Patient picks slot",           0, 180),
    ("Claude drafts confirmation; staff review", 2, 10),
]

def summarise(name, steps):
    work = sum(w for _, w, _ in steps)
    wait = sum(t for _, _, t in steps)
    worst = max(steps, key=lambda s: s[2])
    print(f"{name:<11} work {work:3d} min | waiting {wait:4d} min | total {(work + wait) / 60:4.1f} h | longest wait: '{worst[0]}' ({worst[2]} min)")

summarise("current", current)
summarise("redesigned", redesigned)

# ============================================================================
# Session 4.3 — Supporting solution design
# ============================================================================

requirements = {
    "R1": "Reminder sent the day before",
    "R2": "Patient can reschedule from the message",
    "R3": "Messages in English, Hindi or Marathi",
    "R4": "No clinical details in the message",
    "R5": "Staff can see who confirmed",
}
design = {   # part of the Claude-assisted batch design -> requirements it meets
    "Evening batch in the 'Reminders' Project": ["R1"],
    "Template with booking link":              ["R1", "R2"],
    "Project instruction: language from booking record": ["R3"],
    "Project instruction: only date, time, clinic, link": ["R4"],
}

covered = {r for parts in design.values() for r in parts}
for rid, text in requirements.items():
    by = [part for part, rs in design.items() if rid in rs]
    print(f"{rid} {text:<40} {'covered by: ' + '; '.join(by) if by else 'NOT COVERED'}")

# ============================================================================
# Session 4.4 — Augmenting or redesigning a workflow
# ============================================================================

weeks = 12
baseline   = 3.0                     # hours a week, writing the report by hand
augment    = {"setup": 1.0, "weekly": 1.6}    # Claude drafts; ops lead edits
redesign   = {"setup": 8.0, "weekly": 0.6}    # forms + Project + training; review only

def cumulative(plan):
    return [plan["setup"] + plan["weekly"] * w for w in range(1, weeks + 1)]

aug, red, base = cumulative(augment), cumulative(redesign), [baseline * w for w in range(1, weeks + 1)]
for w in (1, 2, 4, 6, 8, 12):
    print(f"week {w:>2}: by hand {base[w-1]:5.1f} h | augment {aug[w-1]:5.1f} h | redesign {red[w-1]:5.1f} h")
breakeven = next(w for w in range(1, weeks + 1) if red[w-1] <= aug[w-1])
print(f"\nredesign overtakes augment in week {breakeven}; saved vs by-hand after {weeks} weeks: "
      f"augment {base[-1] - aug[-1]:.1f} h, redesign {base[-1] - red[-1]:.1f} h")

# ============================================================================
# Session 4.5 — Communicating value and limits
# ============================================================================

hourly_cost = 450            # ₹ per staff hour, fully loaded (illustrative)
seats, seat_cost = 3, 2_500  # ₹ per seat per month (illustrative assumption, not a quoted price)
scenarios = {                # hours saved per week, hours of review added per week
    "cautious": (4, 2.0),
    "expected": (8, 2.5),
    "optimistic": (12, 3.0),
}
for name, (saved, review) in scenarios.items():
    net_hours = (saved - review) * 4.3
    value = net_hours * hourly_cost - seats * seat_cost
    print(f"{name:<11} net {net_hours:5.1f} h/month -> net value ₹{value:8,.0f} a month")
