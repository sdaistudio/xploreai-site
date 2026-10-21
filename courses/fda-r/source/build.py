#!/usr/bin/env python3
"""Build the Financial Data Analytics using R course pages.

content/mN.md  ->  run R chunks (runner.R)  ->  courses/fda-r/module-N/index.html
                                               courses/fda-r/code/module-N.R
                                               courses/fda-r/img/*.png
Usage: python3 build.py [N ...]   (no args = all modules, and the course hub)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ROOT)                      # courses/fda-r/
DATA = os.path.join(SITE, "data")
RUN = os.path.join(tempfile.gettempdir(), "fdar-run")
URL = "https://xploreai.co.in/courses/fda-r/data/"


# ---------- parse ----------
def parse(path):
    txt = open(path).read()
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
        if ln.startswith("```r"):
            opts = dict(re.findall(r"(\w+)=([\w.]+)", ln))
            code = []
            i += 1
            while not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            n += 1
            cur["blocks"].append({"t": "code", "code": "\n".join(code).strip("\n"),
                                  "id": f"m{meta['module']}c{n:03d}", "opts": opts})
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
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"\|[\s:-]+\|", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            cur["blocks"].append({"t": "table", "rows": rows}); continue
        if ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(```|#|>|\s*[-*] |\|)", lines[i]):
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


# ---------- run ----------
def run_r(mod, sessions):
    chunks = [{"id": b["id"], "code": b["code"], "eval": b["opts"].get("eval") != "false",
               **({"w": float(b["opts"]["w"])} if "w" in b["opts"] else {}),
               **({"h": float(b["opts"]["h"])} if "h" in b["opts"] else {})}
              for s in sessions for b in s["blocks"] if b["t"] == "code"]
    out = os.path.join(RUN, f"m{mod}")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    cj = os.path.join(out, "chunks.json")
    json.dump(chunks, open(cj, "w"))
    p = subprocess.run(["Rscript", os.path.join(ROOT, "runner.R"), cj, out, DATA],
                       capture_output=True, text=True, cwd=out)
    errs = [l for l in p.stderr.splitlines() if l.startswith("ERROR")]
    if p.returncode or errs:
        print(p.stderr[-3000:]); print("\n".join(errs))
    return out, json.load(open(os.path.join(out, "results.json")))


# ---------- render ----------
HEAD = open(os.path.join(ROOT, "tpl_head.html")).read()
FOOT = open(os.path.join(ROOT, "tpl_foot.html")).read()


def head(title, desc, url):
    desc = re.sub(r"[`*]", "", desc)
    return HEAD.replace("%%TITLE%%", html.escape(title)).replace("%%DESC%%", html.escape(desc)).replace("%%URL%%", url)


def trim_output(s, maxlines=70):
    s = s.rstrip("\n")
    ls = s.split("\n")
    if len(ls) > maxlines:
        ls = ls[:maxlines] + [f"… ({len(ls) - maxlines} more lines in your console)"]
    return "\n".join(ls)


def render_module(meta, sessions, res, mods):
    mod = int(meta["module"])
    imgdir = os.path.join(SITE, "img"); os.makedirs(imgdir, exist_ok=True)
    side = "".join(f'<li><a href="#{slug(s["num"])}"><span>{s["num"]}</span>{html.escape(s["title"])}</a></li>' for s in sessions)
    body = []
    for s in sessions:
        body.append(f'<section class="session" id="{slug(s["num"])}"><p class="snum">Session {s["num"]}</p><h2>{html.escape(s["title"])}</h2>')
        for b in s["blocks"]:
            t = b["t"]
            if t == "p":
                body.append(f"<p>{inline(b['text'])}</p>")
            elif t == "h3":
                body.append(f"<h3>{inline(b['text'])}</h3>")
            elif t == "ul":
                body.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in b["items"]) + "</ul>")
            elif t == "table":
                hd, *rows = b["rows"]
                body.append('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in hd) + "</tr></thead><tbody>"
                            + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")
            elif t == "call":
                label = {"read": "How to read it", "tip": "Tip", "concept": "The idea", "warn": "Watch out", "try": "Try it"}.get(b["kind"], b["kind"])
                paras = "".join(f"<p>{inline(x)}</p>" for x in b["text"].split("\n") if x)
                body.append(f'<aside class="call {b["kind"]}"><b>{label}</b>{paras}</aside>')
            elif t == "code":
                r = res.get(b["id"], {"out": "", "plots": []})
                skipped = b["opts"].get("eval") == "false"
                tag = '<span class="noeval">shown, not run here</span>' if skipped else ""
                body.append(f'<div class="cell"><div class="code"><div class="lab"><span>R</span>{tag}<button class="copy" type="button">Copy</button></div>'
                            f'<pre><code class="language-r">{html.escape(b["code"])}</code></pre></div>')
                outtxt = trim_output(r["out"]) if r["out"] and b["opts"].get("echo") != "false" else ""
                if outtxt.strip():
                    body.append(f'<div class="out"><div class="lab"><span>Console output</span></div><pre>{html.escape(outtxt)}</pre></div>')
                for pfile in r["plots"]:
                    shutil.copy(os.path.join(RUN, f"m{mod}", pfile), os.path.join(imgdir, pfile))
                    body.append(f'<figure class="plot"><div class="lab"><span>Plot output</span></div><img src="../img/{pfile}" alt="R plot output for session {s["num"]}" loading="lazy"></figure>')
                body.append("</div>")
        body.append("</section>")
    prev = f'<a class="btn ghost" href="../module-{mod-1}/">← Module {mod-1}</a>' if mod > 1 else '<a class="btn ghost" href="../">← Course home</a>'
    nxt = f'<a class="btn" href="../module-{mod+1}/">Module {mod+1} →</a>' if mod < len(mods) else '<a class="btn" href="../">Course home →</a>'
    page = head(f"Module {mod}: {meta['title']} — Financial Data Analytics using R",
                       meta.get("lede", ""), f"https://xploreai.co.in/courses/fda-r/module-{mod}/")
    page += f'''
<main class="fdar">
<header class="mhero wrap">
  <p class="crumb"><a href="/learn.html">Learn AI</a> / <a href="../">Financial Data Analytics using R</a> / Module {mod}</p>
  <span class="pill">MODULE {mod} OF {len(mods)} · {len(sessions)} SESSIONS</span>
  <h1>{html.escape(meta['title'])}<i>.</i></h1>
  <p class="lede">{inline(meta.get('lede', ''))}</p>
  <div class="dl"><a class="btn" href="../code/module-{mod}.R" download>Download the R script</a> <a class="btn ghost" href="../#data">Get the data</a></div>
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
    open(os.path.join(d, "index.html"), "w").write(page)


def write_script(meta, sessions):
    mod = meta["module"]
    o = [f"# Financial Data Analytics using R — Module {mod}: {meta['title']}",
         f"# https://xploreai.co.in/courses/fda-r/module-{mod}/",
         "# Every data file is read straight from the course site, so this script runs as-is.", ""]
    for s in sessions:
        o += ["", "# " + "=" * 76, f"# Session {s['num']} — {s['title']}", "# " + "=" * 76]
        for b in s["blocks"]:
            if b["t"] == "h3":
                o += ["", f"# --- {b['text']} ---"]
            elif b["t"] == "code":
                code = b["code"]
                if b["opts"].get("eval") == "false":
                    code = "\n".join("# " + l if l.strip() else l for l in code.split("\n"))
                o += ["", code]
    d = os.path.join(SITE, "code"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"module-{mod}.R"), "w").write("\n".join(o) + "\n")


def main():
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "content")) if re.match(r"m\d\.md$", f))
    mods = [parse(os.path.join(ROOT, "content", f)) for f in files]
    want = [int(a) for a in sys.argv[1:]] or [int(m["module"]) for m, _ in mods]
    for meta, sessions in mods:
        if int(meta["module"]) not in want:
            continue
        out, res = run_r(meta["module"], sessions)
        render_module(meta, sessions, res, mods)
        write_script(meta, sessions)
        print(f"module {meta['module']}: {len(sessions)} sessions, {sum(len(r['plots']) for r in res.values())} plots")
    json.dump([{"module": int(m["module"]), "title": m["title"], "lede": m.get("lede", ""),
                "sessions": [{"num": s["num"], "title": s["title"], "id": slug(s["num"])} for s in ss]} for m, ss in mods],
              open(os.path.join(RUN, "outline.json"), "w"), indent=1)
    from hub import render_hub
    ncells = sum(1 for _, ss in mods for x in ss for b in x["blocks"] if b["t"] == "code")
    nplots = len([f for f in os.listdir(os.path.join(SITE, "img")) if f.endswith(".png")])
    render_hub(mods, ncells, nplots, head, FOOT, inline, slug, SITE)


if __name__ == "__main__":
    main()
