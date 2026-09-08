"""
build_dashboard.py — regenerate the dashboard index.html from experiments.json.

Layout
  Level 1 (research threads, sticky tab bar):
    - Emergent Misalignment  : current work (this manifest); inside it a model selector
                               (Qwen3.5-9B | Llama-3.1-8B-Instruct | All) shows one dashboard per model,
                               cards in pipeline order (training sweep -> depth profile -> attribution -> ablations)
    - IMDB sentiment shortcut: the earlier thread, cards from the archived manifest (old/experiments.json)
    - Earlier EM results     : the pre-2026-08-02 EM reports from the archived dashboard
  Entries may carry "model" ("qwen"|"llama") and "stage" (int); both are inferred from id/tags when
  missing so publishers that upsert entries without them still land in the right place.
  Selection (thread + model) is remembered in localStorage and linkable: #em/llama, #sentiment, #archive.

Usage:
  python build_dashboard.py            # reads ./experiments.json (+ ./old/experiments.json), writes ./index.html
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

STATUS = {
    'done':     ('#1f7a3d', 'done'),
    'running':  ('#8a6d00', 'running'),
    'wip':      ('#8a6d00', 'in progress'),
    'planned':  ('#3a4150', 'planned'),
    'archived': ('#4a2030', 'archived'),
}
MODELS = [
    ('qwen',  'Qwen3.5-9B',            'The original dissection: sparse-mask EM training sweep, depth profile, MCQ attribution, ablation ceilings with free-form and insecure-code validation.'),
    ('llama', 'Llama-3.1-8B-Instruct', 'The same pipeline reproduced on Llama, with Transluce’s independently produced neuron descriptions as a ground-truth column on every neuron card.'),
    ('all',   'All',                   'Every report for both models, in pipeline order.'),
]
STAGES = [  # (id pattern, stage number, label shown on the card)
    (r'mask-sweep',      10, 'Step 1 · Training sweep'),
    (r'single-layer',    20, 'Step 2 · Depth profile'),
    (r'mcq-attribution', 30, 'Step 3 · Attribution'),
    (r'ablation-all',    40, 'Step 4 · Ablation, all layers'),
    (r'ablation-layer',  50, 'Step 4 · Ablation, mask layer'),
]
MODEL_BADGE = {'qwen': ('Qwen3.5-9B', '#2b5fa8'), 'llama': ('Llama-3.1-8B', '#7a3f9a')}


def model_of(e):
    m = (e.get('model') or '').lower()
    if m in ('qwen', 'llama'):
        return m
    blob = ' '.join([e.get('id', ''), e.get('title', '')] + list(e.get('tags', []))).lower()
    return 'llama' if 'llama' in blob else 'qwen'


def stage_of(e):
    if isinstance(e.get('stage'), (int, float)):
        s = e['stage']; lab = next((l for _, n, l in STAGES if n == s), '')
        return s, lab
    for pat, n, lab in STAGES:
        if re.search(pat, e.get('id', '')):
            return n, lab
    return 90, ''


def group_of(e):
    if e.get('group'):
        return e['group']
    i = e.get('id', '')
    return 'em' if (i.startswith('em') or i == 'emergent-misalignment') else 'sentiment'


def card(e, base='', show_model=False, show_stage=True):
    color, label = STATUS.get(e.get('status', 'done'), STATUS['done'])
    tags = ''.join(f'<span class="tag">{html.escape(t)}</span>' for t in e.get('tags', [])[:9])
    link = e.get('report')
    if link and base and not link.startswith(base):
        link = base + link
    have = bool(link) and os.path.exists(os.path.join(HERE, link))
    title = html.escape(e['title'])
    title_html = f'<a href="{html.escape(link)}">{title}</a>' if have else title
    if have:
        report_btn = f'<a class="open" href="{html.escape(link)}">open report &rarr;</a>'
    elif link:
        report_btn = '<span class="open disabled">report generating&hellip;</span>'
    else:
        report_btn = '<span class="open disabled">no report</span>'
    chips = ''
    if show_stage:
        _, lab = stage_of(e)
        if lab: chips += f'<span class="chip stage">{html.escape(lab)}</span>'
    if show_model:
        name, col = MODEL_BADGE[model_of(e)]
        chips += f'<span class="chip model" style="background:{col}">{html.escape(name)}</span>'
    return f"""<div class="card">
  <div class="cardtop">{chips}<span class="date">{html.escape(e.get('datetime', e.get('date','')))}</span>
    <span class="status" style="background:{color}">{label}</span></div>
  <h2>{title_html}</h2>
  <p class="summary">{html.escape(e.get('summary',''))}</p>
  {f'<p class="findings"><b>Key result:</b> {html.escape(e["findings"])}</p>' if e.get('findings') else ''}
  <div class="tags">{tags}</div>
  <div class="cardfoot">{report_btn}</div>
</div>"""


def grid(cards, empty='No reports here yet.'):
    return '<main class="grid">' + ('\n'.join(cards) or f'<p class="muted">{empty}</p>') + '</main>'


def main():
    d = json.load(open(os.path.join(HERE, 'experiments.json')))
    exps = d.get('experiments', [])
    old_path = os.path.join(HERE, 'old', 'experiments.json')
    old = json.load(open(old_path)).get('experiments', []) if os.path.exists(old_path) else []
    for e in old:
        e.setdefault('status', 'archived')
    old_sent = [e for e in old if group_of(e) == 'sentiment']
    old_em = [e for e in old if group_of(e) == 'em']
    for lst in (old_sent, old_em):
        lst.sort(key=lambda e: e.get('datetime', e.get('date', '')), reverse=True)

    by = {'qwen': [], 'llama': []}
    for e in exps:
        by[model_of(e)].append(e)
    for k in by:
        by[k].sort(key=lambda e: (stage_of(e)[0], e.get('datetime', e.get('date', ''))))

    # ---- EM thread: model selector + per-model dashboards ----
    mtabs, mpanels = [], []
    for k, (m, label, blurb) in enumerate(MODELS):
        cnt = len(by['qwen']) + len(by['llama']) if m == 'all' else len(by[m])
        mtabs.append(f'<button class="seg" id="seg-{m}" onclick="pick(\'{m}\',this)">{html.escape(label)}<span class="cnt">{cnt}</span></button>')
        if m == 'all':
            body = ''.join(f'<h3 class="modelhdr"><span class="dot" style="background:{MODEL_BADGE[mm][1]}"></span>{html.escape(lbl)}</h3>'
                           + grid([card(e) for e in by[mm]]) for mm, lbl, _ in MODELS[:2])
        else:
            body = grid([card(e) for e in by[m]], 'No reports for this model yet.')
        mpanels.append(f'<div class="mpanel" id="m-{m}"{"" if k==0 else " hidden"}><p class="blurb">{html.escape(blurb)}</p>{body}</div>')
    em_panel = (f'<div class="segwrap"><span class="seglabel">Model</span><div class="segmented">{"".join(mtabs)}</div></div>'
                + ''.join(mpanels))

    # ---- other threads ----
    sent_panel = ('<p class="blurb">The earlier thread on the IMDB sentiment shortcut (archived 2026-08-02). Reports open in the previous dashboard’s layout.</p>'
                  + grid([card(e, base='old/', show_stage=False) for e in old_sent], 'No archived sentiment reports found.'))
    arch_panel = ('<p class="blurb">Emergent-misalignment reports from before the dashboard rebuild on 2026-08-02, kept for reference. '
                  f'<a href="old/index.html">Open the previous dashboard as it was &rarr;</a></p>'
                  + grid([card(e, base='old/', show_stage=False) for e in old_em], 'No archived EM reports found.'))
    THREADS = [('em', 'Emergent Misalignment', len(exps), em_panel),
               ('sentiment', 'IMDB sentiment shortcut', len(old_sent), sent_panel),
               ('archive', 'Earlier EM results', len(old_em), arch_panel)]
    tabs_html = '\n'.join(f'<button class="tab{" active" if k==0 else ""}" id="tab-{g}" onclick="show(\'{g}\',this)">{html.escape(lbl)} <span class="cnt">{cnt}</span></button>'
                          for k, (g, lbl, cnt, _) in enumerate(THREADS))
    panels_html = '\n'.join(f'<div class="group" id="g-{g}"{"" if k==0 else " hidden"}>{body}</div>' for k, (g, _, _, body) in enumerate(THREADS))
    n_reports = len(exps) + len(old)

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(d.get('title','Dashboard'))}</title>
<link rel="stylesheet" href="assets/theme.css">
<style>
header.page .counts{{display:flex;gap:22px;flex-wrap:wrap;margin-top:14px}}
header.page .counts div{{font-size:12.5px;color:var(--text-muted)}}
header.page .counts b{{display:block;font-size:20px;color:var(--text-primary);font-variant-numeric:tabular-nums;letter-spacing:-.3px}}
.group{{max-width:1120px;margin:0 auto;padding:0 24px 48px}}
.group main.grid{{padding:14px 0 8px}}
.blurb{{margin:16px 0 4px;color:var(--text-secondary);font-size:14px;max-width:900px}}
.segwrap{{display:flex;align-items:center;gap:12px;margin:18px 0 2px;flex-wrap:wrap}}
.seglabel{{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--text-muted)}}
.segmented{{display:inline-flex;background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:3px;gap:3px}}
.seg{{background:transparent;border:0;border-radius:8px;padding:7px 14px;font:inherit;font-size:13.5px;color:var(--text-secondary);cursor:pointer;transition:.12s}}
.seg:hover{{color:var(--accent)}} .seg.active{{background:var(--surface-1);color:var(--text-primary);box-shadow:0 1px 2px rgba(0,0,0,.12);font-weight:600}}
.seg .cnt{{margin-left:7px;font-size:11px;color:var(--text-muted);font-weight:500}}
.modelhdr{{display:flex;align-items:center;gap:8px;font-size:14px;margin:22px 0 -4px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.5px}}
.modelhdr .dot{{width:9px;height:9px;border-radius:50%;display:inline-block}}
.chip{{font-size:10.5px;padding:2px 8px;border-radius:9px;letter-spacing:.3px;white-space:nowrap}}
.chip.stage{{background:var(--surface-2);color:var(--text-secondary);border:1px solid var(--border)}}
.chip.model{{color:#fff}}
.cardtop{{gap:8px;flex-wrap:wrap}} .cardtop .date{{margin-left:auto}}
.muted{{color:var(--text-muted)}}
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
  <div class="counts"><div><b>{len(by['qwen'])}</b>Qwen3.5-9B reports</div><div><b>{len(by['llama'])}</b>Llama-3.1-8B reports</div><div><b>{len(old_sent)}</b>sentiment-shortcut reports</div><div><b>{len(old_em)}</b>earlier EM reports</div></div>
</div></header>
<div class="tabs">
{tabs_html}
</div>
{panels_html}
<footer>InterpUpdates · generated from experiments.json · {n_reports} reports ·
 <a href="https://github.com/EdwardoSunny/InterpUpdates">source</a> · <a href="old/index.html">previous dashboard</a></footer>
<script>
var THREADS=['em','sentiment','archive'], MODELS=['qwen','llama','all'];
function save(k,v){{try{{localStorage.setItem(k,v);}}catch(e){{}}}}
function load(k){{try{{return localStorage.getItem(k);}}catch(e){{return null;}}}}
function sync(){{var g=document.querySelector('.tabs .tab.active').id.slice(4), m=(document.querySelector('.seg.active')||{{id:'seg-qwen'}}).id.slice(4);
  if(history.replaceState) history.replaceState(null,'','#'+(g==='em'?'em/'+m:g));}}
function show(g,btn){{
  document.querySelectorAll('.group').forEach(function(x){{x.hidden=(x.id!=='g-'+g);}});
  document.querySelectorAll('.tabs .tab').forEach(function(b){{b.classList.remove('active');}});
  (btn||document.getElementById('tab-'+g)).classList.add('active'); save('iu-thread',g); sync();}}
function pick(m,btn){{
  document.querySelectorAll('.mpanel').forEach(function(x){{x.hidden=(x.id!=='m-'+m);}});
  document.querySelectorAll('.seg').forEach(function(b){{b.classList.remove('active');}});
  (btn||document.getElementById('seg-'+m)).classList.add('active'); save('iu-model',m); sync();}}
(function(){{
  var h=(location.hash||'').replace('#',''), g=h.split('/')[0], m=h.split('/')[1];
  if(THREADS.indexOf(g)<0) g=load('iu-thread')||'em'; if(THREADS.indexOf(g)<0) g='em';
  if(MODELS.indexOf(m)<0) m=load('iu-model')||'qwen'; if(MODELS.indexOf(m)<0) m='qwen';
  pick(m); show(g);
}})();
</script>
</body></html>"""
    with open(os.path.join(HERE, 'index.html'), 'w') as f:
        f.write(page)
    print(f'Wrote index.html: em {len(exps)} (qwen {len(by["qwen"])}, llama {len(by["llama"])}), sentiment {len(old_sent)}, earlier em {len(old_em)}')


if __name__ == '__main__':
    main()
