"""Command-line dispatch for the design-tokens v1 core."""

import argparse
import json
import pathlib
import sys

from . import TokenError
from . import export_css as export_css_mod
from . import export_design_md as design_md_mod
from . import export_preview_html as preview_mod
from . import export_prompt as prompt_mod
from . import import_css as import_css_mod
from . import merge as merge_mod
from . import model
from . import resolve as resolve_mod
from . import serve as serve_mod
from . import validate as validate_mod

_TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "templates" / "base.tokens.json"


def _emit(text, out):
    if out:
        pathlib.Path(out).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def _maybe_serve(args, directory, open_path):
    """Serve previews over HTTP by default when interactive (avoids file:// origin
    breakage). `--serve`/`--no-serve` force it; non-TTY (scripts/CI) defaults off."""
    want = getattr(args, "serve", None)
    if want is None:
        want = sys.stdout.isatty()
    if want:
        serve_mod.serve(directory, open_path, port=getattr(args, "port", None),
                        open_browser=not getattr(args, "no_open", False))


def _add_serve_flags(parser):
    parser.add_argument("--serve", dest="serve", action="store_true", default=None,
                        help="serve the output over HTTP and open it (default: on when interactive)")
    parser.add_argument("--no-serve", dest="serve", action="store_false",
                        help="just write files; do not serve")
    parser.add_argument("--port", type=int, help="port for --serve (default: first free from 8787)")
    parser.add_argument("--no-open", action="store_true", help="serve but do not open a browser")


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
    if args.source:
        # Generate from a previous set: a deterministic, validated clone of an
        # existing token file's structure + content to edit. Insertion order is
        # preserved and serialization is fixed, so a given source always yields
        # byte-identical output.
        src = pathlib.Path(args.source)
        if not src.exists():
            print(f"--from source not found: {src}")
            return 1
        src_errors = validate_mod.validate(model.load(str(src)))
        if src_errors:
            print(f"--from source is not a valid token set: {src}")
            for e in src_errors:
                print(e)
            return 1
        content = json.dumps(
            json.loads(src.read_text(encoding="utf-8")), indent=2, ensure_ascii=False
        ) + "\n"
    else:
        content = _TEMPLATE.read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    errors = validate_mod.validate(model.load(str(dest)))
    if errors:
        for e in errors:
            print(e)
        return 1
    print(f"scaffolded {dest}" + (f" from {args.source}" if args.source else ""))
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
    if args.full:
        html = preview_mod.to_full_preview_html(resolved, name, args.description)
    else:
        html = preview_mod.to_preview_html(resolved, name)
    # Default to a served file when interactive: write next to the source if no
    # -o was given, so the preview opens over http (not file://).
    out = args.out
    if out is None and (getattr(args, "serve", None) or
                        (args.serve is None and sys.stdout.isatty())):
        out = str(pathlib.Path(args.file).with_suffix("").as_posix() + ".preview.html")
    if out:
        pathlib.Path(out).write_text(html, encoding="utf-8")
        print(f"wrote {out}")
        _maybe_serve(args, pathlib.Path(out).resolve().parent, pathlib.Path(out))
    else:
        _emit(html, None)
    return 0


def _cmd_prompt(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    name = args.name or pathlib.Path(args.file).stem
    targets = ["gpt-image-2", "nano-banana", "tufte"] if args.target == "all" else [args.target]
    chunks = []
    for target in targets:
        if target == "tufte":
            chunks.append(prompt_mod.to_tufte_theme(resolved, name))
        else:
            chunks.append(prompt_mod.to_image_prompts(
                resolved, name, target, presets=args.preset,
                platform=args.platform, subject=args.subject,
            ))
    _emit("\n".join(chunks), args.out)
    return 0


def _cmd_serve(args):
    path = pathlib.Path(args.path)
    if not path.exists():
        print(f"not found: {path}")
        return 1
    if path.is_dir():
        directory, open_path = path, None
    else:
        directory, open_path = path.parent, path
    serve_mod.serve(directory, open_path, port=args.port, open_browser=not args.no_open)
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
    (out_dir / "preview-full.html").write_text(
        preview_mod.to_full_preview_html(resolved, name, args.description), encoding="utf-8"
    )
    # Bridge artifacts: tokens -> downstream generation (the prompt door).
    image_prompts = "\n".join(
        prompt_mod.to_image_prompts(resolved, name, t)
        for t in ("gpt-image-2", "nano-banana")
    )
    (out_dir / "image-prompts.md").write_text(image_prompts, encoding="utf-8")
    (out_dir / "tufte-theme.css").write_text(
        prompt_mod.to_tufte_theme(resolved, name), encoding="utf-8"
    )
    print(
        f"wrote {out_dir / 'tokens.css'}, {out_dir / 'DESIGN.md'}, "
        f"{out_dir / 'preview.html'}, {out_dir / 'preview-full.html'}, "
        f"{out_dir / 'image-prompts.md'} and {out_dir / 'tufte-theme.css'}"
    )
    _maybe_serve(args, out_dir, out_dir / "preview-full.html")
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
    ss.add_argument("--from", dest="source",
                    help="generate from an existing token set (deterministic validated clone)")
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
    sp.add_argument("--full", action="store_true",
                    help="render a full landing-page mockup (brand in situ) instead of a swatch sheet")
    sp.add_argument("--description", help="lede/about copy for --full")
    sp.add_argument("-o", "--out")
    _add_serve_flags(sp)
    sp.set_defaults(func=_cmd_preview)

    spr = sub.add_parser("prompt", help="emit generation prompts / theme from tokens")
    spr.add_argument("file")
    spr.add_argument("--target", choices=["gpt-image-2", "nano-banana", "tufte", "all"],
                     default="all")
    spr.add_argument("--preset", action="append",
                     help="override curated presets (image targets; repeatable)")
    spr.add_argument("--platform", default="square")
    spr.add_argument("--subject", help="override the brand mood-board subject")
    spr.add_argument("--name")
    spr.add_argument("-o", "--out")
    spr.set_defaults(func=_cmd_prompt)

    su = sub.add_parser("use")
    su.add_argument("file")
    su.add_argument("--name")
    su.add_argument("--description")
    su.add_argument("--out-dir")
    _add_serve_flags(su)
    su.set_defaults(func=_cmd_use)

    sserve = sub.add_parser("serve", help="serve a file or directory over HTTP and open it")
    sserve.add_argument("path", help="a generated .html file or an output directory")
    sserve.add_argument("--port", type=int)
    sserve.add_argument("--no-open", action="store_true")
    sserve.set_defaults(func=_cmd_serve)

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
