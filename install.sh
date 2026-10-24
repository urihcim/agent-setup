#!/bin/sh
# エージェント向けの指示と設定を、インストール済みのエージェントに配置する。
#
#   curl -fsSL https://raw.githubusercontent.com/urihcim/agent-setup/main/install.sh | sh
#
# チェックアウト済みのリポジトリから実行した場合はその内容を使い、
# それ以外（curl からの実行など）は最新のアーカイブを取得して使う。
set -eu

REPO=${AGENT_SETUP_REPO:-urihcim/agent-setup}
REF=${AGENT_SETUP_REF:-main}

src=$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)
if [ -z "$src" ] || [ ! -f "$src/AGENTS.md" ]; then
	src=$(mktemp -d)
	trap 'rm -rf "$src"' EXIT
	curl -fsSL "https://github.com/$REPO/archive/refs/heads/$REF.tar.gz" |
		tar -xz -C "$src" --strip-components=1
fi

has() {
	[ -d "$HOME/$1" ] || command -v "$2" >/dev/null 2>&1
}

put() {
	mkdir -p "$(dirname "$2")"
	cp "$1" "$2.tmp" && mv "$2.tmp" "$2"
}

# settings.json に追加分をマージする。オブジェクトは再帰的にマージし、
# hooks は同じコマンドの既存エントリを置き換える。
merge_json() {
	python3 - "$1" "$2" <<'EOF'
import json, sys

dst_path, src_path = sys.argv[1:]
try:
    with open(dst_path) as f:
        dst = json.load(f)
except (FileNotFoundError, ValueError):
    dst = {}
with open(src_path) as f:
    src = json.load(f)

def commands(entry):
    return {h.get("command") for h in entry.get("hooks", [])}

def merge(a, b, key=None):
    if key == "hooks" and isinstance(a, dict) and isinstance(b, dict):
        for event, entries in b.items():
            ours = set().union(*map(commands, entries))
            kept = [e for e in a.get(event, []) if not commands(e) & ours]
            a[event] = kept + entries
        return a
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in b.items():
            a[k] = merge(a[k], v, k) if k in a else v
        return a
    return b

with open(dst_path + ".tmp", "w") as f:
    json.dump(merge(dst, src), f, indent=2, ensure_ascii=False)
    f.write("\n")
EOF
	mv "$1.tmp" "$1"
}

if has .claude claude; then
	put "$src/AGENTS.md" "$HOME/.claude/CLAUDE.md"
	mkdir -p "$HOME/.claude/hooks"
	for f in "$src"/claude/hooks/*; do
		put "$f" "$HOME/.claude/hooks/$(basename "$f")"
		chmod +x "$HOME/.claude/hooks/$(basename "$f")"
	done
	merge_json "$HOME/.claude/settings.json" "$src/claude/settings.json"
fi

if has .codex codex; then
	put "$src/AGENTS.md" "$HOME/.codex/AGENTS.md"
fi

if has .gemini gemini; then
	put "$src/AGENTS.md" "$HOME/.gemini/GEMINI.md"
fi

if has .copilot copilot; then
	put "$src/AGENTS.md" "$HOME/.copilot/copilot-instructions.md"
fi
