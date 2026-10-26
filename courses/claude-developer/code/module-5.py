# Claude Certified Developer – Foundations: study course — Module 5: Model Selection and Optimization
# https://xploreai.co.in/courses/claude-developer/module-5/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 5.1 — How an LLM generates text
# ============================================================================

VOCAB = {"the", "cat", "sat", "un", "believ", "able", "appoint", "ment", "s", "clinic", " ", ".", "!",
         "re", "schedul", "ing", "tele", "consult", "a", "b", "c", "d", "e", "i", "l", "n", "o", "t", "u", "v"}

def tokenize(text):
    out, i, text = [], 0, text.lower()
    while i < len(text):
        for j in range(len(text), i, -1):          # longest piece in the vocabulary first
            if text[i:j] in VOCAB:
                out.append(text[i:j]); i = j; break
        else:
            out.append(text[i]); i += 1           # unknown character: its own token
    return [t for t in out if t != " "]

for s in ["The cat sat.", "Unbelievable!", "Rescheduling teleconsult appointments"]:
    toks = tokenize(s)
    print(f"{s:<40} {len(toks)} tokens  {toks}")

WINDOW = 1_000_000
parts = {"system prompt": 3_500, "tool definitions": 4_200, "conversation history": 61_000,
         "retrieved documents": 140_000, "tool results": 38_000}
used = sum(parts.values())
max_tokens = 32_000
for k, v in parts.items():
    print(f"{k:<22} {v:>9,}")
print(f"{'input total':<22} {used:>9,}  ({used / WINDOW:.1%} of the window)")
print(f"{'reserved for reply':<22} {max_tokens:>9,}")
print(f"{'headroom':<22} {WINDOW - used - max_tokens:>9,}")

import math, random

logits = {"daily": 3.1, "often": 2.4, "speaking": 2.0, "with": 1.6, "online": 0.9, "backwards": -1.5}

def probs(logits, temperature):
    exps = {t: math.exp(v / temperature) for t, v in logits.items()}
    z = sum(exps.values())
    return {t: e / z for t, e in exps.items()}

def nucleus(p, top_p):
    kept, total = [], 0.0
    for t, v in sorted(p.items(), key=lambda kv: -kv[1]):
        kept.append(t); total += v
        if total >= top_p: break
    return kept

for T in (0.3, 1.0, 1.8):
    p = probs(logits, T)
    print(f"temperature {T}: " + "  ".join(f"{t} {v:.0%}" for t, v in p.items()))
print("\ntop-p 0.9 at temperature 1.0 keeps:", nucleus(probs(logits, 1.0), 0.9))

rng = random.Random(11)
p = probs(logits, 1.0)
draws = [rng.choices(list(p), weights=list(p.values()))[0] for _ in range(8)]
print("8 samples at temperature 1.0:      ", draws)

# ============================================================================
# Session 5.2 — Thinking, effort and fast mode
# ============================================================================

# response = client.messages.create(
#     model="claude-sonnet-5-5",
#     max_tokens=16000,
#     output_config={"effort": "low"},        # low | medium | high | xhigh | max
#     messages=[{"role": "user", "content": "Classify this message: billing, booking or clinical?\n\n" + text}],
# )

def pick_options(route):
    hard, waiting, volume = route["hard"], route["user_waiting"], route["per_day"]
    if hard and waiting and route.get("latency_critical"):
        return "Opus 5.5, effort high, fast mode (premium price: check it pays)"
    if hard:
        return "Opus 5.5, effort high or xhigh, adaptive thinking"
    if volume > 10_000 and not waiting:
        return "Haiku 5.5, effort low, via the Batches API"
    if volume > 10_000:
        return "Haiku 5.5, effort low"
    return "Sonnet 5.5, effort medium"

routes = [
    ("FAQ chat replies",                dict(hard=False, user_waiting=True,  per_day=40_000)),
    ("Overnight tagging of reviews",    dict(hard=False, user_waiting=False, per_day=200_000)),
    ("Contract risk analysis",          dict(hard=True,  user_waiting=False, per_day=60)),
    ("Agentic bug fixing in CI",        dict(hard=True,  user_waiting=False, per_day=30)),
    ("Live triage for on-call doctors", dict(hard=True,  user_waiting=True,  per_day=300, latency_critical=True)),
    ("Weekly report drafting",          dict(hard=False, user_waiting=True,  per_day=25)),
]
for name, r in routes:
    print(f"{name:<33} → {pick_options(r)}")

out_tokens, in_tokens = 3_000, 20_000
baseline_tps = 60                       # PLACEHOLDER output tokens/second; measure your own
for label, p_in, p_out, speedup in [("standard", 4, 20, 1.0), ("fast mode", 8, 40, 2.5)]:
    cost = (in_tokens * p_in + out_tokens * p_out) / 1e6
    secs = out_tokens / (baseline_tps * speedup)
    speed = "baseline" if speedup == 1 else f"up to {speedup}× faster"
    print(f"Opus 5.5 {label:<10} ${cost:.3f} per reply   ~{secs:.0f}s to generate ({speed})")

# response = client.beta.messages.create(
#     model="claude-opus-5-5", max_tokens=8000,
#     speed="fast", betas=["fast-mode-2026-02-01"],
#     messages=[{"role": "user", "content": triage_case}],
# )
# print(response.usage.speed)        # confirms which speed was used

# ============================================================================
# Session 5.3 — Zero-, one- and few-shot
# ============================================================================

from collections import Counter

def lint_examples(examples, labels):
    issues = []
    counts = Counter(lbl for _, lbl in examples)
    missing = [l for l in labels if l not in counts]
    if missing: issues.append(f"no example for {missing}")
    if counts and max(counts.values()) > len(examples) / 2:
        issues.append(f"skewed towards {counts.most_common(1)[0][0]} ({counts.most_common(1)[0][1]}/{len(examples)})")
    lengths = [len(m.split()) for m, _ in examples]
    if max(lengths) - min(lengths) < 3:
        issues.append("all examples are the same length: Claude may copy it")
    if len({m.lower() for m, _ in examples}) < len(examples):
        issues.append("duplicate examples")
    return issues or ["looks balanced"]

LABELS = ["BOOKING", "BILLING", "CLINICAL", "OTHER"]
set_a = [("Book me for Monday", "BOOKING"), ("Move my Friday slot", "BOOKING"),
         ("Cancel my booking", "BOOKING"), ("Why was I charged twice?", "BILLING")]
set_b = [("Why was I charged twice?", "BILLING"), ("The rash is spreading since yesterday", "CLINICAL"),
         ("Is there parking near the Andheri clinic?", "OTHER"),
         ("Book me with Dr Rao next week, and is the follow-up free?", "BOOKING")]

def to_prompt(examples):
    return "<examples>\n" + "\n".join(f"<example><message>{m}</message><label>{l}</label></example>"
                                      for m, l in examples) + "\n</examples>"

print("set A:", lint_examples(set_a, LABELS))
print("set B:", lint_examples(set_b, LABELS))
print("\n" + to_prompt(set_b))

# ============================================================================
# Session 5.4 — SDKs, REST and websockets
# ============================================================================

import json

RAW = """event: message_start
data: {"type": "message_start", "message": {"id": "msg_ex", "usage": {"input_tokens": 25}}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

event: ping
data: {"type": "ping"}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": ", Mrs Iyer."}}

event: message_delta
data: {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 7}}

event: message_stop
data: {"type": "message_stop"}
"""

def parse_sse(raw):
    for block in raw.strip().split("\n\n"):              # events are separated by a blank line
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        yield fields["event"], json.loads(fields["data"])

text = ""
for name, data in parse_sse(RAW):
    if name == "content_block_delta":
        text += data["delta"]["text"]
    elif name == "message_delta":
        print("stop_reason:", data["delta"]["stop_reason"], "| output tokens:", data["usage"]["output_tokens"])
    elif name == "ping":
        print("(keep-alive ping ignored)")
print("assembled text:", text)

# ============================================================================
# Session 5.5 — Opus, Sonnet or Haiku
# ============================================================================

P = {"Haiku 5.5": (0.10, 0.50), "Sonnet 5.5": (2.00, 10.00), "Opus 5.5": (4.00, 20.00)}

def monthly(model, calls_per_day, tin, tout):
    pin, pout = P[model]
    return calls_per_day * 30 * (tin * pin + tout * pout) / 1e6

workloads = [("classify 50k messages/day", 50_000, 600, 5),
             ("support replies 5k/day", 5_000, 4_000, 300),
             ("code review 200 PRs/day", 200, 30_000, 2_000)]
print(f"{'':<28}" + "".join(f"{m:>13}" for m in P))
for name, n, tin, tout in workloads:
    print(f"{name:<28}" + "".join(f"{'$' + format(monthly(m, n, tin, tout), ',.0f'):>13}" for m in P))

RULES = [  # (applies to target models, test on the request, message)
    ({"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1"},
     lambda r: r.get("tool_choice", {}).get("type") in ("any", "tool"), "forced tool_choice → use auto + strict tools"),
    ({"claude-opus-5-5"}, lambda r: r.get("thinking", {}).get("type") == "disabled", "thinking can't be disabled → lower effort instead"),
    ({"*"}, lambda r: "budget_tokens" in r.get("thinking", {}), "budget_tokens → adaptive thinking + effort"),
    ({"*"}, lambda r: any(k in r for k in ("temperature", "top_p", "top_k")), "sampling parameters → remove them"),
    ({"*"}, lambda r: r["messages"][-1]["role"] == "assistant", "assistant prefill → structured outputs or instructions"),
    ({"claude-opus-5-5", "claude-haiku-5-5"}, lambda r: "effort" not in r.get("output_config", {}), "effort defaults to medium here → set it explicitly"),
]

def check_migration(request, target):
    return [msg for models, test, msg in RULES if ("*" in models or target in models) and test(request)] or ["no known breaking changes"]

legacy = {"model": "claude-sonnet-4-6", "temperature": 0.2, "tool_choice": {"type": "tool", "name": "extract"},
          "thinking": {"type": "enabled", "budget_tokens": 4000},
          "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "{"}]}
for target in ("claude-sonnet-5-5", "claude-opus-5-5"):
    print(f"{legacy['model']} → {target}:")
    for issue in check_migration(legacy, target): print("   -", issue)

# ============================================================================
# Session 5.6 — Token budgets and cost models
# ============================================================================

PRICES = {"claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-sonnet-5-5": (2.00, 10.00, 0.20)}  # in, out, cache read

LOG = [  # route, model, task_id, input, cache_write, cache_read, output
    ("faq",    "claude-haiku-5-5",  "t1", 900,  0,      14_000, 120),
    ("faq",    "claude-haiku-5-5",  "t2", 850,  0,      14_000, 140),
    ("faq",    "claude-haiku-5-5",  "t3", 950,  14_000, 0,      110),
    ("triage", "claude-sonnet-5-5", "t4", 2_100, 0,     22_000, 400),
    ("triage", "claude-sonnet-5-5", "t4", 2_600, 0,     22_000, 380),   # same task, 2nd turn
    ("triage", "claude-sonnet-5-5", "t5", 2_300, 22_000, 0,     420),
    ("report", "claude-sonnet-5-5", "t6", 48_000, 0,    0,      3_900),
    ("report", "claude-sonnet-5-5", "t6", 52_000, 0,    0,      3_600),   # retry after a bad draft
]

def cost(model, inp, cw, cr, out):
    pin, pout, pread = PRICES[model]
    return (inp * pin + cw * pin * 1.25 + cr * pread + out * pout) / 1e6

by_route, tasks = {}, {}
for route, model, task, inp, cw, cr, out in LOG:
    c = cost(model, inp, cw, cr, out)
    r = by_route.setdefault(route, {"usd": 0, "calls": 0, "read": 0, "uncached": 0})
    r["usd"] += c; r["calls"] += 1; r["read"] += cr; r["uncached"] += inp + cw
    tasks.setdefault((route, task), 0); tasks[(route, task)] += c

for route, r in by_route.items():
    n_tasks = len([t for t in tasks if t[0] == route])
    hit = r["read"] / (r["read"] + r["uncached"])
    print(f"{route:<7} ${r['usd']:.4f}  {r['calls']} calls, {n_tasks} tasks  "
          f"→ ${r['usd'] / n_tasks:.4f} per task   cache-read share {hit:.0%}")
total = sum(r["usd"] for r in by_route.values())
print(f"\nreport route is {by_route['report']['usd'] / total:.0%} of today's spend with no caching at all")
