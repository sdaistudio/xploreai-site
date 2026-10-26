"""Course hub page: courses/claude-developer/index.html

PLAN lists every module (one per exam domain, in the official blueprint's order). A module goes
live as soon as content/mN.md exists; until then the hub shows its planned sessions as "coming soon".
"""
import html, os

GUIDE = "https://anthropic-partners.skilljar.com/page/partner-certifications"

PLAN = [
    {"module": 1, "title": "Agents and Workflows", "weight": "14.7%",
     "lede": "When to build a workflow and when an agent, the agentic loop, coordinators and subagents, the Agent SDK and hosting choices, hooks, memory, and agent frameworks.",
     "sessions": [{"num": "1.1", "title": "Workflow or agent?"}, {"num": "1.2", "title": "The agentic loop"},
                  {"num": "1.3", "title": "Coordinators and subagents"}, {"num": "1.4", "title": "Building agents with Claude"},
                  {"num": "1.5", "title": "Hooks for deterministic actions"}, {"num": "1.6", "title": "Memory and context in agents"},
                  {"num": "1.7", "title": "Agent frameworks"}]},
    {"module": 2, "title": "Applications and Integration", "weight": "33.1%",
     "lede": "The biggest domain, a third of the exam. Requirements and the life cycle, the Messages API in depth, batch versus realtime, software engineering foundations, application design and configuration management.",
     "sessions": [{"num": "2.1", "title": "Requirements and the systems life cycle"}, {"num": "2.2", "title": "The Messages API"},
                  {"num": "2.3", "title": "Streaming, vision and thinking"}, {"num": "2.4", "title": "Caching, batches and access paths"},
                  {"num": "2.5", "title": "SDKs and error handling"}, {"num": "2.6", "title": "REST, JSON and async"},
                  {"num": "2.7", "title": "Version control, review and refactoring"}, {"num": "2.8", "title": "Instructions across interfaces"},
                  {"num": "2.9", "title": "Schemas, content boundaries and session hygiene"}, {"num": "2.10", "title": "Configuration management"}]},
    {"module": 3, "title": "Claude Code", "weight": "3.1%",
     "lede": "Claude Code's building blocks, the CLAUDE.md hierarchy, slash commands, settings.json, and running it headless in scripts and CI.",
     "sessions": [{"num": "3.1", "title": "Core components"}, {"num": "3.2", "title": "CLAUDE.md, settings and commands"},
                  {"num": "3.3", "title": "Headless mode and CI/CD"}]},
    {"module": 4, "title": "Eval, Testing, and Debugging", "weight": "2.6%",
     "lede": "Name the error, choose the recovery, read the trace, and tell an integration bug from a model problem. Plus evals and LLM-as-judge.",
     "sessions": [{"num": "4.1", "title": "Error types and recovery"}, {"num": "4.2", "title": "Traces and failure modes"},
                  {"num": "4.3", "title": "Evals and monitoring"}]},
    {"module": 5, "title": "Model Selection and Optimization", "weight": "16.8%",
     "lede": "Tokens, context windows, sampling and non-determinism, thinking and effort, shot prompting, SDKs and websockets, choosing between Opus, Sonnet and Haiku, and modelling cost.",
     "sessions": [{"num": "5.1", "title": "How an LLM generates text"}, {"num": "5.2", "title": "Thinking, effort and fast mode"},
                  {"num": "5.3", "title": "Zero-, one- and few-shot"}, {"num": "5.4", "title": "SDKs, REST and websockets"},
                  {"num": "5.5", "title": "Opus, Sonnet or Haiku"}, {"num": "5.6", "title": "Token budgets and cost models"}]},
    {"module": 6, "title": "Prompt and Context Engineering", "weight": "11%",
     "lede": "Keep context lean with pruning, compaction and isolation; write prompts with clear instructions in the right place; and produce output your code can trust.",
     "sessions": [{"num": "6.1", "title": "Context drift and bloat"}, {"num": "6.2", "title": "Context isolation"},
                  {"num": "6.3", "title": "Writing and iterating prompts"}, {"num": "6.4", "title": "System or user: where instructions go"},
                  {"num": "6.5", "title": "Structured output and defensive parsing"}]},
    {"module": 7, "title": "Security and Safety", "weight": "8.1%",
     "lede": "Prompt injection and jailbreaks, PII and data leakage, layered guardrails and least privilege, hooks that block destructive actions, and keeping secrets secret.",
     "sessions": [{"num": "7.1", "title": "Prompt injection and untrusted input"}, {"num": "7.2", "title": "PII, privacy and data leakage"},
                  {"num": "7.3", "title": "Guardrail layering and least privilege"}, {"num": "7.4", "title": "Hooks as safety controls"},
                  {"num": "7.5", "title": "Secrets, keys and identity"}]},
    {"module": 8, "title": "Tools and MCPs", "weight": "10.6%",
     "lede": "Define and dispatch tools, write descriptions Claude can use, gate risky calls, build an MCP server, and choose between built-in tools, custom tools, Skills and MCP.",
     "sessions": [{"num": "8.1", "title": "Tool use end to end"}, {"num": "8.2", "title": "Tool descriptions and errors"},
                  {"num": "8.3", "title": "Approval patterns and gates"}, {"num": "8.4", "title": "Building an MCP server"},
                  {"num": "8.5", "title": "Tools, Skills or MCP?"}]},
]

FACTS = [("53", "questions"), ("120", "minutes"), ("720", "pass mark, on a 100–1,000 scale"), ("$125", "exam fee (USD)")]
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
    first = f'<a class="btn" href="module-{live[0]["module"]}/">Start with Module {live[0]["module"]} →</a>' if live else ""
    page = head("Claude Certified Developer – Foundations (CCDV-F): a free study course",
                "Prepare for the Claude Certified Developer – Foundations exam: eight modules mapped to the official blueprint, "
                "with animated diagrams, real Python with its output, API code, config files and practice questions.",
                "https://xploreai.co.in/courses/claude-developer/")
    page += f"""
<main class="cca">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / Courses</p>
  <span class="pill">FREE STUDY COURSE · CCDV-F · {len(outline)} MODULES · {nsess} SESSIONS</span>
  <h1>Claude Certified Developer – Foundations<i>.</i></h1>
  <p class="lede">A study course for Anthropic's <strong>Claude Certified Developer – Foundations</strong> exam, built on its official blueprint: one module per exam domain. Every idea is shown as an animated <strong>diagram</strong>, a <strong>screen</strong> or a <strong>config file</strong>, then built step by step in <strong>Python</strong> that really runs, with its real output, and checked with practice questions.</p>
  <div class="dl">{first} <a class="btn ghost" href="#exam">The exam at a glance</a></div>
  <p class="disclaimer"><b>Unofficial.</b> Not affiliated with or endorsed by Anthropic. Exam facts are taken from Anthropic's public <a href="{GUIDE}">Exam Guide, version 1.0 (July 2026)</a>; check it for the latest. Practice questions here are our own and are not drawn from the exam. API details move fast: confirm them in Anthropic's documentation before you ship.</p>
</header>

<section class="hub-sec wrap" id="exam">
  <span class="eyebrow">The exam</span>
  <h2 class="big">At a glance<i>.</i></h2>
  <div class="facts">{facts}</div>
  <p class="lede" style="margin-top:22px">Multiple-choice and multiple-response questions (each says how many answers to pick), proctored online or at a Pearson VUE centre. It's for hands-on developers who build, integrate and ship Claude-powered apps, agents and workflows; Anthropic suggests one to five years of software engineering, six months with Claude or a similar LLM, and Python or TypeScript. The credential lasts 12 months, with free online renewal.</p>
</section>

<section class="hub-sec wrap" id="blueprint">
  <span class="eyebrow">The blueprint</span>
  <h2 class="big">Where the marks are<i>.</i></h2>
  <p class="lede">Each domain's share of the scored questions. Applications and Integration alone is a third of the exam; Claude Code and debugging together are under 6%.</p>
  <div class="weights anim">{bars}</div>
</section>

<section class="hub-sec wrap" id="how">
  <span class="eyebrow">How each session works</span>
  <h2 class="big">See it, build it, check it<i>.</i></h2>
  <p class="lede">Across the course: {counts["anim"]} animated diagrams, screens and comparisons, {counts["python"]} Python cells with their real output, {counts["file"]} config files and API snippets, and {counts["quiz"]} practice questions.</p>
  <div class="legend-grid">
    <div class="card"><b>Diagrams</b><span>Animated sequence diagrams and workflows: who calls whom, in what order.</span></div>
    <div class="card"><b>Python that runs</b><span>Plain Python 3, run when the page was built. The output you see is what it printed. Where Claude would answer, a scripted stand-in plays its part, and says so.</span></div>
    <div class="card"><b>API code</b><span>Real Anthropic SDK calls, marked <em>shown, not run here</em>: copy them into your own project with your own key.</span></div>
    <div class="card"><b>Config files</b><span>CLAUDE.md, settings.json, tool schemas and shell commands, as you would write them.</span></div>
    <div class="card"><b>Exam lens</b><span>What the exam is likely to test, in the style of its questions.</span></div>
    <div class="card"><b>Practice</b><span>Questions with instant feedback and the reasoning behind each answer.</span></div>
  </div>
</section>

<section class="hub-sec wrap" id="modules">
  <span class="eyebrow">The course</span>
  <h2 class="big">Eight domains, eight modules<i>.</i></h2>
  <div class="hub-mods">{"".join(cards)}</div>
</section>
</main>
"""
    page += foot
    open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(page)
