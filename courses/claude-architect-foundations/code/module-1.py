# Claude Certified Architect – Foundations: study course — Module 1: Agentic Architecture & Orchestration
# https://xploreai.co.in/courses/claude-architect-foundations/module-1/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 1.1 — Agentic loops
# ============================================================================

SCRIPT = [
    {"stop_reason": "tool_use", "content": [{"type": "text", "text": "Let me look up the customer first."},
                                             {"type": "tool_use", "id": "t1", "name": "get_customer", "input": {"email": "meera@example.com"}}]},
    {"stop_reason": "tool_use", "content": [{"type": "text", "text": "Customer lookup done. Now the order."},
                                             {"type": "tool_use", "id": "t2", "name": "lookup_order", "input": {"order_id": "ORD-1182"}}]},
    {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "t3", "name": "check_return_window", "input": {"order_id": "ORD-1182"}}]},
    {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "t4", "name": "process_refund", "input": {"order_id": "ORD-1182", "amount": 42.0}}]},
    {"stop_reason": "end_turn", "content": [{"type": "text", "text": "Refund of $42.00 issued for ORD-1182."}]},
]

def run(stop_rule, max_iter=10):
    history, turns = [{"role": "user", "content": "My blender arrived broken, refund please."}], 0
    for turn in range(max_iter):
        reply = SCRIPT[turn]; turns += 1
        history.append({"role": "assistant", "content": reply["content"]})
        if stop_rule(reply, turn):
            break
        results = [{"type": "tool_result", "tool_use_id": b["id"], "content": "ok"} for b in reply["content"] if b["type"] == "tool_use"]
        history.append({"role": "user", "content": results})
    called = [b["name"] for m in history if m["role"] == "assistant" for b in m["content"] if b["type"] == "tool_use"]
    executed = called if stop_rule(SCRIPT[turns - 1], turns - 1) is False or SCRIPT[turns - 1]["stop_reason"] == "end_turn" else called[:-1]
    return turns, executed

RULES = {
    "stop_reason == end_turn (correct)": lambda r, t: r["stop_reason"] == "end_turn",
    "stop when the reply contains text": lambda r, t: any(b["type"] == "text" for b in r["content"]),
    "stop when text says 'done'":        lambda r, t: any("done" in b.get("text", "").lower() for b in r["content"]),
    "stop after 3 iterations (cap)":     lambda r, t: t + 1 >= 3,
}
for name, rule in RULES.items():
    turns, executed = run(rule)
    print(f"{name:<36} stopped after {turns} turn(s); tools run: {executed}")

# ============================================================================
# Session 1.2 — Coordinator–subagent orchestration
# ============================================================================

TOPIC_AREAS = {"AI in creative industries": ["visual arts", "music", "writing", "film", "games"]}

def plan(query, complexity):
    if complexity == "simple":
        return {"search": [query]}                         # one subagent, no full pipeline
    areas = TOPIC_AREAS[query]
    return {"search": areas[:3], "analysis": areas[3:]}    # distinct partitions, no overlap

def run_subagents(assignments, unavailable=()):
    found = {}
    for agent, subtopics in assignments.items():
        for s in subtopics:
            found[s] = None if s in unavailable else f"{agent}: 3 sourced findings on {s}"
    return found

def coordinate(query, complexity="complex", max_rounds=3):
    required = TOPIC_AREAS.get(query, [query])
    assignments = plan(query, complexity)
    findings = run_subagents(assignments, unavailable={"games"})        # first pass: games source down
    for rnd in range(1, max_rounds + 1):
        gaps = [s for s in required if not findings.get(s)]
        print(f"round {rnd}: covered {len(required) - len(gaps)}/{len(required)}  gaps={gaps}")
        if not gaps:
            break
        findings.update(run_subagents({"search": gaps}))       # re-delegate only the gaps
    return findings

print("assignments:", plan("AI in creative industries", "complex"))
print("simple query:", plan("When did the EU AI Act enter into force?", "simple"))
result = coordinate("AI in creative industries")

# ============================================================================
# Session 1.3 — Subagent invocation and context passing
# ============================================================================

# from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

# options = ClaudeAgentOptions(
#     allowed_tools=["Task", "Read"],                 # the guide: "Task" must be allowed for delegation
#     agents={
#         "web-search": AgentDefinition(
#             description="Searches the web for one assigned subtopic and returns sourced findings.",
#             prompt="Return JSON findings: claim, excerpt, source_url, published_date. No prose.",
#             tools=["WebSearch", "WebFetch"]),
#         "synthesis": AgentDefinition(
#             description="Combines findings into a cited report. Use only after findings exist.",
#             prompt="Preserve every claim's source. Mark conflicts; don't resolve them silently.",
#             tools=["Read"]),
#     },
# )

findings = [
    {"claim": "Generative tools cut storyboard time by ~40%", "source": "https://studio-survey.example/2026", "page": None, "date": "2026-03"},
    {"claim": "Session musicians report 18% fewer bookings", "source": "Musicians' Union report.pdf", "page": 12, "date": "2026-06"},
    {"claim": "Session musicians report 11% fewer bookings", "source": "https://labour-stats.example/q2", "page": None, "date": "2025-12"},
]

prose_handoff = "Findings: storyboards are faster with AI; session musicians are getting fewer bookings."

def structured_handoff(items):
    lines = ["<findings>"]
    for i, f in enumerate(items, 1):
        where = f"{f['source']}" + (f", p.{f['page']}" if f["page"] else "")
        lines.append(f'  <finding id="{i}" date="{f["date"]}" source="{where}">{f["claim"]}</finding>')
    lines.append("</findings>")
    return "\n".join(lines)

synthesis_prompt = ("Goal: a cited brief on AI's impact on creative work for a union audience.\n"
                    "Quality bar: every claim keeps its source; if sources disagree, show both with dates.\n\n"
                    + structured_handoff(findings))
print(synthesis_prompt)
print("\nsources available to synthesis — structured:", len({f['source'] for f in findings}), "| prose:", 0)

# ============================================================================
# Session 1.4 — Enforcement and handoff
# ============================================================================

class PrerequisiteGate:
    def __init__(self):
        self.verified_customer = None
        self.orders_for = {"C-7731": {"ORD-1182", "ORD-1190"}}

    def call(self, tool, args):
        if tool == "get_customer":
            if args.get("email") == "meera@example.com" and args.get("phone_last4") == "4471":
                self.verified_customer = "C-7731"
                return "verified C-7731"
            return "not verified"
        if tool in ("lookup_order", "process_refund"):
            if not self.verified_customer:
                return f"BLOCKED {tool}: no verified customer yet (call get_customer first)"
            if args["order_id"] not in self.orders_for[self.verified_customer]:
                return f"BLOCKED {tool}: {args['order_id']} does not belong to {self.verified_customer}"
            return f"{tool} ok for {args['order_id']}"
        return "unknown tool"

g = PrerequisiteGate()
for tool, args in [("process_refund", {"order_id": "ORD-1182"}),                   # agent skipped verification
                   ("get_customer", {"email": "meera@example.com", "phone_last4": "4471"}),
                   ("lookup_order", {"order_id": "ORD-2001"}),                      # someone else's order
                   ("process_refund", {"order_id": "ORD-1182"})]:
    print(f"{tool:<15} → {g.call(tool, args)}")

handoff = {
    "customer_id": "C-7731", "verified": True,
    "issues": [
        {"item": "Blender ORD-1182 arrived broken", "status": "refund issued $42.00", "done": True},
        {"item": "Charged twice for ORD-1190", "root_cause": "payment retried after gateway timeout; two captures",
         "amount": 129.00, "status": "needs billing-team review before refund", "done": False},
    ],
    "recommended_action": "Confirm both captures settled, then refund the duplicate $129.00 on ORD-1190",
    "customer_preference": "Prefers email updates; frustrated about the double charge",
}
print("ESCALATION HANDOFF")
for k, v in handoff.items():
    if k != "issues": print(f"  {k}: {v}")
for i in handoff["issues"]:
    print(f"  - {i['item']}: {i['status']}" + (f" (root cause: {i['root_cause']})" if "root_cause" in i else ""))

# ============================================================================
# Session 1.5 — Hooks for interception and normalisation
# ============================================================================

from datetime import datetime, timezone

REFUND_LIMIT = 500.00
STATUS_CODES = {0: "pending", 1: "processing", 2: "completed", 9: "failed"}

def pre_tool_use(tool, args):
    if tool == "process_refund" and args["amount"] > REFUND_LIMIT:
        return {"decision": "deny",
                "reason": f"Refunds over ${REFUND_LIMIT:.0f} need a person. Call escalate_to_human with the order, amount and reason."}
    return {"decision": "allow"}

def to_iso(v):
    if isinstance(v, (int, float)):                                   # Unix seconds
        return datetime.fromtimestamp(v, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "/" in v:                                                      # 20/10/2026 (day first)
        return datetime.strptime(v, "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00Z")
    return v.replace("+00:00", "Z")                                   # already ISO 8601

def post_tool_use(tool, result):
    out = dict(result)
    for key in ("ts", "created", "updated_at"):
        if key in out: out["processed_at"] = to_iso(out.pop(key))
    if isinstance(out.get("status"), int): out["status"] = STATUS_CODES.get(out["status"], "unknown")
    return out

print(pre_tool_use("process_refund", {"order_id": "ORD-1190", "amount": 650.00}))
print(pre_tool_use("process_refund", {"order_id": "ORD-1182", "amount": 42.00}))
raw = [("refund_api", {"status": 2, "ts": 1792828800}),
       ("orders_mcp", {"status": "completed", "created": "20/10/2026"}),
       ("billing_mcp", {"status": 1, "updated_at": "2026-10-20T06:40:00+00:00"})]
for tool, r in raw:
    print(f"{tool:<12} {str(r):<55} → {post_tool_use(tool, r)}")

# ============================================================================
# Session 1.6 — Task decomposition strategies
# ============================================================================

MODULES = {  # module: (lines, changes in last 90 days, test coverage %, business-critical)
    "billing/charges.py":   (820, 34, 12, True),
    "billing/refunds.py":   (410, 21, 0,  True),
    "orders/cart.py":       (650, 18, 55, True),
    "reports/export.py":    (300, 2,  0,  False),
    "utils/dates.py":       (120, 9,  20, False),
}
def impact(m):
    lines, churn, cov, critical = MODULES[m]
    return round(churn * (100 - cov) / 100 * (2 if critical else 1), 1)

plan = sorted(MODULES, key=impact, reverse=True)
print("step 1, mapped structure:", len(MODULES), "modules")
print("step 2, prioritised by impact (churn × untested share × criticality):")
for m in plan: print(f"   {impact(m):>6}  {m}")

discovered = {"billing/refunds.py": ["billing/charges.py", "utils/dates.py"]}       # found while writing refund tests
print("\nstep 3, adapt: writing refund tests revealed dependencies", discovered["billing/refunds.py"])
adapted = []
for m in plan:
    for dep in discovered.get(m, []):
        if dep not in adapted: adapted.append(dep)
    if m not in adapted: adapted.append(m)
print("adapted order:", adapted)

# ============================================================================
# Session 1.7 — Sessions: resume and fork
# ============================================================================

# from claude_agent_sdk import query, ClaudeAgentOptions

# # Branch B: same baseline analysis, different strategy, without touching branch A
# options = ClaudeAgentOptions(resume=baseline_session_id, fork_session=True)
# async for msg in query(prompt="Try the strangler-fig migration approach instead.", options=options):
#     ...

def resume_or_fresh(files_analysed, files_changed_since, days_since):
    stale = len(set(files_analysed) & set(files_changed_since)) / len(files_analysed)
    if stale == 0:
        return "resume as is", None
    if stale <= 0.25:
        note = ("Since we last spoke these files changed: " + ", ".join(sorted(set(files_analysed) & set(files_changed_since)))
                + ". Re-read only those before continuing; earlier findings for other files still hold.")
        return "resume + tell it what changed", note
    return "start fresh with a structured summary of findings", None

analysed = ["billing/refunds.py", "billing/charges.py", "orders/cart.py", "utils/dates.py", "api/refunds.py", "tests/test_refunds.py", "models/order.py", "models/payment.py"]
for changed in ([], ["billing/refunds.py"], ["billing/refunds.py", "billing/charges.py", "orders/cart.py", "models/order.py"]):
    choice, note = resume_or_fresh(analysed, changed, 1)
    print(f"{len(changed)} changed → {choice}")
    if note: print("   message:", note)
