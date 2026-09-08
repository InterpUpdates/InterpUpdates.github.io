"""
build_dashboard.py — regenerate the dashboard index.html from experiments.json.

Layout: a model selector at the top (Qwen3.5-9B | Llama-3.1-8B-Instruct | all), then one
dashboard per model with its report cards in pipeline order (training sweep -> single-layer
depth profile -> MCQ attribution -> ablation budget sweeps). Each experiment entry may carry
"model" ("qwen" | "llama") and "stage" (int, lower = earlier in the pipeline); both are
inferred from the id/tags when missing, so publishers that upsert entries without them still
land in the right place. The selection is remembered (localStorage) and linkable (#qwen/#llama).

Usage:
  python build_dashboard.py            # reads ./experiments.json, writes ./index.html
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

STATUS = {
    'done':       ('#1f7a3d', 'done'),
    'running':    ('#8a6d00', 'running'),
    'wip':        ('#8a6d00', 'in progress'),
    'planned':    ('#3a4150', 'planned'),
    'archived':   ('#4a2030', 'archived'),
}

MODELS = [
    ('qwen',  'Qwen3.5-9B',            'Original dissection: sparse-mask EM sweep, attribution, ablation ceilings, free-form + insecure-code validation.'),
    ('llama', 'Llama-3.1-8B-Instruct', 'Reproduction of the same pipeline on Llama, plus Transluce ground-truth neuron descriptions on the cards.'),
    ('all',   'All',                   'Every report, both models.'),
]

# pipeline order for the cards inside a model's dashboard (lower first)
STAGE_RULES = [
    (r'mask-sweep', 10), (r'single-layer', 20), (r'mcq-attribution', 30),
    (r'ablation-all', 40), (r'ablation-layer', 50),
]


def model_of(e):
    m = (e.get('model') or '').lower()
    if m in ('qwen', 'llama'):
        return m
    i = e.get('id', '').lower(); tags = ' '.join(e.get('tags', [])).lower(); title = e.get('title', '').lower()
    return 'llama' if ('llama' in i or 'llama' in tags or 'llama' in title) else 'qwen'


def stage_of(e):
    if isinstance(e.get('stage'), (int, float)):
        return e['stage']
    i = e.get('id', '')
    for pat, s in STAGE_RULES:
        if re.search(pat, i):
            return s
    return 90


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
    exps = d.get('experiments', [])
    n = len(exps)
    by = {'qwen': [], 'llama': []}
    for e in exps:
        by[model_of(e)].append(e)
    for k in by:
        by[k].sort(key=lambda e: (stage_of(e), e.get('datetime', e.get('date', ''))))
    by['all'] = by['qwen'] + by['llama']

    tabs, panels = [], []
    for k, (m, label, blurb) in enumerate(MODELS):
        cnt = len(by[m])
        tabs.append(f'<button class="tab{" active" if k==0 else ""}" id="tab-{m}" onclick="show(\'{m}\',this)">'
                    f'{html.escape(label)} <span class="cnt">{cnt}</span></button>')
        if m == 'all':
            grid = ''.join(f'<h2 class="modelhdr">{html.escape(lbl)}</h2><main class="grid">' + '\n'.join(card(e) for e in by[mm]) + '</main>'
                           for mm, lbl, _ in MODELS[:2])
        else:
            grid = '<main class="grid">' + ('\n'.join(card(e) for e in by[m]) or '<p class="muted">No reports for this model yet.</p>') + '</main>'
        panels.append(f'<div class="group" id="g-{m}"{"" if k==0 else " hidden"}>'
                      f'<p class="meta modelblurb">{html.escape(blurb)}</p>{grid}</div>')
    tabs_html = '\n'.join(tabs)
    panels_html = '\n'.join(panels)

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(d.get('title','Dashboard'))}</title>
<link rel="stylesheet" href="assets/theme.css">
<style>
.modelsel{{margin:6px 0 2px}} .modelsel .tab{{font-size:15px;padding:10px 18px}}
.modelblurb{{margin:10px 0 14px}} .modelhdr{{font-size:16px;margin:18px 0 8px;opacity:.85}}
</style>
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
  <div class="meta">Pick a model, then read the cards top to bottom: training sweep &rarr; depth profile &rarr; attribution &rarr; ablation budget sweeps. &nbsp;{len(by['qwen'])} Qwen &nbsp;&middot;&nbsp; {len(by['llama'])} Llama reports</div>
  {('<p class="meta"><a href="' + d['archive']['href'] + '">' + html.escape(d['archive']['label']) + '</a></p>') if d.get('archive') else ''}
</div></header>
<div class="tabs modelsel">
{tabs_html}
</div>
{panels_html}
<footer>InterpUpdates · generated from experiments.json ·
 <a href="https://github.com/EdwardoSunny/InterpUpdates">source</a></footer>
<script>
function show(m, btn){{
  document.querySelectorAll('.group').forEach(x=>x.hidden = (x.id !== 'g-'+m));
  document.querySelectorAll('.modelsel .tab').forEach(b=>b.classList.remove('active'));
  (btn || document.getElementById('tab-'+m)).classList.add('active');
  try {{ localStorage.setItem('iu-model', m); }} catch(e) {{}}
  if (history.replaceState) history.replaceState(null, '', '#'+m);
}}
(function(){{
  var m = (location.hash || '').replace('#','');
  if (!['qwen','llama','all'].includes(m)) {{ try {{ m = localStorage.getItem('iu-model') || 'qwen'; }} catch(e) {{ m = 'qwen'; }} }}
  if (!['qwen','llama','all'].includes(m)) m = 'qwen';
  show(m);
}})();
</script>
</body></html>"""
    out = os.path.join(HERE, 'index.html')
    with open(out, 'w') as f:
        f.write(page)
    print(f'Wrote {out} ({n} experiments: {len(by["qwen"])} qwen, {len(by["llama"])} llama)')


if __name__ == '__main__':
    main()
