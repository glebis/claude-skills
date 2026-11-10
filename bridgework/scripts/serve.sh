#!/bin/sh
# Serve Bridgework on this machine only.
#   serve.sh            your stack, from ~/.bridgework/site, on port 4175
#   serve.sh demo       the synthetic demo stack, on port 4174
#   serve.sh DIR PORT   any built site
# Separate ports keep each stack's saved trail apart in the browser.
here=$(cd "$(dirname "$0")/.." && pwd)
case "$1" in
  demo) dir="$here/assets/app"; port=${2:-4174} ;;
  "") dir="$HOME/.bridgework/site"; port=4175 ;;
  *) dir=$1; port=${2:-4175} ;;
esac
[ -f "$dir/index.html" ] || { echo "No site in $dir. Build one with scripts/build_stack.py first." >&2; exit 1; }
if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then echo "Port $port is busy. Pass another port." >&2; exit 1; fi
echo "Bridgework at http://localhost:$port (Ctrl+C to stop)"
exec python3 -m http.server "$port" --bind 127.0.0.1 --directory "$dir"
