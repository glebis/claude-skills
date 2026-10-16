"""Check a style's fonts (installed + Cyrillic) or install fonts from a folder into ~/Library/Fonts.

python3 fonts.py check godard-riso [--tokens design.tokens.json]
python3 fonts.py install /path/to/fonts            # copies .ttf/.otf, named by PostScript name
Palmier needs fonts installed system-wide; a missing glyph silently falls back to another face (e.g. Futura
Condensed / Futura Medium / Gill Sans have no Cyrillic). Always render a sample after installing.
"""
import glob, os, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
from palmier import cyrillic_ok

if sys.argv[1] == 'install':
    from fontTools.ttLib import TTFont
    for f in glob.glob(os.path.join(sys.argv[2], '**', '*.[ot]tf'), recursive=True):
        n = TTFont(f)['name'].getDebugName(6); dst = os.path.expanduser(f'~/Library/Fonts/{n}{os.path.splitext(f)[1]}')
        if not os.path.exists(dst): shutil.copy(f, dst); print('installed', n)
else:
    from style import load_style
    tok = sys.argv[sys.argv.index('--tokens') + 1] if '--tokens' in sys.argv else None
    st = load_style(sys.argv[2], tok); bad = 0
    for role, f in st['fonts'].items():
        ok = bool(f['ps']) and cyrillic_ok(f['ps'])
        print(f"{role:8s} {f.get('family')} {f.get('weight', '')} -> {f['ps']}  cyrillic={'ok' if ok else 'MISSING'}"); bad += not ok
    sys.exit(1 if bad else 0)
