"""
build_dashboard.py — regenerate the dashboard index.html from experiments.json.

Two top-level tabs group the cards by research thread:
  - Emergent Misalignment (group 'em')
  - IMDB sentiment shortcut (group 'sentiment')
Each experiment carries a "group" field; if missing it's inferred from the id
(em* / emergent-misalignment -> em, else sentiment). To add an experiment, append
an entry to experiments.json (with a "group") and re-run this script.

Usage:
  python build_dashboard.py            # reads ./experiments.json, writes ./index.html
"""
import html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

STATUS = {
    'done':       ('#1f7a3d', 'done'),
    'running':    ('#8a6d00', 'running'),
    'wip':        ('#8a6d00', 'in progress'),
    'planned':    ('#3a4150', 'planned'),
    'archived':   ('#4a2030', 'archived'),
}

GROUPS = [
    ('em',        'Emergent Misalignment'),
    ('sentiment', 'IMDB sentiment shortcut'),
]

def group_of(e):
    if e.get('group'):
        return e['group']
    i = e.get('id', '')
    return 'em' if (i.startswith('em') or i == 'emergent-misalignment') else 'sentiment'


def card(e):
    color, label = STATUS.get(e.get('status', 'done'), STATUS['done'])
    tags = ''.join(f'<span class="tag">{html.escape(t)}</span>' for t in e.get('tags', []))
    link = e.get('report')
    have = bool(link) and os.path.exists(os.path.join(HERE, link))
    title = html.escape(e['title'])
    title_html = f'<a href="{html.escape(link)}">{title}</a>' if have else title
    if have:
        report_btn = f'<a class="open" href="{html.escape(link)}">open report &rarr;</a>'
    elif link:
        report_btn = '<span class="open disabled">report generating&hellip;</span>'
    else:
        report_btn = '<span class="open disabled">no report</span>'
    return f"""<div class="card">
  <div class="cardtop">
    <span class="date">{html.escape(e.get('datetime', e.get('date','')))}</span>
    <span class="status" style="background:{color}">{label}</span>
  </div>
  <h2>{title_html}</h2>
  <p class="summary">{html.escape(e.get('summary',''))}</p>
  {f'<p class="findings"><b>Key result:</b> {html.escape(e["findings"])}</p>' if e.get('findings') else ''}
  <div class="tags">{tags}</div>
  <div class="cardfoot">{report_btn}</div>
</div>"""


def main():
    with open(os.path.join(HERE, 'experiments.json')) as f:
        d = json.load(f)
    exps = sorted(d.get('experiments', []),
                  key=lambda e: (e.get('ts', 0), e.get('datetime', e.get('date', ''))), reverse=True)
    n = len(exps)
    by = {g: [e for e in exps if group_of(e) == g] for g, _ in GROUPS}

    tabs, panels = [], []
    for k, (g, label) in enumerate(GROUPS):
        cnt = len(by[g])
        tabs.append(f'<button class="tab{" active" if k==0 else ""}" onclick="show(\'{g}\',this)">'
                    f'{html.escape(label)} <span class="cnt">{cnt}</span></button>')
        grid = '\n'.join(card(e) for e in by[g]) or '<p class="muted">No experiments in this group yet.</p>'
        panels.append(f'<div class="group" id="g-{g}"{"" if k==0 else " hidden"}><main class="grid">{grid}</main></div>')
    tabs_html = '\n'.join(tabs)
    panels_html = '\n'.join(panels)

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(d.get('title','Dashboard'))}</title>
<link rel="stylesheet" href="assets/theme.css">
<script>(function(){{var t=localStorage.getItem('iu-theme');
 if(t)document.documentElement.setAttribute('data-theme',t);}})();
function toggleTheme(){{var r=document.documentElement,
 cur=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'),
 nxt=cur==='dark'?'light':'dark';
 r.setAttribute('data-theme',nxt);localStorage.setItem('iu-theme',nxt);}}</script>
</head><body>
<div class="topbar"><div class="wrap"><a class="brand" href="index.html">InterpUpdates</a>
<span class="spacer"></span>
<button class="themetoggle" onclick="toggleTheme()">theme</button></div></div>
<header class="page"><div class="wrap">
  <h1>{html.escape(d.get('title','Dashboard'))}</h1>
  <p class="sub">{html.escape(d.get('subtitle',''))}</p>
  {('<p class="meta"><a href="' + d['archive']['href'] + '">' + html.escape(d['archive']['label']) + '</a></p>') if d.get('archive') else ''}
  <div class="meta">{len(by['em'])} emergent-misalignment &nbsp;·&nbsp; {len(by['sentiment'])} sentiment-shortcut &nbsp;·&nbsp; newest first</div>
</div></header>
<div class="tabs">
{tabs_html}
</div>
{panels_html}
<footer>InterpUpdates · generated from experiments.json ·
 <a href="https://github.com/EdwardoSunny/InterpUpdates">source</a></footer>
<script>
function show(g, btn){{
  document.querySelectorAll('.group').forEach(x=>x.hidden = (x.id !== 'g-'+g));
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
}}
</script>
</body></html>"""
    out = os.path.join(HERE, 'index.html')
    with open(out, 'w') as f:
        f.write(page)
    print(f'Wrote {out} ({n} experiments: {len(by["em"])} em, {len(by["sentiment"])} sentiment)')


if __name__ == '__main__':
    main()
