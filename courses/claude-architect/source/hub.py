"""Course hub page: courses/claude-architect/index.html

PLAN lists every module (one per exam domain, in the official blueprint's order). A module goes
live as soon as content/mN.md exists; until then the hub shows its planned sessions as "coming soon".
"""
import html, os

GUIDE = "https://anthropic-partners.skilljar.com/page/partner-certifications"

PLAN = [
    {"module": 1, "title": "Solution Design & Architecture", "weight": "17%",
     "lede": "Turn a business problem into a Claude solution: end-to-end architecture with feedback loops, the right pattern (augmented LLM, workflow or agent), multi-agent orchestration, decomposition, and the business value it must deliver.",
     "sessions": [{"num": "1.1", "title": "From business problem to Claude solution"}, {"num": "1.2", "title": "End-to-end architecture and feedback loops"},
                  {"num": "1.3", "title": "Choosing the pattern"}, {"num": "1.4", "title": "Multi-agent orchestration"},
                  {"num": "1.5", "title": "Decomposition"}, {"num": "1.6", "title": "Business value pillars"}]},
    {"module": 2, "title": "Claude Models, Prompting & Context Engineering", "weight": "13%",
     "lede": "Choose models on real trade-offs, design system prompts and guardrails, pick the right prompting technique, engineer the context window, and reuse prompts with caching, modules and Skills.",
     "sessions": [{"num": "2.1", "title": "Model selection trade-offs"}, {"num": "2.2", "title": "System prompts, templates and guardrails"},
                  {"num": "2.3", "title": "Prompting techniques"}, {"num": "2.4", "title": "Engineering the context window"},
                  {"num": "2.5", "title": "Prompt reuse: caching, modules and Skills"}]},
    {"module": 3, "title": "Integration", "weight": "19%",
     "lede": "The biggest domain. Find capability bloat and auth gaps, justify accuracy-latency trade-offs, observe systems at scale, design RAG pipelines and retrieval, and choose between MCP, APIs, CLIs and agent-to-agent protocols.",
     "sessions": [{"num": "3.1", "title": "Capability bloat and tool scoping"}, {"num": "3.2", "title": "Authentication and authorisation gaps"},
                  {"num": "3.3", "title": "Accuracy versus latency"}, {"num": "3.4", "title": "Observability at scale"},
                  {"num": "3.5", "title": "Designing a RAG pipeline"}, {"num": "3.6", "title": "Retrieval strategies"},
                  {"num": "3.7", "title": "MCP, API/CLI or agent-to-agent"}, {"num": "3.8", "title": "Progressive discovery vs monolithic context"}]},
    {"module": 4, "title": "Evaluation, Testing & Optimization", "weight": "16%",
     "lede": "Define metrics for accuracy, latency, cost, safety and security; build eval datasets with mixed methods; run A/B tests; diagnose prompt failures, hallucinations and model mismatch; and tune cost-performance in production.",
     "sessions": [{"num": "4.1", "title": "Evaluation metrics"}, {"num": "4.2", "title": "Eval datasets and mixed methods"},
                  {"num": "4.3", "title": "A/B testing and iteration"}, {"num": "4.4", "title": "Diagnosing system issues"},
                  {"num": "4.5", "title": "Optimising cost and performance"}, {"num": "4.6", "title": "Monitoring and observability"}]},
    {"module": 5, "title": "Governance, Safety & Risk Management", "weight": "14%",
     "lede": "Layer guardrails, name the risks and failure modes of LLM systems, design human-in-the-loop validation, meet GDPR, HIPAA and FedRAMP requirements, and address bias, fairness and transparency.",
     "sessions": [{"num": "5.1", "title": "Guardrails and safety controls"}, {"num": "5.2", "title": "Risks and failure modes"},
                  {"num": "5.3", "title": "Human-in-the-loop validation"}, {"num": "5.4", "title": "Regulatory compliance"},
                  {"num": "5.5", "title": "Bias, fairness and transparency"}]},
    {"module": 6, "title": "Stakeholder Communication & Lifecycle Management", "weight": "14%",
     "lede": "Run structured discovery, explain architectural decisions and trade-offs to every audience, manage feedback and SLAs, document for the team that builds it, and carry a solution through its whole life cycle.",
     "sessions": [{"num": "6.1", "title": "Structured discovery"}, {"num": "6.2", "title": "Communicating decisions and trade-offs"},
                  {"num": "6.3", "title": "Feedback loops and SLAs"}, {"num": "6.4", "title": "Architecture documentation"},
                  {"num": "6.5", "title": "The solution life cycle"}]},
    {"module": 7, "title": "Developer Productivity & Operational Enablement", "weight": "7%",
     "lede": "Configure Claude Code for a team, improve developer workflows with AI-assisted tooling, and support debugging and operational incidents.",
     "sessions": [{"num": "7.1", "title": "Configuring Claude Code for teams"}, {"num": "7.2", "title": "AI-assisted developer workflows"},
                  {"num": "7.3", "title": "Debugging and operations"}]},
]

FACTS = [("63", "questions"), ("120", "minutes"), ("720", "pass mark, on a 100–1,000 scale"), ("$175", "exam fee (USD)")]
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
    page = head("Claude Certified Architect – Professional (CCAR-P): a study course",
                "Prepare for the Claude Certified Architect – Professional exam: seven modules mapped to the official blueprint, "
                "with animated architectures, decision records, real Python with its output, and practice questions.",
                "https://xploreai.co.in/courses/claude-architect/")
    page += f"""
<main class="cca">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / Courses</p>
  <span class="pill">STUDY COURSE · CCAR-P · {len(outline)} MODULES · {nsess} SESSIONS</span>
  <h1>Claude Certified Architect – Professional<i>.</i></h1>
  <p class="lede">A study course for Anthropic's <strong>Claude Certified Architect – Professional</strong> exam, built on its official blueprint: one module per exam domain. It's about <strong>decisions</strong>: which pattern, which model, which integration, which control, and how to justify each to engineers, security, legal and executives. Every idea comes as an animated <strong>architecture</strong>, a <strong>decision record</strong> or a <strong>trade-off</strong> worked through in <strong>Python</strong> that really runs, with practice questions to check yourself.</p>
  <div class="dl">{first} <a class="btn ghost" href="#exam">The exam at a glance</a></div>
  <p class="disclaimer"><b>Unofficial.</b> Not affiliated with or endorsed by Anthropic. Exam facts are taken from Anthropic's public <a href="{GUIDE}">Exam Guide, version 1.0 (July 2026)</a>; check it for the latest. Practice questions here are our own and are not drawn from the exam. Product details move fast: confirm them in Anthropic's documentation before you design around them.</p>
</header>

<section class="hub-sec wrap" id="exam">
  <span class="eyebrow">The exam</span>
  <h2 class="big">At a glance<i>.</i></h2>
  <div class="facts">{facts}</div>
  <p class="lede" style="margin-top:22px">Multiple-choice and multiple-response questions (each says how many answers to pick), proctored online or at a Pearson VUE centre. It's the senior tier of the architect track, for solution architects, AI/ML engineers and technical leads who design and deliver production Claude systems end to end. Anthropic suggests three or more years in systems architecture or platform engineering and six months of production work with Claude or a similar LLM. There's no prerequisite. The credential lasts 12 months.</p>
</section>

<section class="hub-sec wrap" id="blueprint">
  <span class="eyebrow">The blueprint</span>
  <h2 class="big">Where the marks are<i>.</i></h2>
  <p class="lede">Each domain's share of the scored questions. Integration, design and evaluation make up over half the exam; governance and stakeholder work another 28%.</p>
  <div class="weights anim">{bars}</div>
</section>

<section class="hub-sec wrap" id="how">
  <span class="eyebrow">How each session works</span>
  <h2 class="big">Decide it, prove it, defend it<i>.</i></h2>
  <p class="lede">Across the course: {counts["anim"]} animated architectures, flows and comparisons, {counts["python"]} Python cells with their real output, {counts["file"]} decision records, configs and API snippets, and {counts["quiz"]} practice questions.</p>
  <div class="legend-grid">
    <div class="card"><b>Architectures</b><span>Animated sequence diagrams and flows: what calls what, and where the controls sit.</span></div>
    <div class="card"><b>Python that runs</b><span>Trade-offs worked through in plain Python 3, run when the page was built. Where Claude would answer, a scripted stand-in plays its part, and says so.</span></div>
    <div class="card"><b>Decision records</b><span>Architecture decision records, runbooks and configs, written the way you'd hand them to a team.</span></div>
    <div class="card"><b>API code</b><span>Real Anthropic SDK calls, marked <em>shown, not run here</em>.</span></div>
    <div class="card"><b>Exam lens</b><span>What the exam is likely to test, in the style of its questions.</span></div>
    <div class="card"><b>Practice</b><span>Scenario questions with instant feedback and the reasoning behind each answer.</span></div>
  </div>
</section>

<section class="hub-sec wrap" id="modules">
  <span class="eyebrow">The course</span>
  <h2 class="big">Seven domains, seven modules<i>.</i></h2>
  <div class="hub-mods">{"".join(cards)}</div>
</section>
</main>
"""
    page += foot
    open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(page)
