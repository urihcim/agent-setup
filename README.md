# agent-setup

コーディングエージェント（Claude Code、Codex、Gemini CLI、Copilot CLI）向けの共通の指示と設定。

## 導入

```sh
curl -fsSL https://raw.githubusercontent.com/urihcim/agent-setup/main/install.sh | sh
```

チェックアウトしたリポジトリから `./install.sh` を実行してもよい。その場合はチェックアウトの内容が使われる。

何度実行しても同じ結果になる。インストール済みのエージェント（ホームの設定ディレクトリかコマンドがあるもの）にだけ、次のファイルを配置する。

| エージェント | 配置先 |
| --- | --- |
| Claude Code | `~/.claude/CLAUDE.md`、`~/.claude/hooks/`、`~/.claude/settings.json`（マージ） |
| Codex | `~/.codex/AGENTS.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |
| Copilot CLI | `~/.copilot/copilot-instructions.md` |

`settings.json` は既存の内容にマージする。オブジェクトは再帰的にマージし、`hooks` は同じコマンドのエントリを置き換える。

### Claude Code on the web

環境設定のセットアップスクリプトに、上の `curl` の1行を書く。セットアップスクリプトは新しいセッションを作るたびに実行されるので、常に最新の内容が入る。

## 構成

- `AGENTS.md`: 全エージェント共通の指示（正本）
- `claude/settings.json`: Claude Code の設定に追加する分
- `claude/hooks/strip-pr-attribution.py`: Claude Projects が PR 本文に挿入する帰属ブロックを取り除く PreToolUse フック
