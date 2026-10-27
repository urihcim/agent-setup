#!/bin/sh
# 公開されている最新の AGENTS.md をコンテキストに加える SessionStart フック。
# クラウド環境ではセットアップスクリプトの結果が数日キャッシュされ、
# ~/.claude/CLAUDE.md が古いままになることがあるので、違うときだけ出力する。
# 取得に失敗したら何も出さず、手元の CLAUDE.md で続ける。
url=https://raw.githubusercontent.com/${AGENT_SETUP_REPO:-urihcim/agent-setup}/${AGENT_SETUP_REF:-main}/AGENTS.md

latest=$(curl -fsSL --max-time 10 "$url") || exit 0
current=$(cat "$HOME/.claude/CLAUDE.md" 2>/dev/null) || current=
[ "$latest" = "$current" ] && exit 0

echo "~/.claude/CLAUDE.md は古い版で、最新版は次のとおり。違いがある箇所はこちらに従う。"
echo
echo "$latest"
