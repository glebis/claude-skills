#!/usr/bin/env bash
# Copy the kinetic motion system into a raea project made with `raea project new NAME`.
#   scaffold.sh DEST [--src KINETIC_PROJECT] [--with-sfx]
# Copies components/, the three tools, compositions/glyphs.gen.ts, assets/fonts, package.json and tsconfig.json,
# links compositions/media -> ../assets, then runs npm install. Never overwrites: an existing file is kept and reported.
# --with-sfx also copies the levelled ElevenLabs clips (assets/sounds/sfx); music is never copied (it is per piece).
set -euo pipefail

SRC="${KINETIC_SRC:-$HOME/raea/showreel/projects/kinetic}"
DEST=""; SFX=0
while [ $# -gt 0 ]; do
  case "$1" in
    --src) SRC="$2"; shift 2 ;;
    --with-sfx) SFX=1; shift ;;
    -h|--help) sed -n 2,6p "$0"; exit 0 ;;
    *) DEST="$1"; shift ;;
  esac
done
[ -n "$DEST" ] || { echo "usage: scaffold.sh DEST [--src DIR] [--with-sfx]" >&2; exit 2; }
[ -d "$SRC/components" ] || { echo "no kinetic project at $SRC" >&2; exit 1; }
[ -d "$DEST" ] || { echo "$DEST does not exist: make it with 'raea project new NAME' first" >&2; exit 1; }
DEST="$(cd "$DEST" && pwd)"

copy() { # copy SRC_REL [DEST_REL]: file or directory, keeping what is there
  local from="$SRC/$1" to="$DEST/${2:-$1}"
  if [ -d "$from" ]; then
    mkdir -p "$to"
    for f in "$from"/*; do
      [ -e "$f" ] || continue
      case "$(basename "$f")" in .raea-view*) continue ;; esac
      if [ -e "$to/$(basename "$f")" ]; then echo "kept   ${2:-$1}/$(basename "$f")"; else cp -R "$f" "$to/"; echo "copied ${2:-$1}/$(basename "$f")"; fi
    done
  else
    mkdir -p "$(dirname "$to")"
    if [ -e "$to" ]; then echo "kept   ${2:-$1}"; else cp "$from" "$to"; echo "copied ${2:-$1}"; fi
  fi
}

copy components
copy compositions/glyphs.gen.ts
copy tools/glyph_widths.py
copy tools/kick.py
copy tools/eleven_sfx.py
copy assets/fonts
copy package.json
copy tsconfig.json
[ "$SFX" = 1 ] && copy assets/sounds/sfx
# the skill's own parts: Board (many slides at once, camera moves between them) and its demo
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
for f in components/board.tsx examples/board-demo.tsx; do
  to="$DEST/$( [ "$f" = examples/board-demo.tsx ] && echo compositions/board-demo.tsx || echo "$f" )"
  if [ -e "$to" ]; then echo "kept   ${to#$DEST/}"; else cp "$SKILL/assets/$f" "$to"; echo "copied ${to#$DEST/}"; fi
done
mkdir -p "$DEST/assets/music" "$DEST/assets/sounds/sfx" "$DEST/out"
[ -e "$DEST/compositions/media" ] || { ln -s ../assets "$DEST/compositions/media"; echo "linked compositions/media -> ../assets"; }

(cd "$DEST" && npm install --silent && echo "npm install done")
echo "next: write brief.ts, then compositions/<name>.tsx (see the skill's references/composition.md)"
