#!/usr/bin/env sh
set -eu

SKIP_MERMAID=0
for arg in "$@"; do
  case "$arg" in
    --skip-mermaid)
      SKIP_MERMAID=1
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if command -v uv >/dev/null 2>&1; then
  uv tool install --reinstall .
else
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3.11+ or uv is required." >&2
    exit 1
  fi
  python3 -m pip install --user .
fi

if [ "$SKIP_MERMAID" -eq 0 ]; then
  if command -v npm >/dev/null 2>&1; then
    npm install -g @mermaid-js/mermaid-cli
  else
    echo "npm was not found. Install Node.js/npm, then run: md2doc install-deps" >&2
  fi
fi

md2doc --help >/dev/null
echo "md2doc installed successfully."
