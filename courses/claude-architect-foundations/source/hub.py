"""Course hub page: courses/claude-architect-foundations/index.html

PLAN lists every module (one per exam domain, in the official blueprint's order), with one session per
task statement. A module goes live as soon as content/mN.md exists.
"""
import html, os

GUIDE = "https://anthropic-partners.skilljar.com/page/partner-certifications"

PLAN = [
    {"module": 1, "title": "Agentic Architecture & Orchestration", "weight": "27%",
     "lede": "The biggest domain. Agentic loops, coordinator–subagent orchestration, passing context to subagents, enforcing workflow order with code, hooks, task decomposition, and session resumption and forking.",
     "sessions": [{"num": "1.1", "title": "Agentic loops"}, {"num": "1.2", "title": "Coordinator–subagent orchestration"},
                  {"num": "1.3", "title": "Subagent invocation and context passing"}, {"num": "1.4", "title": "Enforcement and handoff"},
                  {"num": "1.5", "title": "Hooks for interception and normalisation"}, {"num": "1.6", "title": "Task decomposition strategies"},
                  {"num": "1.7", "title": "Sessions: resume and fork"}]},
    {"module": 2, "title": "Tool Design & MCP Integration", "weight": "18%",
     "lede": "Tool descriptions that route reliably, structured error responses, tools scoped to agent roles and tool_choice, MCP servers in Claude Code, and the built-in tools.",
     "sessions": [{"num": "2.1", "title": "Tool interfaces and descriptions"}, {"num": "2.2", "title": "Structured error responses"},
                  {"num": "2.3", "title": "Distributing tools and tool_choice"}, {"num": "2.4", "title": "Integrating MCP servers"},
                  {"num": "2.5", "title": "The built-in tools"}]},
    {"module": 3, "title": "Claude Code Configuration & Workflows", "weight": "20%",
     "lede": "The CLAUDE.md hierarchy, slash commands and skills, path-specific rules, plan mode versus direct execution, iterative refinement, and Claude Code in CI/CD.",
     "sessions": [{"num": "3.1", "title": "The CLAUDE.md hierarchy"}, {"num": "3.2", "title": "Slash commands and skills"},
                  {"num": "3.3", "title": "Path-specific rules"}, {"num": "3.4", "title": "Plan mode or direct execution"},
                  {"num": "3.5", "title": "Iterative refinement"}, {"num": "3.6", "title": "Claude Code in CI/CD"}]},
    {"module": 4, "title": "Prompt Engineering & Structured Output", "weight": "20%",
     "lede": "Explicit criteria that cut false positives, few-shot examples, structured output with tool use and JSON schemas, validation and retry loops, batch processing, and multi-pass review.",
     "sessions": [{"num": "4.1", "title": "Explicit criteria"}, {"num": "4.2", "title": "Few-shot examples"},
                  {"num": "4.3", "title": "Structured output with tool use"}, {"num": "4.4", "title": "Validation, retry and feedback"},
                  {"num": "4.5", "title": "Batch processing"}, {"num": "4.6", "title": "Multi-instance and multi-pass review"}]},
    {"module": 5, "title": "Context Management & Reliability", "weight": "15%",
     "lede": "Keeping critical facts through long interactions, escalation and ambiguity, error propagation across agents, exploring large codebases, human review and confidence calibration, and provenance in multi-source synthesis.",
     "sessions": [{"num": "5.1", "title": "Preserving critical information"}, {"num": "5.2", "title": "Escalation and ambiguity"},
                  {"num": "5.3", "title": "Error propagation across agents"}, {"num": "5.4", "title": "Exploring large codebases"},
                  {"num": "5.5", "title": "Human review and confidence"}, {"num": "5.6", "title": "Provenance and uncertainty"}]},
]

FACTS = [("60", "questions"), ("4 of 6", "scenarios per exam"), ("720", "pass mark, on a 100–1,000 scale"), ("$125", "exam fee (USD)")]

SCENARIOS = [
    ("Customer support resolution agent", "An Agent SDK agent with MCP tools for customers, orders, refunds and escalation, aiming for 80%+ first-contact resolution.", "1, 2, 5"),
    ("Code generation with Claude Code", "Slash commands, CLAUDE.md configuration, and knowing when to use plan mode.", "3, 5"),
    ("Multi-agent research system", "A coordinator delegating to search, analysis, synthesis and report subagents that produce cited reports.", "1, 2, 5"),
    ("Developer productivity with Claude", "An agent that explores unfamiliar codebases with the built-in tools and MCP servers.", "2, 3, 1"),
    ("Claude Code for continuous integration", "Automated reviews, test generation and PR feedback with few false positives.", "3, 4"),
    ("Structured data extraction", "Extracting from unstructured documents, validating with JSON schemas, handling edge cases.", "4, 5"),
]
TOP = max(float(p["weight"][:-1]) for p in PLAN)


def render_hub(outline, counts, head, foot, inline, slug, site):
    nsess = sum(len(m["sessions"]) for m in outline)
    live = [m for m in outline if m["live"]]
    bars = "".join(
        f'<div class="wbar" style="--w:{float(m["weight"][:-1]) / TOP:.3f};--i:{k}"><span class="lbl">{m["module"]}. {html.escape(m["title"])}</span>'
        f'<span class="track"><span class="fill"></span></span><b>{m["weight"]}</b></div>' for k, m in enumerate(outline))
    cards = []
    for m in outline:
        n = m["module"]
        if m["live"]:
            li = "".join(f'<li><a href="module-{n}/#{x["id"]}"><span>{x["num"]}</span>{html.escape(x["title"])}</a></li>' for x in m["sessions"])
            cta = f'<a class="btn" href="module-{n}/">Start module {n} →</a>'
            title = f'<a href="module-{n}/">{html.escape(m["title"])}</a>'
        else:
            li = "".join(f'<li><span>{x["num"]}</span>{html.escape(x["title"])}</li>' for x in m["sessions"])
            cta = '<span class="soon">Coming soon</span>'
            title = html.escape(m["title"])
        cards.append(
            f'<article class="mod{"" if m["live"] else " off"}"><div class="no">{n:02d}<small>DOMAIN · {m["weight"]}</small></div><div>'
            f'<h3>{title}</h3><p>{inline(m["lede"])}</p><ol>{li}</ol>{cta}</div></article>')
    facts = "".join(f'<div class="card"><b>{a}</b><span>{b}</span></div>' for a, b in FACTS)
    scen = "".join(f'<div class="card"><b>{k}. {html.escape(t)}</b><span>{html.escape(d)} <em>Domains {dm}.</em></span></div>'
                   for k, (t, d, dm) in enumerate(SCENARIOS, 1))
    first = f'<a class="btn" href="module-{live[0]["module"]}/">Start with Module {live[0]["module"]} →</a>' if live else ""
    page = head("Claude Certified Architect – Foundations (CCAR-F): a free study course",
                "Prepare for the Claude Certified Architect – Foundations exam: five modules mapped to the official blueprint, one session per "
                "task statement, with animated architectures, real Python with its output, configs and practice questions.",
                "https://xploreai.co.in/courses/claude-architect-foundations/")
    page += f"""
<main class="cca">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / Courses</p>
  <span class="pill">FREE STUDY COURSE · CCAR-F · {len(outline)} MODULES · {nsess} TASK STATEMENTS</span>
  <h1>Claude Certified Architect – Foundations<i>.</i></h1>
  <p class="lede">A study course for Anthropic's <strong>Claude Certified Architect – Foundations</strong> exam, built on its official guide: one module per domain and <strong>one session per task statement</strong>. The exam is scenario-based and practical (agent loops, subagents, hooks, tools, MCP, Claude Code configuration, structured output, context and escalation), so every session pairs an animated <strong>architecture</strong> with <strong>Python</strong> that really runs and scenario-style practice questions.</p>
  <div class="dl">{first} <a class="btn ghost" href="#scenarios">The six scenarios</a></div>
  <p class="disclaimer"><b>Unofficial.</b> Not affiliated with or endorsed by Anthropic. Exam facts are taken from Anthropic's public <a href="{GUIDE}">Exam Guide</a>; check it for the latest. Practice questions here are our own wording, not exam items. Where the guide and current Claude models differ (for example, newer models reject forced tool_choice), each session says so.</p>
</header>

<section class="hub-sec wrap" id="exam">
  <span class="eyebrow">The exam</span>
  <h2 class="big">At a glance<i>.</i></h2>
  <div class="facts">{facts}</div>
  <p class="lede" style="margin-top:22px">120 minutes of multiple-choice and multiple-response questions, proctored online or at a Pearson VUE centre, grouped under realistic production scenarios. It's for solution architects who build production applications with the Claude Agent SDK, Claude Code and MCP, with about six months of hands-on experience. The credential lasts 12 months.</p>
</section>

<section class="hub-sec wrap" id="scenarios">
  <span class="eyebrow">The scenarios</span>
  <h2 class="big">Four of these six, at random<i>.</i></h2>
  <p class="lede">Every question sits inside one of these production scenarios. The course's examples are built around them.</p>
  <div class="legend-grid">{scen}</div>
</section>

<section class="hub-sec wrap" id="blueprint">
  <span class="eyebrow">The blueprint</span>
  <h2 class="big">Where the marks are<i>.</i></h2>
  <p class="lede">Each domain's share of the scored questions. Agentic architecture alone is more than a quarter of the exam.</p>
  <div class="weights anim">{bars}</div>
</section>

<section class="hub-sec wrap" id="how">
  <span class="eyebrow">How each session works</span>
  <h2 class="big">See it, run it, check it<i>.</i></h2>
  <p class="lede">Across the course: {counts["anim"]} animated architectures and flows, {counts["python"]} Python cells with their real output, {counts["file"]} configs and API snippets, and {counts["quiz"]} scenario-style practice questions.</p>
  <div class="legend-grid">
    <div class="card"><b>Architectures</b><span>Animated sequence diagrams: what calls what, and where the controls sit.</span></div>
    <div class="card"><b>Python that runs</b><span>Plain Python 3, run when the page was built. Where Claude would answer, a scripted stand-in plays its part, and says so.</span></div>
    <div class="card"><b>Configs and API code</b><span>CLAUDE.md, rules, skills, .mcp.json, tool schemas and SDK calls, as you'd write them.</span></div>
    <div class="card"><b>Exam lens</b><span>What the guide says is tested, and the traps in the wrong answers.</span></div>
    <div class="card"><b>Then vs now</b><span>Where current Claude models behave differently from the guide, flagged in place.</span></div>
    <div class="card"><b>Practice</b><span>Scenario questions with instant feedback and the reasoning behind each answer.</span></div>
  </div>
</section>

<section class="hub-sec wrap" id="modules">
  <span class="eyebrow">The course</span>
  <h2 class="big">Five domains, five modules<i>.</i></h2>
  <div class="hub-mods">{"".join(cards)}</div>
</section>
</main>
"""
    page += foot
    open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(page)
