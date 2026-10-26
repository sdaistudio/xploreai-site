# Claude Certified Associate – Foundations: study course — Module 3: Product and Model Selection
# https://xploreai.co.in/courses/claude-associate/module-3/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 3.1 — Choosing the right Claude feature
# ============================================================================

def pick_feature(task):
    t = task.lower()
    if any(w in t for w in ("compare", "landscape", "in-depth", "across sources", "competitor")):
        return "Research"
    if any(w in t for w in ("current", "latest", "today", "this week", "price of")):
        return "Web search"
    if any(w in t for w in ("every month", "each week", "recurring", "our style guide", "same documents")):
        return "Project"
    if any(w in t for w in ("dashboard", "calculator", "one-pager", "document to share", "slide")):
        return "Artifact"
    return "Chat"

for task in ["Compare five WhatsApp Business providers on price, features and support",
             "What is today's repo rate?",
             "Draft the patient newsletter every month using our style guide",
             "Build a calculator for treatment EMI options",
             "Explain what 'opt-in consent' means",
             "Write a one-pager to share with the owners on Sunday hours"]:
    print(f"{task:<66} -> {pick_feature(task)}")

# ============================================================================
# Session 3.2 — Haiku, Sonnet and Opus
# ============================================================================

PRICE = {                     # USD per million tokens: (input, output), Anthropic's published rates, Oct 2026
    "Haiku 5.5":  (0.10, 0.50),
    "Sonnet 5.5": (2.00, 10.00),
    "Opus 5.5":   (4.00, 20.00),
    "Fable 5.1":  (10.00, 50.00),
}
TOKENS_PER_WORD = 1.8         # from Anthropic: 1M tokens is roughly 555k words
USD_TO_INR = 84               # illustrative exchange rate

replies   = 20_000            # per month
in_words  = 250               # instructions + the customer's message
out_words = 90                # the drafted reply

in_tok  = replies * in_words  * TOKENS_PER_WORD
out_tok = replies * out_words * TOKENS_PER_WORD
print(f"{in_tok/1e6:.1f}M input tokens and {out_tok/1e6:.1f}M output tokens a month\n")
for model, (pin, pout) in PRICE.items():
    usd = in_tok / 1e6 * pin + out_tok / 1e6 * pout
    print(f"{model:<11} ${usd:8.2f} a month   (about ₹{usd * USD_TO_INR:9,.0f})")

# ============================================================================
# Session 3.3 — Matching the model to the task
# ============================================================================

MODELS = {               # quality, speed, cost (5 = best value). Rough relative ratings, not benchmarks.
    "Haiku":  (3, 5, 5),
    "Sonnet": (4.5, 4, 3),
    "Opus":   (5, 3, 2),
}

def best_model(task, w_quality, w_speed, w_cost):
    scores = {m: w_quality * q + w_speed * s + w_cost * c for m, (q, s, c) in MODELS.items()}
    pick = max(scores, key=scores.get)
    print(f"{task:<44} " + "  ".join(f"{m} {v:4.1f}" for m, v in scores.items()) + f"  -> {pick}")

best_model("Tag 5,000 tickets by topic",               w_quality=0.2, w_speed=0.4, w_cost=0.4)
best_model("Weekly ops report from meeting notes",     w_quality=0.5, w_speed=0.3, w_cost=0.2)
best_model("Find risks in a 60-page supplier contract", w_quality=0.8, w_speed=0.1, w_cost=0.1)

# ============================================================================
# Session 3.4 — Context limits and memory
# ============================================================================

WINDOW = 1_000_000            # tokens, current Claude models
TOKENS_PER_WORD = 1.8

session = [                   # (what was added, words)
    ("project instructions", 400),
    ("brand guide + price sheet (project knowledge)", 9_000),
    ("annual report attached", 60_000),
    ("first draft and discussion", 4_500),
    ("three rounds of revisions", 7_000),
    ("second annual report attached", 85_000),
    ("rewrite for a new audience", 5_000),
    ("board pack attached", 150_000),
]

used = 0
for what, words in session:
    used += words * TOKENS_PER_WORD
    share = used / WINDOW
    advice = "handoff summary, then a fresh chat" if share > 0.25 else "fine"
    print(f"{what:<46} total {used/1000:7.1f}k tokens  {share:5.1%}  {advice}")
