"""
check_site.py — local validator for the dashboard + reports.

Checks, with no server:
  - every relative href/src in every .html resolves to a file that exists
  - dashboard only links reports that exist (and links the ones that do)
  - each report's tab count == panel count == show(i) handler count (tabs wired)
  - each report has the shared Setup panel and a back-link to the dashboard
  - experiments.json is valid and each entry's report path is consistent

Exit code 0 = all good; non-zero = problems (printed). Run from anywhere:
  python /workspace-vast/$USER/website/check_site.py
"""
import json, os, re, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
errors, warns, oks = [], [], []


def rel_links(text):
    return re.findall(r'(?:href|src)="([^"]+)"', text)


def check_links():
    for hf in glob.glob(os.path.join(HERE, '**', '*.html'), recursive=True):
        text = open(hf).read()
        base = os.path.dirname(hf)
        for link in rel_links(text):
            if link.startswith(('http://', 'https://', '#', 'mailto:', 'data:', 'javascript:')):
                continue
            target = os.path.normpath(os.path.join(base, link.split('#')[0]))
            if not os.path.exists(target):
                errors.append(f"BROKEN LINK  {os.path.relpath(hf, HERE)} -> {link}")


def check_reports():
    for rep in glob.glob(os.path.join(HERE, 'reports', '*', 'index.html')):
        name = os.path.relpath(rep, HERE)
        t = open(rep).read()
        tabs = len(re.findall(r'class="tab[ "]', t))
        panels = len(re.findall(r'class="panel[ "]', t))
        shows = len(set(re.findall(r'onclick="show\((\d+)\)"', t)))
        if not (tabs == panels == shows) and tabs:
            errors.append(f"TAB/PANEL MISMATCH  {name}: tabs={tabs} panels={panels} show()={shows}")
        elif tabs:
            oks.append(f"{name}: {tabs} tabs wired")
        if 'class="setup"' not in t:
            warns.append(f"NO SETUP PANEL  {name}")
        if '../../index.html' not in t:
            warns.append(f"NO BACK-LINK  {name}")


def check_manifest():
    mf = os.path.join(HERE, 'experiments.json')
    try:
        d = json.load(open(mf))
    except Exception as e:
        errors.append(f"experiments.json invalid: {e}"); return
    for e in d.get('experiments', []):
        rep = e.get('report')
        exists = rep and os.path.exists(os.path.join(HERE, rep))
        dash = open(os.path.join(HERE, 'index.html')).read()
        title = e['title']
        if exists and rep not in dash:
            warns.append(f"manifest: '{title}' report exists but not linked in dashboard")
        oks.append(f"manifest: {e['id']} ({e.get('status')}) report={'live' if exists else 'pending'}")


def main():
    if not os.path.exists(os.path.join(HERE, 'index.html')):
        print('FATAL: dashboard index.html missing'); sys.exit(2)
    check_links(); check_reports(); check_manifest()
    print('=== site check ===')
    for o in oks: print('  ok   ', o)
    for w in warns: print('  WARN ', w)
    for e in errors: print('  ERR  ', e)
    print(f'\n{len(errors)} errors, {len(warns)} warnings')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
