"""Course hub page: courses/claude-associate/index.html

PLAN lists every module (one per exam domain, in the official blueprint's order). A module goes
live as soon as content/mN.md exists; until then the hub shows its planned sessions as "coming soon".
"""
import html, os

GUIDE = "https://anthropic-partners.skilljar.com/page/partner-certifications"

PLAN = [
    {"module": 1, "title": "Prompting and Task Execution", "weight": "14%",
     "lede": "Write prompts that get it right first time, break big jobs into steps, iterate with purpose, and match your approach to the task.",
     "sessions": [{"num": "1.1", "title": "Anatomy of an effective prompt"}, {"num": "1.2", "title": "Decomposing complex tasks"},
                  {"num": "1.3", "title": "Iterating to a better output"}, {"num": "1.4", "title": "Prompting by task type"}]},
    {"module": 2, "title": "Output Evaluation and Validation", "weight": "21%",
     "lede": "The biggest domain. Check outputs for accuracy, spot hallucinations and bias, verify facts, know when a human must review, and shape the result for its audience.",
     "sessions": [{"num": "2.1", "title": "Accuracy and completeness"}, {"num": "2.2", "title": "Hallucinations, inconsistencies and bias"},
                  {"num": "2.3", "title": "Fact-checking techniques"}, {"num": "2.4", "title": "When a human must review"},
                  {"num": "2.5", "title": "Editing for the audience"}, {"num": "2.6", "title": "Choosing the output format"}]},
    {"module": 3, "title": "Product and Model Selection", "weight": "12%",
     "lede": "Chat, Projects, Research or Artifacts? Haiku, Sonnet or Opus? Pick the right tool for quality, speed and cost, and manage context.",
     "sessions": [{"num": "3.1", "title": "Choosing the right Claude feature"}, {"num": "3.2", "title": "Haiku, Sonnet and Opus"},
                  {"num": "3.3", "title": "Matching the model to the task"}, {"num": "3.4", "title": "Context limits and memory"}]},
    {"module": 4, "title": "Workflow Integration and Solution Design", "weight": "16%",
     "lede": "Use Claude to analyse requirements, research and plan, design and iterate on solutions, fit into existing workflows, and explain its value honestly.",
     "sessions": [{"num": "4.1", "title": "Analysing requirements and use cases"}, {"num": "4.2", "title": "Research, planning and process optimisation"},
                  {"num": "4.3", "title": "Supporting solution design"}, {"num": "4.4", "title": "Augmenting or redesigning a workflow"},
                  {"num": "4.5", "title": "Communicating value and limits"}]},
    {"module": 5, "title": "Configuration and Knowledge Management", "weight": "12%",
     "lede": "Set up Projects with instructions and knowledge, connect Google Drive and Gmail, write system-level instructions, and keep it all current.",
     "sessions": [{"num": "5.1", "title": "Configuring a Project"}, {"num": "5.2", "title": "Knowledge files and connectors"},
                  {"num": "5.3", "title": "Writing system-level instructions"}, {"num": "5.4", "title": "Maintaining configurations"}]},
    {"module": 6, "title": "Governance, Risk, and Responsible Use", "weight": "15%",
     "lede": "Know which uses are appropriate, protect sensitive and regulated data, follow your organisation's AI policy, and weigh the ethics.",
     "sessions": [{"num": "6.1", "title": "Appropriate and inappropriate uses"}, {"num": "6.2", "title": "Data sensitivity and privacy"},
                  {"num": "6.3", "title": "Following AI policy and governance"}, {"num": "6.4", "title": "Ethical implications"}]},
    {"module": 7, "title": "Troubleshooting and Optimization", "weight": "10%",
     "lede": "Diagnose why a prompt or output falls short, adjust from feedback, and make whole workflows faster and more reliable.",
     "sessions": [{"num": "7.1", "title": "Diagnosing poor outputs"}, {"num": "7.2", "title": "Adjusting from feedback"},
                  {"num": "7.3", "title": "Optimising workflows"}]},
]

FACTS = [("60", "questions"), ("120", "minutes"), ("720", "pass mark, on a 100–1,000 scale"), ("$99", "exam fee (USD)")]


def render_hub(outline, counts, head, foot, inline, slug, site):
    nsess = sum(len(m["sessions"]) for m in outline)
    live = [m for m in outline if m["live"]]
    bars = "".join(
        f'<div class="wbar" style="--w:{int(m["weight"][:-1]) / 21:.3f};--i:{k}"><span class="lbl">{m["module"]}. {html.escape(m["title"])}</span>'
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
    page = head("Claude Certified Associate – Foundations (CCAO-F): a free study course",
                "Prepare for the Claude Certified Associate – Foundations exam: seven modules mapped to the official blueprint, "
                "with animated workflows, example screens, prompts to copy, light Python and practice questions.",
                "https://xploreai.co.in/courses/claude-associate/")
    page += f"""
<main class="cca">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / Courses</p>
  <span class="pill">FREE STUDY COURSE · CCAO-F · {len(outline)} MODULES · {nsess} SESSIONS</span>
  <h1>Claude Certified Associate – Foundations<i>.</i></h1>
  <p class="lede">A study course for Anthropic's <strong>Claude Certified Associate – Foundations</strong> exam, built on its official blueprint: one module per exam domain, one session per objective. Every idea is shown as a <strong>workflow</strong>, a <strong>screen</strong> or a <strong>prompt</strong> you can copy, with light Python where it helps, and practice questions to check yourself.</p>
  <div class="dl">{first} <a class="btn ghost" href="#exam">The exam at a glance</a></div>
  <p class="disclaimer"><b>Unofficial.</b> Not affiliated with or endorsed by Anthropic. Exam facts are taken from Anthropic's public <a href="{GUIDE}">Exam Guide, version 1.0 (July 2026)</a>; check it for the latest. Practice questions here are our own and are not drawn from the exam.</p>
</header>

<section class="hub-sec wrap" id="exam">
  <span class="eyebrow">The exam</span>
  <h2 class="big">At a glance<i>.</i></h2>
  <div class="facts">{facts}</div>
  <p class="lede" style="margin-top:22px">Multiple-choice and multiple-response questions (each says how many answers to pick), proctored online or at a Pearson VUE centre. No coding or API experience is needed: it's for people who use Claude to get business work done, such as operations, marketing, project management, education and communications. The credential lasts 12 months, with free online renewal.</p>
</section>

<section class="hub-sec wrap" id="blueprint">
  <span class="eyebrow">The blueprint</span>
  <h2 class="big">Where the marks are<i>.</i></h2>
  <p class="lede">Each domain's share of the scored questions. Output evaluation alone is about a fifth of the exam.</p>
  <div class="weights anim">{bars}</div>
</section>

<section class="hub-sec wrap" id="how">
  <span class="eyebrow">How each session works</span>
  <h2 class="big">See it, copy it, check it<i>.</i></h2>
  <p class="lede">Across the course: {counts["anim"]} animated workflows, screens and comparisons, {counts["prompt"]} ready-to-copy prompts, {counts["python"]} Python cells that run with their real output, and {counts["quiz"]} practice questions.</p>
  <div class="legend-grid">
    <div class="card"><b>Workflows</b><span>Animated diagrams of how a task flows from request to result.</span></div>
    <div class="card"><b>Screens</b><span>Example Claude conversations and settings panels. They are <em>illustrative</em>: real replies vary.</span></div>
    <div class="card"><b>Prompts</b><span>Ready to copy into Claude, often as a weak and a strong version side by side.</span></div>
    <div class="card"><b>Python</b><span>Light, optional code that really runs, with its real output, for the parts a script does best.</span></div>
    <div class="card"><b>Exam lens</b><span>What the exam is likely to test, in the style of its questions.</span></div>
    <div class="card"><b>Practice</b><span>Questions with instant feedback and the reasoning behind each answer.</span></div>
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
