# Claude Certified Developer – Foundations: study course — Module 8: Tools and MCPs
# https://xploreai.co.in/courses/claude-developer/module-8/
# Plain Python 3, no extra packages. Run it top to bottom.


# ============================================================================
# Session 8.1 — Tool use end to end
# ============================================================================

import json, re, time
from concurrent.futures import ThreadPoolExecutor

def check_slots(doctor, date):
    time.sleep(0.2)                                   # pretend network call
    return {"Dr Rao": ["10:30", "11:15"], "Dr Iyer": []}.get(doctor, [])

def get_invoice(invoice_no):
    time.sleep(0.2)
    return {"INV-88213": {"amount": 850, "status": "paid twice"}}[invoice_no]

REGISTRY = {
    "check_slots": (check_slots, {"doctor": str, "date": r"^\d{4}-\d{2}-\d{2}$"}),
    "get_invoice": (get_invoice, {"invoice_no": r"^INV-\d{5}$"}),
}

def validate(args, spec):
    for field, rule in spec.items():
        if field not in args: return f"missing required field '{field}'"
        v = args[field]
        if rule is str and not isinstance(v, str): return f"'{field}' must be a string"
        if isinstance(rule, str) and not re.fullmatch(rule, str(v)): return f"'{field}'={v!r} doesn't match {rule}"
    extra = set(args) - set(spec)
    return f"unexpected field(s) {sorted(extra)}" if extra else None

def run_one(block):
    name, args = block["name"], block["input"]
    if name not in REGISTRY:
        return {"type": "tool_result", "tool_use_id": block["id"], "is_error": True,
                "content": f"Unknown tool '{name}'. Available: {sorted(REGISTRY)}"}
    fn, spec = REGISTRY[name]
    problem = validate(args, spec)
    if problem:
        return {"type": "tool_result", "tool_use_id": block["id"], "is_error": True, "content": f"Invalid input: {problem}"}
    try:
        return {"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(fn(**args))}
    except Exception as e:
        return {"type": "tool_result", "tool_use_id": block["id"], "is_error": True, "content": f"{type(e).__name__}: {e}"}

response_content = [
    {"type": "text", "text": "Let me check both doctors and your invoice."},
    {"type": "tool_use", "id": "tu_1", "name": "check_slots", "input": {"doctor": "Dr Rao", "date": "2026-10-30"}},
    {"type": "tool_use", "id": "tu_2", "name": "check_slots", "input": {"doctor": "Dr Iyer", "date": "30/10/2026"}},
    {"type": "tool_use", "id": "tu_3", "name": "get_invoice", "input": {"invoice_no": "INV-88213"}},
    {"type": "tool_use", "id": "tu_4", "name": "refund_all", "input": {}},
]
calls = [b for b in response_content if b["type"] == "tool_use"]
t0 = time.time()
with ThreadPoolExecutor() as pool:
    results = list(pool.map(run_one, calls))          # order preserved, run concurrently
print(f"{len(calls)} calls in {time.time() - t0:.1f}s\n")
for r in results:
    print(f"{r['tool_use_id']}  {'ERROR ' if r.get('is_error') else 'ok    '}{r['content']}")
next_message = {"role": "user", "content": results}
print("\nall results in one user message:", len(next_message["content"]), "tool_result blocks")

# ============================================================================
# Session 8.2 — Tool descriptions and errors
# ============================================================================

STOP = set("a an the of for to and or by use it is are with on in this that as e g".split())

TOOLS = {
    "get_customer":  "Gets customer information and account data.",
    "lookup_order":  "Gets order information and account data for customers.",
    "refund_status": "Returns the refund state and expected date for one order number, e.g. ORD-104233. Not for order contents.",
    "find_slots":    "Lists free appointment times for one doctor on one date.",
}

def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP}

pairs = []
names = list(TOOLS)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = words(TOOLS[names[i]]), words(TOOLS[names[j]])
        pairs.append((len(a & b) / len(a | b), names[i], names[j], sorted(a & b)))
for score, a, b, shared in sorted(pairs, reverse=True)[:3]:
    flag = "  ← likely to be confused" if score > 0.4 else ""
    print(f"{score:.2f}  {a} / {b}  shared: {shared}{flag}")

class NotFound(Exception): pass
class RateLimited(Exception): pass

def describe_error(tool, args, exc):
    if isinstance(exc, NotFound):
        return (f"No order matches {args.get('order_ref')!r}. Order numbers look like ORD-123456. "
                "Ask the user to check the number; don't guess another one.")
    if isinstance(exc, RateLimited):
        return "The order service is busy. Wait a few seconds and retry once; if it fails again, tell the user it's temporarily unavailable."
    if isinstance(exc, PermissionError):
        return "This order belongs to a different account. Don't reveal anything about it; ask the user to sign in to the right account."
    return f"{tool} failed unexpectedly ({type(exc).__name__}). Don't retry; apologise and offer the support line."

for exc in [NotFound(), RateLimited(), PermissionError(), ValueError("bad state")]:
    print(f"{type(exc).__name__:<16} → {describe_error('lookup_order', {'order_ref': 'ORD-14233'}, exc)}")

# ============================================================================
# Session 8.3 — Approval patterns and gates
# ============================================================================

def risk_policy(action):
    t, a = action["tool"], action["args"]
    if t == "run_sql" and re.search(r"\b(drop|truncate|delete)\b", a["query"], re.I):
        return "deny", "destructive SQL is never run by the agent"
    if t in ("read_file", "search_docs", "check_slots", "run_sql"):
        return "allow", "read-only"
    if t == "send_email":
        external = not a["to"].endswith("@sunriseclinic.in")
        bulk = a.get("recipients", 1) > 20
        if external or bulk:
            return "ask", ("external " if external else "") + ("bulk " if bulk else "") + "email"
        return "allow", "internal, small"
    if t == "issue_refund":
        return ("ask", "refund over ₹2,000") if a["amount"] > 2_000 else ("allow", "small refund within policy")
    return "ask", "unknown action: default to a person"

day = ([{"tool": "check_slots", "args": {}}] * 140 + [{"tool": "search_docs", "args": {}}] * 60 +
       [{"tool": "send_email", "args": {"to": "front@sunriseclinic.in"}}] * 25 +
       [{"tool": "issue_refund", "args": {"amount": 850}}] * 12 + [{"tool": "issue_refund", "args": {"amount": 4_200}}] * 2 +
       [{"tool": "send_email", "args": {"to": "patients@list", "recipients": 3_200}}] +
       [{"tool": "run_sql", "args": {"query": "DELETE FROM bookings WHERE date < '2025-01-01'"}}])

tally = {}
for act in day:
    verdict, why = risk_policy(act)
    tally.setdefault(verdict, {}).setdefault(why, 0)
    tally[verdict][why] += 1
for verdict in ("allow", "ask", "deny"):
    total = sum(tally.get(verdict, {}).values())
    print(f"{verdict.upper():<6} {total:>4}  {tally.get(verdict, {})}")
print(f"\nprompts a person sees today: {sum(tally['ask'].values())} out of {len(day)} actions")

# ============================================================================
# Session 8.4 — Building an MCP server
# ============================================================================

import json, os, subprocess, sys, tempfile

SERVER = r'''
import json, sys
STOCK = {"GLV-M-100": 412, "MSK-N95-20": 0}
TOOLS = [{"name": "check_stock", "description": "Units in stock for one SKU, e.g. GLV-M-100.",
          "inputSchema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}}]
RESOURCES = [{"uri": "inventory://warehouses", "name": "Warehouses", "mimeType": "text/plain"}]
PROMPTS = [{"name": "stockout_report", "description": "Weekly report of SKUs at zero stock"}]

def handle(req):
    m, p = req["method"], req.get("params", {})
    if m == "tools/list":     return {"tools": TOOLS}
    if m == "resources/list": return {"resources": RESOURCES}
    if m == "prompts/list":   return {"prompts": PROMPTS}
    if m == "resources/read": return {"contents": [{"uri": p["uri"], "text": "Andheri, Thane, Pune"}]}
    if m == "tools/call":
        sku = p["arguments"]["sku"]
        if sku not in STOCK:
            return {"content": [{"type": "text", "text": f"Unknown SKU {sku}"}], "isError": True}
        return {"content": [{"type": "text", "text": f"{STOCK[sku]} in stock"}]}
    raise KeyError(m)

for line in sys.stdin:
    req = json.loads(line)
    try:
        out = {"jsonrpc": "2.0", "id": req["id"], "result": handle(req)}
    except KeyError as e:
        out = {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": f"Method not found: {e}"}}
    print(json.dumps(out), flush=True)
'''

path = os.path.join(tempfile.mkdtemp(), "inventory_server.py")
open(path, "w").write(SERVER)
proc = subprocess.Popen([sys.executable, "-I", path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

def rpc(i, method, params=None):
    msg = {"jsonrpc": "2.0", "id": i, "method": method, **({"params": params} if params else {})}
    proc.stdin.write(json.dumps(msg) + "\n"); proc.stdin.flush()
    reply = json.loads(proc.stdout.readline())
    print(f"→ {json.dumps(msg)}\n← {json.dumps(reply)}\n")
    return reply

rpc(1, "tools/list")
rpc(2, "tools/call", {"name": "check_stock", "arguments": {"sku": "GLV-M-100"}})
rpc(3, "tools/call", {"name": "check_stock", "arguments": {"sku": "XYZ"}})
rpc(4, "resources/read", {"uri": "inventory://warehouses"})
rpc(5, "tools/delete")
proc.stdin.close(); proc.wait()
print("server process exited with code", proc.returncode)

# from mcp.server import MCPServer

# mcp = MCPServer("inventory")

# @mcp.tool()
# async def check_stock(sku: str) -> str:
#     """Units in stock for one SKU, e.g. GLV-M-100. Returns 'unknown SKU' if it doesn't exist."""
#     units = await inventory_api.get_units(sku)          # your existing REST API
#     return f"{units} in stock"

# @mcp.resource("inventory://warehouses")
# def warehouses() -> str:
#     return "Andheri, Thane, Pune"

# if __name__ == "__main__":
#     mcp.run(transport="stdio")

# response = client.beta.messages.create(
#     model="claude-sonnet-5-5", max_tokens=4096,
#     betas=["mcp-client-2026-09-15"],
#     mcp_servers=[{"type": "url", "url": "https://mcp.example.com/mcp", "name": "tickets",
#                   "authorization_token": os.environ["TICKETS_TOKEN"]}],
#     tools=[{"type": "mcp_toolset", "mcp_server_name": "tickets"}],
#     messages=[{"role": "user", "content": "Open a ticket for the broken X-ray printer at Andheri."}],
# )

# ============================================================================
# Session 8.5 — Tools, Skills or MCP?
# ============================================================================

def choose(need):
    if need.get("generic_capability"):                       return "built-in / server tool"
    if need.get("procedure_or_style") and not need.get("new_access"):
                                                             return "Skill"
    if need.get("new_access") and need.get("apps", 1) > 1:   return "MCP server"
    if need.get("new_access"):                               return "custom tool in that app"
    if need.get("must_always_happen"):                       return "hook"
    return "CLAUDE.md / prompt"

needs = [
    ("Inventory REST API, used by several Claude apps, owned by the ops team", dict(new_access=True, apps=3)),
    ("Look up current news for a research brief",                             dict(generic_capability=True)),
    ("Our 9-step month-end reconciliation procedure",                         dict(procedure_or_style=True)),
    ("Issue refunds from inside the billing app only",                        dict(new_access=True, apps=1)),
    ("Run the formatter after every edit",                                    dict(must_always_happen=True)),
    ("Always use British spelling in this repo",                              dict()),
]
for name, n in needs:
    print(f"{choose(n):<26} ← {name}")

M, N = 4, 6
print(f"\n{M} apps × {N} systems: {M * N} custom integrations, or {M + N} MCP pieces ({M} clients + {N} servers)")
