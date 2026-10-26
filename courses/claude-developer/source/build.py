#!/usr/bin/env python3
"""Build the Claude Certified Developer – Foundations study course pages.

content/mN.md  ->  run ```python cells  ->  courses/claude-developer/module-N/index.html
                                           courses/claude-developer/code/module-N.py
Usage: python3 build.py [N ...]   (no args = every module that has a content file, plus the hub)

Block types in content/mN.md (inside a "## N.n | Title" session):
  plain paragraphs, "### " subheads, "- " lists, "| a | b |" tables
  > [read|tip|concept|warn|try|exam] callouts
  ```python            real Python, run at build time; output captured   (eval=false: shown, not run)
  ```prompt title="…"  a prompt to copy into Claude
  ```claude            an ILLUSTRATIVE Claude reply (labelled as such on the page; never a recording)
  ```chat              an animated chat screen: lines "you: …" / "claude: …" (illustrative)
  ```flow              an animated workflow: one step per line, "Title | detail"
  ```anatomy           a prompt whose parts are tagged [role]…[/role]; drawn with a colour legend
  ```compare           two prompts split by a line "---"; first line of each half is its heading
                       (style=neutral: two equally valid versions, no ✗/✓)
  ```quiz              Q: …  then "- [x] right" / "- [ ] wrong" options, then "why: …"
  ```screen title="…"  a mock settings panel: "Label: value" lines ("- item" lines become a list)
  ```seq title="…"     an animated sequence diagram: first line "A, B, C" (the actors), then
                       "A -> B: label" messages, "note A: text" notes; dashed "A --> B: label" for replies
  ```file title="…" lang=json|bash|markdown|typescript   a config file, shell session or other code shown as is
"""
import contextlib, html, io, json, os, re, sys, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ROOT)                       # courses/claude-developer/
BASE = "https://xploreai.co.in/courses/claude-developer/"
COURSE = "Claude Certified Developer – Foundations: study course"
SHORT = "Claude Developer (CCDV-F) course"
FENCE = ("python", "prompt", "claude", "chat", "flow", "anatomy", "compare", "quiz", "screen", "file", "seq")


# ---------- parse ----------
def opts_of(line):
    return {k: v1 or v2 for k, v1, v2 in re.findall(r'(\w+)=(?:"([^"]*)"|([\w.\-]+))', line)}


def parse(path):
    txt = open(path, encoding="utf-8").read()
    meta, body = {}, txt
    m = re.match(r"---\n(.*?)\n---\n", txt, re.S)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        body = txt[m.end():]
    sessions, cur, lines = [], None, body.split("\n")
    i, n = 0, 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("## "):
            num, _, title = ln[3:].partition("|")
            cur = {"num": num.strip(), "title": title.strip(), "blocks": []}
            sessions.append(cur); i += 1; continue
        if cur is None:
            i += 1; continue
        fm = re.match(r"```(\w+)(.*)$", ln)
        if fm and fm.group(1) in FENCE:
            kind, opts, code = fm.group(1), opts_of(fm.group(2)), []
            i += 1
            while not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            n += 1
            cur["blocks"].append({"t": kind, "code": "\n".join(code).strip("\n"),
                                  "id": f"m{meta['module']}b{n:03d}", "opts": opts})
            i += 1; continue
        if ln.startswith("### "):
            cur["blocks"].append({"t": "h3", "text": ln[4:]}); i += 1; continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip()); i += 1
            kind = "read"
            m2 = re.match(r"\[(\w+)\]\s*(.*)", buf[0])
            if m2:
                kind, buf[0] = m2.group(1), m2.group(2)
            cur["blocks"].append({"t": "call", "kind": kind, "text": "\n".join(buf)}); continue
        if re.match(r"\s*[-*] ", ln):
            items = []
            while i < len(lines) and re.match(r"\s*[-*] ", lines[i]):
                items.append(re.sub(r"^\s*[-*] ", "", lines[i])); i += 1
            cur["blocks"].append({"t": "ul", "items": items}); continue
        if re.match(r"\d+\. ", ln):
            items = []
            while i < len(lines) and re.match(r"\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
            cur["blocks"].append({"t": "ol", "items": items}); continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"\|[\s:-]+\|", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            cur["blocks"].append({"t": "table", "rows": rows}); continue
        if ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(```|#|>|\s*[-*] |\d+\. |\|)", lines[i]):
                buf.append(lines[i]); i += 1
            cur["blocks"].append({"t": "p", "text": " ".join(buf)}); continue
        i += 1
    return meta, sessions


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def slug(num):
    return "s" + num.replace(".", "-")


# ---------- run the Python cells (one shared namespace per module, like a notebook) ----------
def run_python(sessions):
    ns, res = {"__name__": "__main__"}, {}
    for s in sessions:
        for b in s["blocks"]:
            if b["t"] != "python" or b["opts"].get("eval") == "false":
                continue
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                try:
                    exec(compile(b["code"], b["id"], "exec"), ns)
                except Exception:
                    if b["opts"].get("error") != "true":
                        raise SystemExit(f"cell {b['id']} (session {s['num']}) failed:\n{traceback.format_exc(limit=1)}")
                    print(traceback.format_exc(limit=0).strip())
            res[b["id"]] = buf.getvalue().rstrip("\n")
    return res


# ---------- render one block ----------
ROLE_COLOURS = ["role", "task", "context", "format", "constraints", "examples", "input", "steps", "tone"]


def copy_btn():
    return '<button class="copy" type="button">Copy</button>'


def render_block(b, res):
    t, code, o = b["t"], b.get("code", ""), b.get("opts", {})
    if t == "p":
        return f"<p>{inline(b['text'])}</p>"
    if t == "h3":
        return f"<h3>{inline(b['text'])}</h3>"
    if t in ("ul", "ol"):
        return f"<{t}>" + "".join(f"<li>{inline(x)}</li>" for x in b["items"]) + f"</{t}>"
    if t == "table":
        hd, *rows = b["rows"]
        return ('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in hd) + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
    if t == "call":
        label = {"read": "How to read it", "tip": "Tip", "concept": "The idea", "warn": "Watch out",
                 "try": "Try it", "exam": "Exam lens"}.get(b["kind"], b["kind"])
        paras = "".join(f"<p>{inline(x)}</p>" for x in b["text"].split("\n") if x)
        return f'<aside class="call {b["kind"]}"><b>{label}</b>{paras}</aside>'
    if t == "python":
        skipped = o.get("eval") == "false"
        tag = '<span class="noeval">shown, not run here</span>' if skipped else ""
        out = res.get(b["id"], "")
        h = (f'<div class="cell"><div class="code"><div class="lab"><span>Python</span>{tag}{copy_btn()}</div>'
             f'<pre><code class="language-python">{html.escape(code)}</code></pre></div>')
        if out.strip():
            h += f'<div class="out"><div class="lab"><span>Output · produced by running this code</span></div><pre>{html.escape(out)}</pre></div>'
        return h + "</div>"
    if t == "seq":
        lines = [ln for ln in code.split("\n") if ln.strip()]
        actors = [a.strip() for a in lines[0].split(",")]
        col = {a: k + 1 for k, a in enumerate(actors)}
        rows = []
        for k, ln in enumerate(lines[1:]):
            m = re.match(r"\s*note\s+(.+?):\s*(.*)", ln)
            if m:
                c = col[m.group(1).strip()]
                rows.append(f'<div class="m note" style="grid-column:{c}/{c+1};--k:{k}"><span>{inline(m.group(2))}</span></div>')
                continue
            m = re.match(r"\s*(.+?)\s*(-->|->)\s*(.+?):\s*(.*)", ln)
            a, b = col[m.group(1)], col[m.group(3)]
            lo, hi = min(a, b), max(a, b)
            cls = ("l" if b < a else "r") + (" reply" if m.group(2) == "-->" else "")
            rows.append(f'<div class="m {cls}" style="grid-column:{lo}/{hi+1};--s:{hi-lo+1};--k:{k}"><span>{inline(m.group(4))}</span><i></i></div>')
        heads = "".join(f"<b>{html.escape(a)}</b>" for a in actors)
        cap = o.get("title", "")
        return (f'<figure class="seq anim" style="--c:{len(actors)}">{f"<figcaption>{html.escape(cap)}</figcaption>" if cap else ""}'
                f'<div class="actors">{heads}</div><div class="lane">{"".join(rows)}</div></figure>')
    if t == "file":
        lang, title = o.get("lang", "plaintext"), o.get("title", "File")
        return (f'<div class="cell file"><div class="code"><div class="lab"><span>{html.escape(title)}</span>{copy_btn()}</div>'
                f'<pre><code class="language-{lang}">{html.escape(code)}</code></pre></div></div>')
    if t == "prompt":
        title = o.get("title", "Prompt")
        return (f'<div class="pcard"><div class="lab"><span>✎ {html.escape(title)}</span>{copy_btn()}</div>'
                f'<pre><code>{html.escape(code)}</code></pre></div>')
    if t == "claude":
        title = o.get("title", "Claude's reply")
        return (f'<div class="ccard"><div class="lab"><span>{html.escape(title)}</span><em class="illus">Illustrative example, not a recorded output</em></div>'
                f'<div class="body">{md_light(code)}</div></div>')
    if t == "chat":
        title = o.get("title", "Chat with Claude")
        msgs = []
        for line in code.split("\n"):
            m = re.match(r"(you|claude|note):\s*(.*)", line, re.I)
            if m:
                msgs.append([m.group(1).lower(), m.group(2)])
            elif msgs and line.strip():
                msgs[-1][1] += "\n" + line
        bubbles = "".join(f'<div class="msg {who}"><span class="who">{"You" if who == "you" else "Claude" if who == "claude" else ""}</span>'
                          f'<div class="bub">{md_light(txt)}</div></div>' for who, txt in msgs)
        return (f'<figure class="screen chat anim"><div class="bar"><i></i><i></i><i></i><span>{html.escape(title)}</span></div>'
                f'<div class="thread">{bubbles}</div><figcaption>Illustrative screen. Real replies vary from run to run.</figcaption></figure>')
    if t == "flow":
        steps = [ln.split("|", 1) for ln in code.split("\n") if ln.strip()]
        items = "".join(f'<li style="--i:{k}"><b>{inline(a.strip())}</b>{f"<span>{inline(d.strip())}</span>" if len(x) > 1 else ""}</li>'
                        for k, x in enumerate(steps) for a, d in [(x[0], x[1] if len(x) > 1 else "")])
        cap = o.get("title", "")
        return (f'<figure class="flow anim" style="--n:{len(steps)}">{f"<figcaption>{html.escape(cap)}</figcaption>" if cap else ""}'
                f'<ol>{items}</ol></figure>')
    if t == "anatomy":
        used = []
        def tag(m):
            k = m.group(1)
            if k not in used:
                used.append(k)
            return f'<mark class="part {k}" data-part="{k}">{html.escape(m.group(2))}</mark>'
        body = re.sub(r"\[(\w+)\](.*?)\[/\1\]", tag, html.escape(code, quote=False).replace("&lt;", "\x00").replace("&gt;", "\x01"), flags=re.S)
        body = body.replace("\x00", "&lt;").replace("\x01", "&gt;")
        legend = "".join(f'<button type="button" class="part {k}" data-part="{k}">{k}</button>' for k in used)
        return (f'<figure class="anatomy anim"><div class="legend">{legend}</div>'
                f'<pre>{body}</pre><figcaption>Tap a label to highlight that part of the prompt.</figcaption></figure>')
    if t == "compare":
        halves = code.split("\n---\n")
        cols = []
        for k, h in enumerate(halves):
            head, _, rest = h.partition("\n")
            cols.append(f'<div class="side {"weak" if k == 0 else "strong"}"><div class="lab"><span>{html.escape(head.lstrip("# "))}</span>{copy_btn()}</div>'
                        f'<pre><code>{html.escape(rest.strip())}</code></pre></div>')
        neutral = " neutral" if o.get("style") == "neutral" else ""
        return f'<div class="compare anim{neutral}">{"".join(cols)}</div>'
    if t == "quiz":
        q, opts_, why = "", [], ""
        for line in code.split("\n"):
            if line.startswith("Q:"):
                q = line[2:].strip()
            elif re.match(r"- \[[ x]\]", line):
                opts_.append((line[3] == "x", line[6:].strip()))
            elif line.startswith("why:"):
                why = line[4:].strip()
            elif line.strip() and not opts_:
                q += " " + line.strip()
        multi = sum(c for c, _ in opts_) > 1
        btns = "".join(f'<button type="button" data-ok="{int(c)}">{chr(65 + k)}. {inline(x)}</button>' for k, (c, x) in enumerate(opts_))
        hint = f'<span class="n">Select {sum(c for c, _ in opts_)}</span>' if multi else ""
        return (f'<div class="quiz" data-multi="{int(multi)}"><p class="q"><b>Practice question</b>{hint}{inline(q)}</p>'
                f'<div class="opts">{btns}</div>{"<button type=button class=check>Check answer</button>" if multi else ""}'
                f'<p class="why" hidden>{inline(why)}</p></div>')
    if t == "screen":
        rows, title = [], o.get("title", "Settings")
        for line in code.split("\n"):
            if line.startswith("- ") and rows:
                rows[-1][2].append(line[2:])
            elif ":" in line:
                k, _, v = line.partition(":")
                rows.append([k.strip(), v.strip(), []])
        body = "".join(f'<div class="row"><span class="k">{html.escape(k)}</span><div class="v">'
                       + (f"<p>{inline(text)}</p>" if text else "")
                       + ("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>" if items else "")
                       + "</div></div>" for k, text, items in rows)
        return (f'<figure class="screen panel anim"><div class="bar"><i></i><i></i><i></i><span>{html.escape(title)}</span></div>'
                f'<div class="rows">{body}</div><figcaption>Illustrative screen, simplified. Labels in the real app may differ.</figcaption></figure>')
    return ""


def md_light(s):
    """Tiny markdown for illustrative replies: paragraphs, - lists, **bold**, `code`."""
    out, buf = [], []
    for ln in s.split("\n") + [""]:
        if re.match(r"\s*[-*] ", ln):
            item = re.sub(r"^\s*[-*] ", "", ln)
            buf.append(f"<li>{inline(item)}</li>"); continue
        if buf:
            out.append("<ul>" + "".join(buf) + "</ul>"); buf = []
        if ln.strip():
            out.append(f"<p>{inline(ln)}</p>")
    return "".join(out)


# ---------- page shell ----------
def _stamp(name):   # cache-buster: changes whenever the file changes
    return str(int(os.path.getmtime(os.path.join(SITE, name))))

HEAD = open(os.path.join(ROOT, "tpl_head.html"), encoding="utf-8").read().replace("course.css", "course.css?v=" + _stamp("course.css"))
FOOT = open(os.path.join(ROOT, "tpl_foot.html"), encoding="utf-8").read().replace("course.js", "course.js?v=" + _stamp("course.js"))


def head(title, desc, url):
    desc = re.sub(r"[`*]", "", desc)
    return HEAD.replace("%%TITLE%%", html.escape(title)).replace("%%DESC%%", html.escape(desc)).replace("%%URL%%", url)


def render_module(meta, sessions, res, outline):
    mod, total = int(meta["module"]), len(outline)
    side = "".join(f'<li><a href="#{slug(s["num"])}"><span>{s["num"]}</span>{html.escape(s["title"])}</a></li>' for s in sessions)
    body = []
    for s in sessions:
        body.append(f'<section class="session" id="{slug(s["num"])}"><p class="snum">Session {s["num"]}</p><h2>{html.escape(s["title"])}</h2>')
        body += [render_block(b, res) for b in s["blocks"]]
        body.append("</section>")
    live = [m["module"] for m in outline if m["live"]]
    prev = f'<a class="btn ghost" href="../module-{mod-1}/">← Module {mod-1}</a>' if mod - 1 in live else '<a class="btn ghost" href="../">← Course home</a>'
    nxt = f'<a class="btn" href="../module-{mod+1}/">Module {mod+1} →</a>' if mod + 1 in live else '<a class="btn" href="../">Course home →</a>'
    page = head(f"Module {mod}: {meta['title']} — {SHORT}", meta.get("lede", ""), f"{BASE}module-{mod}/")
    ncode = sum(1 for s in sessions for b in s["blocks"] if b["t"] == "python")
    dl = f'<a class="btn ghost" href="../code/module-{mod}.py" download>Download the Python</a>' if ncode else ""
    page += f'''
<main class="cca">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / <a href="../">{html.escape(SHORT)}</a> / Module {mod}</p>
  <span class="pill">MODULE {mod} OF {total} · DOMAIN {mod} · {meta.get("weight", "")} OF THE EXAM · {len(sessions)} SESSIONS</span>
  <h1>{html.escape(meta['title'])}<i>.</i></h1>
  <p class="lede">{inline(meta.get('lede', ''))}</p>
  <div class="dl"><a class="btn" href="#{slug(sessions[0]["num"])}">Start session {sessions[0]["num"]} →</a> {dl}</div>
</header>
<div class="wrap layout">
  <aside class="toc" aria-label="Sessions"><p>In this module</p><ol>{side}</ol></aside>
  <div class="content">
{"".join(body)}
  <div class="pager">{prev}{nxt}</div>
  </div>
</div>
</main>
'''
    page += FOOT
    d = os.path.join(SITE, f"module-{mod}"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)


def write_script(meta, sessions):
    cells = [(s, b) for s in sessions for b in s["blocks"] if b["t"] == "python"]
    if not cells:
        return
    mod = meta["module"]
    o = [f"# {COURSE} — Module {mod}: {meta['title']}", f"# {BASE}module-{mod}/",
         "# Plain Python 3, no extra packages. Run it top to bottom.", ""]
    last = None
    for s, b in cells:
        if s is not last:
            o += ["", "# " + "=" * 76, f"# Session {s['num']} — {s['title']}", "# " + "=" * 76]
            last = s
        code = b["code"]
        if b["opts"].get("eval") == "false":
            code = "\n".join("# " + l if l.strip() else l for l in code.split("\n"))
        o += ["", code]
    d = os.path.join(SITE, "code"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"module-{mod}.py"), "w", encoding="utf-8").write("\n".join(o) + "\n")


def main():
    from hub import PLAN, render_hub
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "content")) if re.match(r"m\d\.md$", f))
    mods = {int(m["module"]): (m, ss) for m, ss in (parse(os.path.join(ROOT, "content", f)) for f in files)}
    outline = [{**p, "live": p["module"] in mods,
                "sessions": [{"num": s["num"], "title": s["title"], "id": slug(s["num"])} for s in mods[p["module"]][1]]
                if p["module"] in mods else p["sessions"]} for p in PLAN]
    want = [int(a) for a in sys.argv[1:]] or sorted(mods)
    for k in want:
        meta, sessions = mods[k]
        res = run_python(sessions)
        render_module(meta, sessions, res, outline)
        write_script(meta, sessions)
        kinds = {}
        for s in sessions:
            for b in s["blocks"]:
                kinds[b["t"]] = kinds.get(b["t"], 0) + 1
        print(f"module {k}: {len(sessions)} sessions · " + ", ".join(f"{v} {k2}" for k2, v in sorted(kinds.items())))
    counts = {"python": 0, "prompt": 0, "quiz": 0, "anim": 0, "file": 0}
    for _, ss in mods.values():
        for s in ss:
            for b in s["blocks"]:
                if b["t"] == "python" and b["opts"].get("eval") == "false":
                    counts["file"] += 1                      # API snippets shown, not run
                elif b["t"] in ("python", "prompt", "quiz", "file"):
                    counts[b["t"]] += 1
                if b["t"] in ("chat", "flow", "anatomy", "compare", "screen", "seq"):
                    counts["anim"] += 1
    render_hub(outline, counts, head, FOOT, inline, slug, SITE)


if __name__ == "__main__":
    main()
