#!/usr/bin/env python3
"""Pluggable image transform pipeline for cover art.

A pipeline is a JSON list of steps, each {"op": NAME, ...args}. Steps run in
order, each reading the previous output. Brand profiles declare pipelines per
slot (brands/<name>.json -> "transforms"), so a new lab never needs code
changes for a new look — only a new list of steps.

Built-in ops (all ImageMagick 7 `magick`):
  recolor   {"map": {"#src": "#dst", ...}, "fuzz": 30}   swap colours (fuzzy)
  level     {"black": "0%", "white": "55%"}              brighten / crush
  negate    {}                                           invert
  key_out   {"color": "#f3f0e8", "fuzz": 10}             colour -> transparent
  trim      {}                                           crop to content
  resize    {"width": 1200}                              keep aspect
  grain     {"amount": 4}                                riso-style noise
  halftone  {"pattern": "h6x6o"}                         ordered-dither dots
  magick    {"args": ["-modulate", "100,120"]}           raw magick args between in/out
Escape hatches for anything else:
  shell     {"cmd": "some-tool {in} {out}"}              any command; {in}/{out} quoted
  python    {"file": "path.py", "func": "transform"}     func(in_path, out_path, **args)

CLI:
  image_transforms.py IN OUT --pipeline '[{"op":"key_out","color":"#f3f0e8"}]'
  image_transforms.py IN OUT --pipeline-file steps.json
"""
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _magick(*args):
    subprocess.run(["magick", *map(str, args)], check=True)


def op_recolor(src, dst, map=None, fuzz=30):
    args = []
    for frm, to in (map or {}).items():
        args += ["-fuzz", f"{fuzz}%", "-fill", to, "-opaque", frm]
    _magick(src, *args, dst)


def op_level(src, dst, black="0%", white="100%"):
    _magick(src, "-level", f"{black},{white}", dst)


def op_negate(src, dst):
    _magick(src, "-channel", "RGB", "-negate", "+channel", dst)


def op_key_out(src, dst, color="#ffffff", fuzz=10):
    _magick(src, "-alpha", "set", "-fuzz", f"{fuzz}%", "-transparent", color, dst)


def op_trim(src, dst):
    _magick(src, "-trim", "+repage", dst)


def op_resize(src, dst, width=1200):
    _magick(src, "-resize", f"{width}x", dst)


def op_grain(src, dst, amount=4):
    _magick(src, "-attenuate", amount / 10, "+noise", "Gaussian", dst)


def op_halftone(src, dst, pattern="h6x6o"):
    _magick(src, "-ordered-dither", pattern, dst)


def op_magick(src, dst, args=()):
    _magick(src, *args, dst)


def op_shell(src, dst, cmd=""):
    subprocess.run(cmd.format(**{"in": shlex.quote(str(src)), "out": shlex.quote(str(dst))}),
                   shell=True, check=True)


def op_python(src, dst, file="", func="transform", **kw):
    spec = importlib.util.spec_from_file_location("user_transform", Path(file).expanduser())
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    getattr(mod, func)(str(src), str(dst), **kw)


OPS = {name[3:]: fn for name, fn in globals().items() if name.startswith("op_")}


def run_pipeline(src, dst, steps):
    """Apply steps to src, write dst. Empty pipeline = plain copy."""
    src, dst = Path(src), Path(dst)
    if not steps:
        shutil.copyfile(src, dst)
        return dst
    with tempfile.TemporaryDirectory() as tmp:
        cur = src
        for i, step in enumerate(steps):
            step = dict(step)
            name = step.pop("op")
            if name not in OPS:
                raise SystemExit(f"unknown transform op '{name}' (have: {', '.join(sorted(OPS))})")
            out = Path(tmp) / f"step{i}.png"
            OPS[name](cur, out, **step)
            cur = out
        shutil.copyfile(cur, dst)
    return dst


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__); sys.exit(2)
    src, dst = a[0], a[1]
    if "--pipeline" in a:
        steps = json.loads(a[a.index("--pipeline") + 1])
    elif "--pipeline-file" in a:
        steps = json.loads(Path(a[a.index("--pipeline-file") + 1]).read_text())
    else:
        print(__doc__); sys.exit(2)
    print(run_pipeline(src, dst, steps))


if __name__ == "__main__":
    main()
