# Claude Certified Architect – Foundations: study course — Module 2: Tool Design & MCP Integration
# https://xploreai.co.in/courses/claude-architect-foundations/module-2/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 2.1 — Tool interfaces and descriptions
# ============================================================================

import re

MINIMAL = {"get_customer": "Retrieves customer information.",
           "lookup_order": "Retrieves order details."}
COMPLETE = {
    "get_customer": "Returns a customer's account: name, email, address, phone, loyalty tier. Input: email or customer ID like C-7731. "
                    "Use for account, address or profile questions. Not for orders, parcels or deliveries: use lookup_order.",
    "lookup_order": "Returns one order: status, items, delivery date, refund state. Input: order number like ORD-12345 or #12345, "
                    "or a parcel tracking number. Use for 'where is my order', delivery, return and refund questions about an order.",
}
STOP = set("a an the my is of for to and or i me it this like use not on".split())
def stem(w): return w[:-3] + "y" if w.endswith("ies") else (w[:-1] if w.endswith("s") and len(w) > 3 else w)
def words(s): return {stem(w) for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP}

def score(query, desc):
    pos, _, neg = desc.partition("Not for")                  # the boundary clause counts against the tool
    return len(words(query) & words(pos)) - 2 * len(words(query) & words(neg))

def choose(query, tools):
    scores = {t: score(query, d) for t, d in tools.items()}
    best = max(scores.values())
    return [t for t, v in scores.items() if v == best][0] if best > 0 else "get_customer (default: first tool)"

QUERIES = [("check my order #12345", "lookup_order"), ("where is my parcel, it was due Tuesday", "lookup_order"),
           ("change the email on my account", "get_customer"), ("has my refund for the blender gone through", "lookup_order")]
for label, tools in [("minimal", MINIMAL), ("complete", COMPLETE)]:
    right = 0
    for q, want in QUERIES:
        got = choose(q, tools); right += got.startswith(want)
    print(f"{label:<9} descriptions: {right}/{len(QUERIES)} routed correctly")
    for q, want in QUERIES:
        print(f"    {q!r:<44} → {choose(q, tools)}")

# ============================================================================
# Session 2.2 — Structured error responses
# ============================================================================

import json

def tool_error(category, message, retryable, customer_message=None, **extra):
    return {"isError": True, "content": [{"type": "text", "text": json.dumps(
        {"errorCategory": category, "isRetryable": retryable, "message": message,
         **({"customerMessage": customer_message} if customer_message else {}), **extra})}]}

def agent_decision(result):
    if not result.get("isError"):
        data = json.loads(result["content"][0]["text"])
        return "valid empty result: tell the customer there are no matches" if data.get("matches") == [] else "use the data"
    e = json.loads(result["content"][0]["text"])
    if e["isRetryable"]:                   return f"retry ({e['errorCategory']}), bounded"
    if e["errorCategory"] == "business":   return f"don't retry; tell the customer: {e['customerMessage']}"
    if e["errorCategory"] == "validation": return "don't retry as is; fix the input or ask the user"
    return "don't retry; escalate or request access"

results = {
    "timeout":        tool_error("transient", "orders service timed out after 10s", True),
    "bad id":         tool_error("validation", "order_id 'ORD12' doesn't match ORD-NNNNN", False),
    "window closed":  tool_error("business", "return window closed 2026-09-30", False,
                                 customer_message="This order is outside the 30-day return window, but it may still be under warranty."),
    "no access":      tool_error("permission", "agent role can't read corporate accounts", False),
    "no matches":     {"isError": False, "content": [{"type": "text", "text": json.dumps({"matches": []})}]},
}
for name, r in results.items():
    print(f"{name:<14} → {agent_decision(r)}")

# ============================================================================
# Session 2.3 — Distributing tools and tool_choice
# ============================================================================

checks = 100
simple, deep = 85, 15
via_coordinator_trips = 3          # synthesis → coordinator → search → synthesis
verify_fact_trips = 1              # one scoped tool call

before = checks * via_coordinator_trips
after = simple * verify_fact_trips + deep * via_coordinator_trips
print(f"round trips per 100 checks: {before} before, {after} with a scoped verify_fact tool ({1 - after / before:.0%} fewer)")

ALLOWED_STORES = ("https://docs.internal.example/", "https://policies.internal.example/")
def load_document(url):
    if not url.startswith(ALLOWED_STORES):
        return {"isError": True, "errorCategory": "validation", "isRetryable": False,
                "message": "load_document only accepts approved document stores"}
    return {"isError": False, "content": f"(document text from {url})"}
for u in ["https://docs.internal.example/refund-policy", "https://evil.example/payload.html"]:
    print(f"{u:<48} → {'loaded' if not load_document(u)['isError'] else 'rejected: not an approved store'}")

# response = client.messages.create(
#     model="claude-haiku-5-5",                    # a model that still accepts forced tool_choice
#     max_tokens=2048,
#     tools=[extract_invoice, extract_receipt, extract_contract],
#     tool_choice={"type": "any"},                 # must call one of the extraction tools
#     messages=[{"role": "user", "content": [doc_block, {"type": "text", "text": "Extract this document."}]}],
# )

# ============================================================================
# Session 2.4 — Integrating MCP servers
# ============================================================================

import os, re

PROJECT = {"github": {"headers": {"Authorization": "Bearer ${GITHUB_TOKEN}"}, "tools": ["create_issue", "search_code"]},
           "orders": {"env": {"ORDERS_API_KEY": "${ORDERS_API_KEY}"}, "tools": ["lookup_order", "process_refund"]}}
USER = {"scratch-notes": {"env": {}, "tools": ["save_note", "find_note"]}}
ENV = {"GITHUB_TOKEN": "ghp_(set in the shell)"}                        # ORDERS_API_KEY missing on this machine

def expand(obj, env, missing):
    if isinstance(obj, dict): return {k: expand(v, env, missing) for k, v in obj.items()}
    if isinstance(obj, list): return [expand(v, env, missing) for v in obj]
    if isinstance(obj, str):
        for var in re.findall(r"\$\{(\w+)\}", obj):
            if var not in env: missing.append(var)
        return re.sub(r"\$\{(\w+)\}", lambda m: env.get(m.group(1), "<MISSING>"), obj)
    return obj

available = []
for scope, servers in (("project", PROJECT), ("user", USER)):
    for name, cfg in servers.items():
        missing = []
        expand(cfg, ENV, missing)
        status = f"credential missing: {missing}" if missing else "connected"
        if not missing: available += [f"mcp__{name}__{t}" for t in cfg["tools"]]
        print(f"{scope:<8}{name:<14}{status}")
print("\ntools available together:", available)

# ============================================================================
# Session 2.5 — The built-in tools
# ============================================================================

import fnmatch

REPO = {
    "src/payments/refund.py": "from .client import charge\n\ndef issue_refund(order, amount):\n    log('refund start')\n    result = charge(order, -amount)\n    log('refund done')\n    return result\n",
    "src/payments/client.py": "def charge(order, amount):\n    log('charge')\n    return gateway.post(order, amount)\n",
    "src/payments/__init__.py": "from .refund import issue_refund as refund\nfrom .client import charge as raw_charge\n",
    "src/api/routes.py": "from payments import refund\n\ndef post_refund(req):\n    return refund(req.order, req.amount)\n",
    "src/ui/Button.test.tsx": "test('renders')\n", "src/ui/Modal.test.tsx": "test('opens')\n",
}
grep = lambda pat: [(p, i + 1) for p, src in REPO.items() for i, line in enumerate(src.splitlines()) if re.search(pat, line)]
glob = lambda pat: sorted(p for p in REPO if fnmatch.fnmatch(p, pat))

print("Glob **/*.test.tsx:", glob("*.test.tsx"))           # fnmatch's * also crosses folders, like **
print("Grep 'log\\(' (content):", grep(r"log\("))

def edit(path, old, new):
    count = REPO[path].count(old)
    if count != 1:
        return f"Edit failed: {count} matches for {old!r}; fall back to Read + Write"
    REPO[path] = REPO[path].replace(old, new); return "edited"
print("Edit 'log(' → 'audit(' in refund.py:", edit("src/payments/refund.py", "log(", "audit("))
src = REPO["src/payments/refund.py"]                                    # fallback: Read the whole file...
REPO["src/payments/refund.py"] = src.replace("log(", "audit(")         # ...and Write the corrected version
print("after Read + Write:", re.findall(r"\w+\('refund \w+'\)", REPO["src/payments/refund.py"]))

exports = re.findall(r"import (\w+) as (\w+)", REPO["src/payments/__init__.py"])
print("\nwrapper exports:", exports)
for original, alias in exports:
    print(f"  callers of {alias} (wraps {original}):", [p for p, _ in grep(rf"\b{alias}\(")])
