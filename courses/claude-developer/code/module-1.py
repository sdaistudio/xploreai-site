# Claude Certified Developer – Foundations: study course — Module 1: Agents and Workflows
# https://xploreai.co.in/courses/claude-developer/module-1/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 1.1 — Workflow or agent?
# ============================================================================

def choose_tier(task):
    """Return the lowest tier that fits, with the reason."""
    if task["steps_known_in_advance"] and task["steps"] == 1:
        return "single call", "one step, nothing to orchestrate"
    if task["steps_known_in_advance"]:
        return "workflow", "the path can be written down, so code should own it"
    # Open-ended: an agent is a candidate, but only if all four checks pass
    checks = {
        "complexity": not task["steps_known_in_advance"],
        "value": task["value_per_run_usd"] >= 5 * task["est_cost_usd"],
        "viability": task["claude_good_at_it"],
        "cost of error": task["errors_reversible"],
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        return "workflow (+ human)", "agent ruled out by: " + ", ".join(failed)
    return "agent", "open-ended, worth it, feasible, and errors can be undone"

tasks = [
    ("Tag a message as booking/billing/clinical", dict(steps_known_in_advance=True,  steps=1, value_per_run_usd=0.02, est_cost_usd=0.001, claude_good_at_it=True,  errors_reversible=True)),
    ("Invoice: extract, validate, draft email",   dict(steps_known_in_advance=True,  steps=3, value_per_run_usd=1.5,  est_cost_usd=0.01,  claude_good_at_it=True,  errors_reversible=True)),
    ("Fix last night's failing build",            dict(steps_known_in_advance=False, steps=0, value_per_run_usd=60,   est_cost_usd=1.2,   claude_good_at_it=True,  errors_reversible=True)),
    ("Research a competitor, write a brief",      dict(steps_known_in_advance=False, steps=0, value_per_run_usd=40,   est_cost_usd=0.8,   claude_good_at_it=True,  errors_reversible=True)),
    ("Move money between client accounts",        dict(steps_known_in_advance=False, steps=0, value_per_run_usd=25,   est_cost_usd=0.5,   claude_good_at_it=True,  errors_reversible=False)),
]

for name, t in tasks:
    tier, why = choose_tier(t)
    print(f"{name:<44} → {tier:<18} {why}")

# ============================================================================
# Session 1.2 — The agentic loop
# ============================================================================

# import anthropic

# client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY from the environment
# messages = [{"role": "user", "content": "Is Dr Rao free on Friday morning? If so, hold 10:30 for Mrs Iyer."}]

# while True:
#     response = client.messages.create(
#         model="claude-opus-5-5", max_tokens=16000,
#         system=SYSTEM, tools=TOOLS, messages=messages,
#     )
#     messages.append({"role": "assistant", "content": response.content})   # keep the whole turn

#     if response.stop_reason != "tool_use":
#         break

#     results = []
#     for block in response.content:                     # there may be several tool_use blocks
#         if block.type == "tool_use":
#             output, failed = run_tool(block.name, block.input)
#             results.append({"type": "tool_result", "tool_use_id": block.id,
#                             "content": output, "is_error": failed})
#     messages.append({"role": "user", "content": results})   # all results, one user turn

# print(next(b.text for b in response.content if b.type == "text"))

import json

CALENDAR = {("Dr Rao", "Fri"): {"09:00": "Mr Shah", "10:30": None, "11:15": None}}
HOLDS = []

def check_slots(doctor, day):
    slots = CALENDAR.get((doctor, day))
    if slots is None:
        raise KeyError(f"no calendar for {doctor} on {day}")
    return [t for t, who in slots.items() if who is None]

def hold_slot(doctor, day, time, patient):
    if CALENDAR[(doctor, day)].get(time, "taken") is not None:
        raise ValueError(f"{time} is not free")
    CALENDAR[(doctor, day)][time] = patient + " (held)"
    HOLDS.append((doctor, day, time, patient))
    return f"held {time} on {day} with {doctor} for {patient}"

TOOLS = {"check_slots": check_slots, "hold_slot": hold_slot}

def run_tool(name, args):
    """Route a tool call to its function. Return (content, is_error)."""
    if name not in TOOLS:
        return f"unknown tool: {name}", True
    try:
        return json.dumps(TOOLS[name](**args)), False
    except Exception as e:                       # report the failure to the model, don't crash the loop
        return f"{type(e).__name__}: {e}", True

print(run_tool("check_slots", {"doctor": "Dr Rao", "day": "Fri"}))
print(run_tool("check_slots", {"doctor": "Dr Rao", "day": "Sun"}))

SCRIPT = [
    {"stop_reason": "tool_use", "content": [
        {"type": "text", "text": "I'll check Friday, and Saturday as a fallback."},
        {"type": "tool_use", "id": "tu_1", "name": "check_slots", "input": {"doctor": "Dr Rao", "day": "Fri"}},
        {"type": "tool_use", "id": "tu_2", "name": "check_slots", "input": {"doctor": "Dr Rao", "day": "Sat"}}]},
    {"stop_reason": "tool_use", "content": [
        {"type": "tool_use", "id": "tu_3", "name": "hold_slot",
         "input": {"doctor": "Dr Rao", "day": "Fri", "time": "10:30", "patient": "Mrs Iyer"}}]},
    {"stop_reason": "end_turn", "content": [
        {"type": "text", "text": "Done: 10:30 on Friday with Dr Rao is held for Mrs Iyer."}]},
]

def scripted_claude(messages, turn):
    """A stand-in for client.messages.create: returns the next scripted reply."""
    return SCRIPT[turn]

def run_agent(user_text, model=scripted_claude, max_turns=10):
    messages = [{"role": "user", "content": user_text}]
    for turn in range(max_turns):
        reply = model(messages, turn)
        messages.append({"role": "assistant", "content": reply["content"]})
        calls = [b for b in reply["content"] if b["type"] == "tool_use"]
        print(f"turn {turn + 1}: stop_reason={reply['stop_reason']}, tool calls={len(calls)}")
        if reply["stop_reason"] != "tool_use":
            return reply["content"][-1]["text"], messages
        results = []
        for c in calls:
            content, failed = run_tool(c["name"], c["input"])
            print(f"   {c['name']}({c['input']['day']}) → {'ERROR ' if failed else ''}{content}")
            results.append({"type": "tool_result", "tool_use_id": c["id"], "content": content, "is_error": failed})
        messages.append({"role": "user", "content": results})
    raise RuntimeError(f"no answer after {max_turns} turns")

answer, history = run_agent("Is Dr Rao free on Friday morning? If so, hold 10:30 for Mrs Iyer.")
print("\nfinal answer:", answer)
print("messages in history:", len(history), "→", [m["role"] for m in history])

def check_history(messages):
    problems = []
    for i, m in enumerate(messages):
        if m["role"] != "assistant" or isinstance(m["content"], str):
            continue
        asked = {b["id"] for b in m["content"] if b["type"] == "tool_use"}
        if not asked:
            continue
        nxt = messages[i + 1] if i + 1 < len(messages) else {"content": []}
        answered = {b.get("tool_use_id") for b in nxt["content"] if isinstance(b, dict)}
        for missing in sorted(asked - answered):
            problems.append(f"message {i}: tool_use {missing} has no tool_result in the next user turn")
    return problems or ["ok"]

print("good history:  ", check_history(history))

broken = [dict(m) for m in history]
broken[2] = {"role": "user", "content": broken[2]["content"][:1]}     # handled only the first call
print("broken history:", check_history(broken))

# ============================================================================
# Session 1.3 — Coordinators and subagents
# ============================================================================

# Rough token accounting: what each design puts in the deciding model's context
reading = {"finance": 38_000, "market": 52_000, "risk": 27_000}   # tokens each piece of research reads
summary = 400                                                       # tokens each subagent sends back
brief_instructions = 1_500

single = brief_instructions + sum(reading.values())
coordinator = brief_instructions + summary * len(reading)

print(f"one agent does everything : {single:>7,} tokens in context when it writes the brief")
print(f"coordinator + 3 subagents : {coordinator:>7,} tokens in the coordinator's context")
print(f"largest subagent context  : {max(reading.values()) + 600:>7,} tokens (its own window)")
print(f"total tokens processed    : {sum(reading.values()) + 600 * 3 + coordinator:>7,} (more in total, but no window is overloaded)")

from concurrent.futures import ThreadPoolExecutor
import time

REQUIRED = ("objective", "inputs", "output", "out_of_scope")

plan = [
    {"agent": "finance", "objective": "Q3 vs Q2 revenue and margin per clinic", "inputs": "P&L exports",
     "output": "table + 150 words", "out_of_scope": "forecasts"},
    {"agent": "market", "objective": "competitor openings within 3 km since July", "inputs": "maps search",
     "output": "list of name, date, distance", "out_of_scope": "pricing"},
    {"agent": "risk", "objective": "analyse risks"},                       # under-specified on purpose
]

def missing_fields(spec):
    return [f for f in REQUIRED if not spec.get(f)]

for spec in plan:
    gaps = missing_fields(spec)
    print(f"{spec['agent']:<8} {'ready' if not gaps else 'REJECTED, missing: ' + ', '.join(gaps)}")

def subagent(spec):                      # stand-in: a real one would be its own Claude loop
    time.sleep(0.2)                      # pretend to work
    return {"agent": spec["agent"], "summary": f"[{spec['agent']}] findings on: {spec['objective']}"}

ready = [s for s in plan if not missing_fields(s)]
t0 = time.time()
with ThreadPoolExecutor() as pool:
    reports = list(pool.map(subagent, ready))
print(f"\n{len(reports)} subagents ran in parallel in {time.time() - t0:.1f}s (each takes 0.2s)")
for r in reports:
    print(" ", r["summary"])

# ============================================================================
# Session 1.4 — Building agents with Claude
# ============================================================================

# import anthropic
# from anthropic import beta_tool

# client = anthropic.Anthropic()

# @beta_tool
# def check_slots(doctor: str, day: str) -> str:
#     """List the free appointment times for a doctor on a given day.

#     Args:
#         doctor: The doctor's name exactly as it appears in the rota, e.g. "Dr Rao".
#         day: Three-letter day name, e.g. "Fri".
#     """
#     return json.dumps(free_slots(doctor, day))

# runner = client.beta.messages.tool_runner(
#     model="claude-opus-5-5", max_tokens=16000,
#     tools=[check_slots],
#     messages=[{"role": "user", "content": "When is Dr Rao free on Friday?"}],
# )
# for message in runner:          # one BetaMessage per model turn; stops when Claude is done
#     print(message.content)

# import asyncio
# from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

# options = ClaudeAgentOptions(
#     system_prompt="You maintain the clinic booking service. Never touch production config.",
#     allowed_tools=["Read", "Grep", "Glob", "Bash"],   # pre-approved; not a whitelist on its own
#     permission_mode="default",
#     max_turns=30,
#     model="claude-opus-5-5",
#     agents={                                           # subagents Claude can delegate to
#         "test-runner": AgentDefinition(
#             description="Runs the test suite and reports failures concisely.",
#             prompt="Run the tests. Report only failing tests with file, line and error.",
#             model="claude-haiku-5-5",
#         ),
#     },
# )

# async def main():
#     async for message in query(prompt="Find why test_booking fails and fix it.", options=options):
#         print(message)

# asyncio.run(main())

def stuck_model(messages, turn):
    """A scripted stand-in that never stops calling tools."""
    return {"stop_reason": "tool_use", "usage": {"input_tokens": 1_800 + 900 * turn, "output_tokens": 120},
            "content": [{"type": "tool_use", "id": f"tu_{turn}", "name": "check_slots",
                         "input": {"doctor": "Dr Rao", "day": "Fri"}}]}

def guarded_agent(user_text, model, max_turns=8, token_budget=12_000):
    messages, spent, trace = [{"role": "user", "content": user_text}], 0, []
    for turn in range(max_turns):
        reply = model(messages, turn)
        spent += reply["usage"]["input_tokens"] + reply["usage"]["output_tokens"]
        trace.append((turn + 1, reply["stop_reason"], spent))
        if spent > token_budget:
            return "stopped: token budget exceeded", trace
        messages.append({"role": "assistant", "content": reply["content"]})
        if reply["stop_reason"] != "tool_use":
            return "finished", trace
        results = [{"type": "tool_result", "tool_use_id": b["id"], "content": run_tool(b["name"], b["input"])[0]}
                   for b in reply["content"] if b["type"] == "tool_use"]
        messages.append({"role": "user", "content": results})
    return "stopped: turn limit reached", trace

for limit, budget in [(8, 12_000), (3, 50_000)]:
    status, trace = guarded_agent("Find me a slot.", stuck_model, limit, budget)
    print(f"max_turns={limit}, budget={budget:,}: {status}")
    for t, why, spent in trace:
        print(f"   turn {t}: {why:<8} tokens so far {spent:>6,}")

# ============================================================================
# Session 1.5 — Hooks for deterministic actions
# ============================================================================

import json, os, re

SANDBOX = "/tmp/agent-sandbox"
DANGEROUS = {                                   # what the rule stops: the pattern that spots it
    "rm -rf reaching outside the project": r"\brm\s+-rf?\b.*(\s/|\s\.\.|~)",
    "force-pushing": r"\bgit\s+push\b.*--force",
    "dropping a table": r"\bDROP\s+TABLE\b",
    "piping a download into a shell": r"curl[^|]*\|\s*(ba)?sh",
}

def pre_tool_use(event):
    """Return (exit_code, stdout, stderr), as a hook script would."""
    tool, args = event["tool_name"], event["tool_input"]
    if tool == "Bash":
        for rule, pattern in DANGEROUS.items():
            if re.search(pattern, args["command"], re.I):
                return 2, "", f"Blocked by policy: {rule} is not allowed. Work inside the project only."
    if tool in ("Write", "Edit"):
        path = args["file_path"]
        if not os.path.abspath(path).startswith(SANDBOX + "/"):
            fixed = dict(args, file_path=os.path.join(SANDBOX, os.path.basename(path)))
            out = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                          "permissionDecision": "allow", "updatedInput": fixed}}
            return 0, json.dumps(out), ""
    return 0, "", ""                                    # silence = no opinion

events = [
    {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "pytest -q tests/"}},
    {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "rm -rf build/ ../shared"}},
    {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "/etc/report.txt", "content": "..."}},
    {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": SANDBOX + "/notes.md", "content": "..."}},
]
for e in events:
    code, out, err = pre_tool_use(e)
    shown = e["tool_input"].get("command") or e["tool_input"]["file_path"]
    verdict = "BLOCK" if code == 2 else ("REWRITE" if out else "pass")
    print(f"{e['tool_name']:<6} {shown:<28} exit={code}  {verdict}")
    if err: print("       stderr →", err)
    if out: print("       stdout →", json.loads(out)["hookSpecificOutput"]["updatedInput"]["file_path"])

# from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

# async def protect_env_files(input_data, tool_use_id, context):
#     path = input_data["tool_input"].get("file_path", "")
#     if path.split("/")[-1].lower() == ".env":
#         return {"hookSpecificOutput": {
#             "hookEventName": input_data["hook_event_name"],
#             "permissionDecision": "deny",
#             "permissionDecisionReason": "Agents may not modify .env files",
#         }}
#     return {}

# options = ClaudeAgentOptions(
#     hooks={"PreToolUse": [HookMatcher(matcher="Write|Edit", hooks=[protect_env_files])]},
# )

# ============================================================================
# Session 1.6 — Memory and context in agents
# ============================================================================

def run_cost(turns, tool_tokens, keep_last=None, base=2_500, per_turn_text=150, price_in=2.00):
    """Total input tokens (and $ at price_in per million) for an agent run."""
    history, total = [], 0
    for t in range(turns):
        context = base + sum(history)
        total += context
        history.append(per_turn_text + tool_tokens)        # this turn's reply + tool result join the history
        if keep_last is not None and len(history) > keep_last:
            i = len(history) - keep_last - 1
            history[i] = per_turn_text + 40                 # old result replaced by a short stub
    return total, total * price_in / 1e6, base + sum(history)

for label, keep in [("keep every tool result", None), ("keep only the last 3", 3)]:
    total, usd, final = run_cost(20, 3_000, keep)
    print(f"{label:<24} total input {total:>9,} tokens  ≈ ${usd:.2f} at $2/MTok   context at the end {final:>6,}")

NOTES = []        # in production: a file, a database table, or the memory tool's directory

def remember(topic, note):
    NOTES.append({"topic": topic, "note": note})
    return "saved"

STOP = {"the", "a", "an", "and", "of", "to", "for", "in", "on", "my", "our"}

def recall(query):
    words = set(query.lower().split()) - STOP
    hits = [n for n in NOTES if words & set((n["topic"] + " " + n["note"]).lower().split())]
    return hits[-3:] or "nothing relevant"

# Run 1 (episodic): the agent records what happened
remember("migration", "Step 3 failed: the index on bookings.created_at took 40 min. Build it concurrently.")
remember("style", "Clinic prefers dates as 12 Oct 2026, never 10/12/26.")

# Run 2, days later: a fresh context. The harness recalls before the agent starts work.
print(recall("plan the bookings migration"))
print(recall("format the appointment dates"))

# ============================================================================
# Session 1.7 — Agent frameworks
# ============================================================================

def classify(state):
    msg = state["message"].lower()
    state["category"] = "clinical" if any(w in msg for w in ("pain", "bleeding", "fever")) else "admin"
    return state

def draft_reply(state):
    state["attempts"] = state.get("attempts", 0) + 1
    state["draft"] = "Thanks, we've received your message." if state["attempts"] == 1 else \
                     "Thanks, Mrs Iyer. Your 10:30 Friday booking is confirmed."
    return state

def check_reply(state):
    state["ok"] = "booking" in state["draft"]           # stand-in for a real quality check
    return state

def escalate(state):
    state["routed_to"] = "duty nurse"
    return state

NODES = {"classify": classify, "draft": draft_reply, "check": check_reply, "escalate": escalate}
EDGES = {
    "classify": lambda s: "escalate" if s["category"] == "clinical" else "draft",
    "draft":    lambda s: "check",
    "check":    lambda s: "END" if s["ok"] or s["attempts"] >= 3 else "draft",   # retry loop
    "escalate": lambda s: "END",
}

def run_graph(state, start="classify"):
    node, checkpoints = start, []
    while node != "END":
        state = NODES[node](dict(state))
        checkpoints.append((node, dict(state)))           # a resumable snapshot after every node
        node = EDGES[node](state)
    return state, checkpoints

for text in ["Can you confirm my Friday booking?", "Sharp pain since this morning"]:
    final, cps = run_graph({"message": text})
    print(f"{text!r}\n   path: {' → '.join(n for n, _ in cps)}")
    print(f"   result: {final.get('draft') or 'routed to ' + final['routed_to']}")

from dataclasses import dataclass

@dataclass
class Triage:
    category: str
    urgency: int
    reply: str

    def __post_init__(self):
        if self.category not in {"admin", "clinical", "billing"}:
            raise ValueError(f"category {self.category!r} not allowed")
        if not 1 <= self.urgency <= 5:
            raise ValueError(f"urgency {self.urgency} outside 1–5")

for raw in ['{"category": "clinical", "urgency": 4, "reply": "A nurse will call you."}',
            '{"category": "urgent!!", "urgency": 9, "reply": "Go to A&E"}']:
    try:
        print("valid  →", Triage(**json.loads(raw)))
    except ValueError as e:
        print("invalid →", e, "(send the error back to the model and ask again)")
