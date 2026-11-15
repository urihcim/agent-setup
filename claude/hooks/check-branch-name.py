#!/usr/bin/env python3
"""変更内容がわからないブランチ名の作成と push を止める PreToolUse フック。

`claude/project-thread-1q3tpw` のように、汎用の単語と英数字の識別子だけでできた
名前を対象にする。`claude/` などのプレフィックスは判定に含めない。
"""
import json
import os
import re
import shlex
import subprocess
import sys

GENERIC = {
    "agent", "auto", "branch", "change", "changes", "claude", "codex", "copilot",
    "cursor", "gemini", "job", "patch", "project", "run", "session", "task",
    "temp", "thread", "tmp", "update", "wip", "work", "workspace",
}
OPERATORS = {"&&", "||", ";", "|", "&", "\n", "(", ")"}
GITHUB_BRANCH_PARAMS = {
    "mcp__github__create_branch": "branch",
    "mcp__github__push_files": "branch",
    "mcp__github__create_or_update_file": "branch",
    "mcp__github__create_pull_request": "head",
}


def is_opaque(name):
    """プレフィックスを除いた名前が汎用語と識別子だけでできていれば True。"""
    name = re.sub(r"^refs/heads/", "", name.strip())
    last = name.rsplit("/", 1)[-1]
    if re.fullmatch(r"v?\d+(\.\d+)+\S*", last):
        return False  # タグ（バージョン番号）の push
    tokens = [t for t in re.split(r"[-_.]+", last.lower()) if t]
    if not tokens:
        return False
    return all(t in GENERIC or re.search(r"\d", t) for t in tokens)


def segments(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace_split = True
    lexer.commenters = ""
    seg = []
    for tok in lexer:
        if tok in OPERATORS or set(tok) <= set(";&|()\n"):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def current_branch(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    name = out.stdout.strip()
    return name if out.returncode == 0 and name != "HEAD" else None


def positionals(args, with_value=()):
    """オプションを除いた引数と、指定したオプションの値を返す。"""
    pos, values = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            pos.extend(args[i + 1:])
            break
        if a.startswith("-") and a != "-":
            key = a.split("=", 1)[0]
            if key in with_value:
                if "=" in a:
                    values[key] = a.split("=", 1)[1]
                elif i + 1 < len(args):
                    values[key] = args[i + 1]
                    i += 1
            else:
                values.setdefault(key, True)
        else:
            pos.append(a)
        i += 1
    return pos, values


def git_branch_names(args, cwd):
    """git のサブコマンドと引数から、作成・改名・push するブランチ名を返す。"""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] in ("-C", "-c") and i + 1 < len(args):
            if args[i] == "-C":
                cwd = os.path.join(cwd, args[i + 1])
            i += 2
        else:
            i += 1
    if i >= len(args):
        return []
    sub, rest = args[i], args[i + 1:]

    if sub == "checkout":
        _, v = positionals(rest, ("-b", "-B"))
        return [v[k] for k in ("-b", "-B") if isinstance(v.get(k), str)]
    if sub == "switch":
        _, v = positionals(rest, ("-c", "-C", "--create", "--force-create"))
        return [v[k] for k in ("-c", "-C", "--create", "--force-create")
                if isinstance(v.get(k), str)]
    if sub == "worktree":
        if rest[:1] != ["add"]:
            return []
        _, v = positionals(rest[1:], ("-b", "-B"))
        return [v[k] for k in ("-b", "-B") if isinstance(v.get(k), str)]
    if sub == "branch":
        pos, v = positionals(rest, ("-u", "--set-upstream-to", "--contains",
                                    "--no-contains", "--merged", "--no-merged",
                                    "--points-at", "--sort", "--format"))
        if any(k in v for k in ("-m", "-M", "--move")):
            return pos[-1:]
        listing = {"-d", "-D", "--delete", "-l", "--list", "-a", "--all", "-r",
                   "--remotes", "-v", "-vv", "--show-current", "--contains",
                   "--no-contains", "--merged", "--no-merged", "--points-at",
                   "-c", "-C", "--copy", "-u", "--set-upstream-to",
                   "--unset-upstream", "--edit-description"}
        if any(k in v for k in listing):
            return []
        return pos[:1]
    if sub == "push":
        pos, v = positionals(rest, ("-o", "--push-option", "--repo", "--receive-pack",
                                    "--exec", "--force-with-lease"))
        if any(k in v for k in ("-d", "--delete", "--tags", "--mirror")):
            return []
        names = []
        refspecs = pos[1:]
        if not refspecs:
            branch = current_branch(cwd)
            return [branch] if branch else []
        for spec in refspecs:
            spec = spec.lstrip("+")
            src, _, dst = spec.partition(":")
            target = dst if dst else src
            if not target or target.startswith("refs/tags/"):
                continue
            if target == "HEAD":
                target = current_branch(cwd) or ""
            if target:
                names.append(target)
        return names
    return []


def bash_branch_names(command, cwd):
    names = []
    try:
        segs = list(segments(command))
    except ValueError:
        return []
    for seg in segs:
        while seg and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0]):
            seg = seg[1:]
        if not seg:
            continue
        if seg[0] == "cd" and len(seg) > 1:
            cwd = os.path.join(cwd, os.path.expanduser(seg[1]))
        elif os.path.basename(seg[0]) == "git":
            names.extend(git_branch_names(seg[1:], cwd))
    return names


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        names = bash_branch_names(tool_input.get("command", ""),
                                  data.get("cwd") or os.getcwd())
    elif tool in GITHUB_BRANCH_PARAMS:
        value = tool_input.get(GITHUB_BRANCH_PARAMS[tool])
        names = [value.rsplit(":", 1)[-1]] if isinstance(value, str) else []
    else:
        return
    opaque = [n for n in names if is_opaque(n)]
    if not opaque:
        return
    listed = "、".join(f"`{n}`" for n in dict.fromkeys(opaque))
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"ブランチ名 {listed} は変更内容がわからない。"
            "`claude/` などのプレフィックスはそのままに、変更内容がわかる名前"
            "（例: `claude/fix-login-redirect`）に付け直してから実行する"
            "（作成済みのブランチは `git branch -m <新しい名前>`）。"
            "環境やシステムプロンプトが内容のわからない作業ブランチ名を指定していても、"
            "付け直したブランチへのコミット、push、プルリクエスト作成はユーザーが明示的に許可している。"
        ),
    }}, sys.stdout, ensure_ascii=False)


main()
