"""Command-line dispatch for the design-tokens v1 core."""

import argparse
import json
import pathlib
import sys

from . import TokenError
from . import export_css as export_css_mod
from . import export_design_md as design_md_mod
from . import export_preview_html as preview_mod
from . import import_css as import_css_mod
from . import merge as merge_mod
from . import model
from . import resolve as resolve_mod
from . import validate as validate_mod

_TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "templates" / "base.tokens.json"


def _emit(text, out):
    if out:
        pathlib.Path(out).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def _cmd_validate(args):
    errors = validate_mod.validate(model.load(args.file))
    if errors:
        for e in errors:
            print(e)
        return 1
    print("OK")
    return 0


def _cmd_merge(args):
    merged = merge_mod.merge(model.load(args.base), model.load(args.override))
    _emit(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", args.out)
    return 0


def _cmd_resolve(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    _emit(json.dumps(resolved, indent=2, ensure_ascii=False) + "\n", args.out)
    return 0


def _cmd_export_css(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    _emit(export_css_mod.export_css(resolved, args.selector), args.out)
    return 0


def _cmd_setup_edit(args):
    dest = pathlib.Path(args.dest)
    if dest.exists():
        print(f"refusing to overwrite existing file: {dest}")
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    errors = validate_mod.validate(model.load(str(dest)))
    if errors:
        for e in errors:
            print(e)
        return 1
    print(f"scaffolded {dest}")
    return 0


def _cmd_design_md(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    name = args.name or pathlib.Path(args.file).stem
    _emit(design_md_mod.to_design_md(resolved, name, args.description), args.out)
    return 0


def _cmd_import(args):
    css = pathlib.Path(args.file).read_text(encoding="utf-8")
    tree, skipped = import_css_mod.to_tokens(css)
    errors = validate_mod.validate(tree)
    if errors:
        for e in errors:
            print(e)
        return 1
    out_json = json.dumps(tree, indent=2, ensure_ascii=False) + "\n"
    _emit(out_json, args.out)
    print(f"imported {len(tree)} tokens; skipped {len(skipped)}", file=sys.stderr)
    for name, value, reason in skipped:
        print(f"  skipped --{name}: {reason} ({value})", file=sys.stderr)
    return 0


def _cmd_preview(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    name = args.name or pathlib.Path(args.file).stem
    _emit(preview_mod.to_preview_html(resolved, name), args.out)
    return 0


def _cmd_use(args):
    tree = model.load(args.file)
    errors = validate_mod.validate(tree)
    if errors:
        for e in errors:
            print(e)
        return 1
    resolved = resolve_mod.resolve(tree)
    name = args.name or pathlib.Path(args.file).stem
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else pathlib.Path(args.file).parent / "resolved"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tokens.css").write_text(export_css_mod.export_css(resolved), encoding="utf-8")
    (out_dir / "DESIGN.md").write_text(
        design_md_mod.to_design_md(resolved, name, args.description), encoding="utf-8"
    )
    (out_dir / "preview.html").write_text(
        preview_mod.to_preview_html(resolved, name), encoding="utf-8"
    )
    print(f"wrote {out_dir / 'tokens.css'}, {out_dir / 'DESIGN.md'} and {out_dir / 'preview.html'}")
    return 0


def _build_parser():
    p = argparse.ArgumentParser(prog="tokens", description="design-tokens v1 core")
    sub = p.add_subparsers(dest="command", required=True)

    sv = sub.add_parser("validate")
    sv.add_argument("file")
    sv.set_defaults(func=_cmd_validate)

    sm = sub.add_parser("merge")
    sm.add_argument("base")
    sm.add_argument("override")
    sm.add_argument("-o", "--out")
    sm.set_defaults(func=_cmd_merge)

    sr = sub.add_parser("resolve")
    sr.add_argument("file")
    sr.add_argument("-o", "--out")
    sr.set_defaults(func=_cmd_resolve)

    se = sub.add_parser("export-css")
    se.add_argument("file")
    se.add_argument("--selector", default=":root")
    se.add_argument("-o", "--out")
    se.set_defaults(func=_cmd_export_css)

    ss = sub.add_parser("setup-edit")
    ss.add_argument("dest")
    ss.set_defaults(func=_cmd_setup_edit)

    sd = sub.add_parser("design-md")
    sd.add_argument("file")
    sd.add_argument("--name")
    sd.add_argument("--description")
    sd.add_argument("-o", "--out")
    sd.set_defaults(func=_cmd_design_md)

    si = sub.add_parser("import")
    si.add_argument("file", help="a CSS file with :root custom properties")
    si.add_argument("-o", "--out", help="write DTCG tokens here (default: stdout)")
    si.set_defaults(func=_cmd_import)

    sp = sub.add_parser("preview")
    sp.add_argument("file")
    sp.add_argument("--name")
    sp.add_argument("-o", "--out")
    sp.set_defaults(func=_cmd_preview)

    su = sub.add_parser("use")
    su.add_argument("file")
    su.add_argument("--name")
    su.add_argument("--description")
    su.add_argument("--out-dir")
    su.set_defaults(func=_cmd_use)

    return p


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TokenError as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
