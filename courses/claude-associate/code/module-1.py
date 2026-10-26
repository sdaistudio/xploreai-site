# Claude Certified Associate – Foundations: study course — Module 1: Prompting and Task Execution
# https://xploreai.co.in/courses/claude-associate/module-1/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 1.1 — Anatomy of an effective prompt
# ============================================================================

def build_prompt(role, task, context="", output_format="", constraints=(), example=""):
    """Assemble a structured prompt. Empty parts are simply left out."""
    parts = [role, "", f"<task>\n{task}\n</task>"]
    if context:
        parts.append(f"<context>\n{context}\n</context>")
    if output_format:
        parts.append(f"<format>\n{output_format}\n</format>")
    if constraints:
        rules = "\n".join(f"- {c}" for c in constraints)
        parts.append(f"<constraints>\n{rules}\n</constraints>")
    if example:
        parts.append(f"<example>\n{example}\n</example>")
    return "\n".join(parts)

prompt = build_prompt(
    role="You are the operations lead for a chain of three dental clinics in Mumbai.",
    task="Write a WhatsApp message to our patients announcing Sunday hours at the Bandra clinic.",
    context="Sunday hours are 10 am to 4 pm from 1 March, as a one-month trial.",
    output_format="Under 80 words. Booking link on its own final line.",
    constraints=["Don't say the hours are permanent.", "No exclamation marks."],
)
print(prompt)
print(f"\n({len(prompt.split())} words)")

import re

CHECKS = {
    "role":        r"\byou are\b|\bact as\b|\bas (?:an?|the) \w+",
    "task":        r"\b(write|draft|summari[sz]e|analy[sz]e|list|create|compare|explain|review|plan)\b",
    "audience":    r"\b(for|to) (?:our |the )?(patients|customers|team|board|managers?|clients?|staff|students)\b|\baudience\b",
    "format":      r"\b(words?|bullets?|table|paragraphs?|email|whatsapp|json|slides?|headings?|format)\b",
    "constraints": r"\b(don't|do not|never|avoid|only|must|without)\b",
    "example":     r"<example>|for example|e\.g\.",
}

def check(prompt):
    found = {k: bool(re.search(p, prompt, re.I)) for k, p in CHECKS.items()}
    missing = [k for k, ok in found.items() if not ok]
    return sum(found.values()), missing

vague = "Write something about our Sunday opening."
for name, text in [("vague", vague), ("structured", prompt)]:
    score, missing = check(text)
    print(f"{name:<11} covers {score}/6 parts | missing: {', '.join(missing) or 'nothing'}")

# ============================================================================
# Session 1.2 — Decomposing complex tasks
# ============================================================================

plan = [
    ("Extract",    ["feedback export"],     "complaint list"),
    ("Categorise", ["complaint list"],      "themes"),
    ("Prioritise", ["themes"],              "ranked themes"),
    ("Propose",    ["ranked themes"],       "fixes"),
    ("Summarise",  ["ranked themes", "fixes", "owner priorities"], "owner brief"),
]

available = {"feedback export"}          # what we have before step 1
for k, (step, needs, makes) in enumerate(plan, start=1):
    missing = [n for n in needs if n not in available]
    status = "ok" if not missing else f"MISSING {', '.join(missing)}"
    print(f"step {k} {step:<11} needs {', '.join(needs):<40} -> {makes:<14} {status}")
    available.add(makes)

# ============================================================================
# Session 1.3 — Iterating to a better output
# ============================================================================

outputs = {
    "v1 (no format)": "The customer, who visited on Tuesday, says she was charged twice for a "
                      "cleaning and is quite upset about it and would like the money back soon.",
    "v2 (format only)": "Issue: Charged twice for cleaning\nCustomer wants: Refund\n"
                                        "Urgency: Medium",
    "v3 (format + example)": "Issue: Charged twice for one cleaning appointment\n"
                             "Customer wants: Refund of the duplicate charge\n"
                             "Urgency: Medium (no health impact, money owed)",
}

def criteria(text):
    lines = text.splitlines()
    wants = next((l for l in lines if l.startswith("Customer wants:")), "")
    return {
        "has 3 labelled lines": [l.split(":")[0] for l in lines] == ["Issue", "Customer wants", "Urgency"],
        "each line < 15 words": all(len(l.split()) < 15 for l in lines),
        "urgency has a reason": "(" in text.split("Urgency:")[-1] if "Urgency:" in text else False,
        "refund is specific":   any(w in wants for w in ("duplicate", "twice")),
    }

for name, text in outputs.items():
    c = criteria(text)
    passed = sum(c.values())
    print(f"{name:<34} {passed}/4  " + "  ".join(("✓ " if ok else "✗ ") + k for k, ok in c.items()))

# ============================================================================
# Session 1.4 — Prompting by task type
# ============================================================================

STRATEGY = {
    "analysis":      ("analy|why did|trend|compare|which .* (?:highest|lowest)|data",
                      "attach the data; ask for step-by-step reasoning and stated assumptions"),
    "research":      ("research|latest|current|regulation|rules|what are the|find out",
                      "use Research or web search; ask for sources; verify key claims"),
    "drafting":      ("write|draft|email|message|letter|post|announce",
                      "give audience, purpose, tone, length and a sample of your style"),
    "brainstorming": ("ideas|brainstorm|ways to|options|suggest",
                      "ask for many varied options, add constraints, then narrow down"),
}
import re

def strategy(request):
    for kind, (pattern, advice) in STRATEGY.items():
        if re.search(pattern, request, re.I):
            return kind, advice
    return "unclear", "say what kind of output you want before anything else"

for req in ["Why did no-shows rise at Bandra in October?",
            "What are the current rules on WhatsApp reminders?",
            "Draft an email to patients about new Sunday hours",
            "Give me ideas to fill empty afternoon slots",
            "Help me with the clinic"]:
    kind, advice = strategy(req)
    print(f"{req:<52} -> {kind:<13} {advice}")
