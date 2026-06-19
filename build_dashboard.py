"""
build_dashboard.py — regenerate the dashboard index.html from experiments.json.

The dashboard is the running log of experiments: each entry shows the date it was
run, a title, tags, a short summary, and a link to its full report. To add an
experiment, append an entry to experiments.json and re-run this script.

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
    <span class="date">{html.escape(e.get('date',''))}</span>
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
    exps = sorted(d.get('experiments', []), key=lambda e: e.get('date', ''), reverse=True)
    cards = '\n'.join(card(e) for e in exps)
    n = len(exps)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(d.get('title','Dashboard'))}</title>
<style>
 :root{{--bg:#ffffff;--panel:#f7f8fa;--border:#e3e6ea;--muted:#667085;--accent:#2d5cff}}
 *{{box-sizing:border-box}}
 body{{font:15px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:var(--bg);color:#1c1e21}}
 header{{padding:40px 24px 28px;background:linear-gradient(180deg,#f4f6fb,#fdfefe);border-bottom:1px solid var(--border)}}
 .wrap{{max-width:1000px;margin:0 auto}}
 header h1{{margin:0;font-size:26px;letter-spacing:-.3px}}
 header p{{margin:10px 0 0;color:var(--muted);font-size:15px;max-width:760px}}
 .meta{{margin-top:16px;color:var(--muted);font-size:13px}}
 main{{padding:26px 24px 60px}}
 .grid{{display:grid;grid-template-columns:1fr;gap:16px}}
 @media(min-width:760px){{.grid{{grid-template-columns:1fr 1fr}}}}
 .card{{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:18px 18px 14px;display:flex;flex-direction:column}}
 .cardtop{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
 .date{{color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums}}
 .status{{margin-left:auto;font-size:11px;color:#fff;padding:2px 9px;border-radius:10px;text-transform:uppercase;letter-spacing:.5px}}
 .card h2{{margin:2px 0 8px;font-size:17px;line-height:1.35}}
 .card h2 a{{color:#16213a;text-decoration:none}} .card h2 a:hover{{color:var(--accent)}}
 .summary{{margin:0 0 10px;color:#3a4150;font-size:13.5px;flex:1}}
 .findings{{margin:0 0 12px;padding:8px 10px;background:#f3f6ff;border-left:3px solid var(--accent);border-radius:4px;font-size:13px;color:#22304d}}
 .tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}}
 .tag{{font-size:11px;color:#4a5160;background:#eef1f5;border:1px solid var(--border);border-radius:10px;padding:2px 8px}}
 .cardfoot{{border-top:1px solid var(--border);padding-top:10px}}
 .open{{color:var(--accent);text-decoration:none;font-size:13px;font-weight:600}} .open:hover{{text-decoration:underline}}
 .open.disabled{{color:#98a2b3;font-weight:400}}
 footer{{text-align:center;color:#98a2b3;font-size:12px;padding:24px}}
 footer a{{color:#667085}}
</style></head><body>
<header><div class="wrap">
  <h1>{html.escape(d.get('title','Dashboard'))}</h1>
  <p>{html.escape(d.get('subtitle',''))}</p>
  <div class="meta">{n} experiment{'s' if n!=1 else ''} logged &nbsp;·&nbsp; newest first</div>
</div></header>
<main><div class="wrap"><div class="grid">
{cards}
</div></div></main>
<footer>InterpUpdates · generated from experiments.json ·
 <a href="https://github.com/EdwardoSunny/InterpUpdates">source</a></footer>
</body></html>"""
    out = os.path.join(HERE, 'index.html')
    with open(out, 'w') as f:
        f.write(page)
    print(f'Wrote {out} ({n} experiments)')


if __name__ == '__main__':
    main()
