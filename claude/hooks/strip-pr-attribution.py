#!/usr/bin/env python3
"""PR 本文から Claude Projects の帰属ブロックを取り除く PreToolUse フック。"""
import json
import re
import sys

MARKER = "claude-projects-attribution"
BLOCK = re.compile(
    r"^[ \t]*<!-- claude-projects-attribution:.*?-->[ \t]*\r?\n"
    r"(?:[ \t]*_Requested by .*?_[ \t]*\r?\n)?(?:[ \t]*\r?\n)*",
    re.MULTILINE,
)

data = json.load(sys.stdin)
tool_input = data.get("tool_input") or {}
if data.get("tool_name") == "Bash":
    if MARKER in tool_input.get("command", ""):
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "PR 本文に帰属表示を入れないこと。claude-projects-attribution の行と Requested by の行を削除して再実行する。",
        }}, sys.stdout, ensure_ascii=False)
else:
    body = tool_input.get("body")
    if isinstance(body, str) and MARKER in body:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {**tool_input, "body": BLOCK.sub("", body)},
        }}, sys.stdout, ensure_ascii=False)
