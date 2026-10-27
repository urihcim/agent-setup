#!/bin/bash
# クラウド環境（Claude Code on the web など）向けに、エージェントの指示と設定を配置する。
# ローカル環境ではこのスクリプトは使わない。
#
#   curl -fsSL https://raw.githubusercontent.com/urihcim/agent-setup/main/install.sh | bash
#
# チェックアウト済みのリポジトリから実行した場合はその内容を使い、
# それ以外（パイプでの実行など）は最新のアーカイブを取得して使う。
# 何度実行しても同じ結果になる。
set -euo pipefail

REPO=${AGENT_SETUP_REPO:-urihcim/agent-setup}
REF=${AGENT_SETUP_REF:-main}

src=
if [ "$(basename "$0")" = install.sh ] && [ -f "$0" ]; then
	src=$(cd "$(dirname "$0")" && pwd)
fi
if [ -z "$src" ] || [ ! -f "$src/AGENTS.md" ]; then
	src=$(mktemp -d)
	trap 'rm -rf "$src"' EXIT
	curl -fsSL --retry 3 "https://github.com/$REPO/archive/refs/heads/$REF.tar.gz" |
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
	local dst=$1
	shift
	[ -s "$dst" ] && jq -e . "$dst" >/dev/null 2>&1 || echo '{}' >"$dst"
	jq '
		def commands: [.hooks[]?.command];
		def merge_hooks($b):
			reduce ($b | to_entries[]) as $e (.;
				($e.value | map(commands[])) as $ours
				| .[$e.key] = ((.[$e.key] // []) | map(select(commands - $ours == commands))) + $e.value);
		def merge($b):
			if type == "object" and ($b | type) == "object" then
				reduce ($b | to_entries[]) as $e (.;
					if has($e.key) | not then .[$e.key] = $e.value
					elif $e.key == "hooks" and (.[$e.key] | type) == "object" and ($e.value | type) == "object"
					then .[$e.key] |= merge_hooks($e.value)
					else .[$e.key] |= merge($e.value) end)
			else $b end;
		reduce inputs as $b (.; merge($b))
	' "$dst" "$@" >"$dst.tmp"
	mv "$dst.tmp" "$dst"
}

if has .claude claude; then
	put "$src/AGENTS.md" "$HOME/.claude/CLAUDE.md"
	for f in "$src"/claude/hooks/*; do
		put "$f" "$HOME/.claude/hooks/$(basename "$f")"
		chmod +x "$HOME/.claude/hooks/$(basename "$f")"
	done
	merge_json "$HOME/.claude/settings.json" \
		"$src/claude/settings.json" "$src/claude/cloud-settings.json"
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
