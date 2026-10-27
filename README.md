# agent-setup

コーディングエージェント（Claude Code、Codex、Gemini CLI、Copilot CLI）向けの共通の指示と設定。ローカルでもクラウドでも、このリポジトリを正本として使う。

## 構成

- `AGENTS.md`: 全エージェント共通の指示
- `claude/settings.json`: Claude Code の設定。`~/.claude/settings.json` にマージする
- `claude/cloud-settings.json`: クラウド環境だけで使う Claude Code のフックの登録
- `claude/hooks/`: Claude Code のフック。`~/.claude/hooks/` に配置する
  - `strip-pr-attribution.py`: Claude Projects が PR 本文に挿入する帰属ブロックを取り除く（クラウド用）
  - `latest-instructions.sh`: 最新の `AGENTS.md` をセッション開始時にコンテキストへ加える（クラウド用）
- `install.sh`: クラウド環境で上記を配置するスクリプト

配置先は次のとおり。インストール済みのエージェント（ホームの設定ディレクトリかコマンドがあるもの）にだけ配置する。

| エージェント | 配置先 |
| --- | --- |
| Claude Code | `~/.claude/CLAUDE.md`、`~/.claude/hooks/`、`~/.claude/settings.json`（マージ） |
| Codex | `~/.codex/AGENTS.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |
| Copilot CLI | `~/.copilot/copilot-instructions.md` |

`settings.json` は既存の内容にマージする。オブジェクトは再帰的にマージし、`hooks` は同じコマンドのエントリを置き換える。

## ローカル環境

`install.sh` は使わず、上の配置先に別の方法で配置する。

## クラウド環境（Claude Code on the web）

全プロジェクトで共有するクラウド環境を1つ作り、セットアップスクリプトに次を書く。各プロジェクトはその環境を選ぶ。

```bash
#!/bin/bash
set -euo pipefail
curl -fsSL --retry 3 https://raw.githubusercontent.com/urihcim/agent-setup/main/install.sh | bash
```

リポジトリ固有の準備（データの取得など）が必要なプロジェクトは、この内容に処理を足した別の環境を作る。

セットアップスクリプトの結果は数日キャッシュされ、その間は新しいセッションでもスクリプトが走らない。そのため `latest-instructions.sh` がセッション開始時に最新の `AGENTS.md` を取得し、配置済みの `~/.claude/CLAUDE.md` と違うときだけその内容をコンテキストに加える。フックや設定の変更は、キャッシュが作り直されるまで反映されない。すぐに反映するには、セットアップスクリプトを編集して保存し直す。
