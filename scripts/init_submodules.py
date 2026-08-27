#!/usr/bin/env python3
"""Checkout vendor submodules. Default: runtime only, depth 1.

Research refs in .gitmodules use update=none so
`git clone --recurse-submodules` skips them. Pass --all to fetch those too.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITMODULES = ROOT / ".gitmodules"


def gitmodules_entries(path: Path = GITMODULES) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("[submodule "):
            if current is not None:
                entries.append(current)
            name = line.split('"', 1)[1].rsplit('"', 1)[0]
            current = {"name": name}
            continue
        if current is None or "=" not in line or line.startswith(("#", ";")):
            continue
        key, value = line.split("=", 1)
        current[key.strip()] = value.strip()
    if current is not None:
        entries.append(current)
    return entries


def runtime_paths(entries: list[dict[str, str]] | None = None) -> list[str]:
    if entries is None:
        entries = gitmodules_entries()
    return [e["path"] for e in entries if e.get("update") != "none"]


def reference_paths(entries: list[dict[str, str]] | None = None) -> list[str]:
    if entries is None:
        entries = gitmodules_entries()
    return [e["path"] for e in entries if e.get("update") == "none"]


def _update(paths: list[str], *, checkout: bool) -> None:
    if not paths:
        return
    cmd = ["git", "-C", str(ROOT), "submodule", "update", "--init", "--depth", "1"]
    if checkout:
        cmd.append("--checkout")
    cmd.extend(["--jobs", "4", "--", *paths])
    subprocess.run(cmd, check=True)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if any(a in ("-h", "--help") for a in args):
        print("usage: init_submodules.py [--all]")
        return 0
    want_all = "--all" in args
    entries = gitmodules_entries()
    _update(runtime_paths(entries), checkout=False)
    if want_all:
        _update(reference_paths(entries), checkout=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
