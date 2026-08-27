#!/usr/bin/env python3
"""Fold latex/catalog/shorthand + Lean/MMA snapshots into math-symbols.csv.

Offline only. Reads docs/drafts/import/*.json. Does not touch proj-ref/.
Same Lean abbrev mapping to two glyphs exits non-zero.

vscode-lean4 abbreviations.json:
  https://github.com/leanprover/vscode-lean4
  (vendored under docs/drafts/import/lean-abbreviations.json)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

WIDE_COLS = (
    "glyph",
    "latex",
    "latex_alias",
    "katex",
    "typst",
    "typst_shorthand",
    "lean",
    "lean_shorthand",
    "mma",
    "mma_alias",
)

# Cloverplus English names that are not TeX control sequences.
LATEX_FORCE_ALIAS = frozenset(
    {
        "clam",
        "dollar",
        "percent",
        "ampersand",
        "and",
        "plus",
        "comma",
        "period",
        "slash",
        "semicolon",
        "atsign",
        "yuan",
        "section",
        "paragraph",
        "sterling",
    }
)
LATEX_CLASSIC_EXTRA = frozenset(
    {
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "zeta",
        "eta",
        "theta",
        "iota",
        "kappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "omicron",
        "pi",
        "rho",
        "sigma",
        "tau",
        "upsilon",
        "phi",
        "chi",
        "psi",
        "omega",
        "varepsilon",
        "vartheta",
        "varphi",
        "varpi",
        "varrho",
        "varkappa",
        "le",
        "ge",
        "ne",
        "neq",
        "to",
        "gets",
        "lnot",
        "land",
        "lor",
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "log",
        "ln",
        "lg",
        "exp",
        "lim",
        "inf",
        "sup",
        "max",
        "min",
        "det",
        "dim",
        "gcd",
        "hom",
        "ker",
        "arg",
        "deg",
        "frac",
        "sqrt",
        "sum",
        "int",
        "oint",
        "prod",
        "dots",
        "ldots",
        "cdots",
        "vdots",
        "ddots",
        "infty",
        "emptyset",
        "partial",
        "nabla",
        "hbar",
        "ell",
        "aleph",
        "cdot",
        "times",
        "div",
        "pm",
        "mp",
        "circ",
        "ast",
        "star",
        "cap",
        "cup",
        "subset",
        "subseteq",
        "forall",
        "exists",
        "neg",
        "backslash",
        "lbrace",
        "rbrace",
        "vert",
        "langle",
        "rangle",
        "rightarrow",
        "leftarrow",
        "leftrightarrow",
        "leq",
        "geq",
        "colon",
        "implies",
        "impliedby",
        "iff",
        "square",
        "blacksquare",
        "smallsetminus",
        "bullet",
        "eth",
        "underbar",
        "degree",
    }
)
EXTRA_COLS = ("commit", "code", "kind", "glyph", "comment", "source")

# Typst/Lean shorthand overlap plus research-named MMA input aliases.
MMA_INPUT_ALIASES = {
    "->": "→",
    "==>": "⟹",
    "=>": "⇒",
    "!=": "≠",
    "<=": "≤",
    ">=": "≥",
    "<->": "↔",
    "<=>": "⇔",
}


def split_codes(raw: str) -> list[str]:
    return [c.strip() for c in (raw or "").split(" | ") if c.strip()]


def merge_codes(*parts: str) -> str:
    seen: list[str] = []
    for raw in parts:
        for code in split_codes(raw):
            if " " in code or "\\" in code:
                print(f"drop code {code!r} (space or backslash)", file=sys.stderr)
                continue
            if code not in seen:
                seen.append(code)
    return " | ".join(seen)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") or "" for k in fieldnames})


def load_latex_native(draft: Path) -> set[str]:
    names = {n.lower() for n in LATEX_CLASSIC_EXTRA}
    listed = draft / "import" / "latex-native.txt"
    if listed.is_file():
        for line in listed.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                names.add(s.lower())
    tex = draft / "import" / "unicode-math-table.tex"
    if tex.is_file():
        import re

        for m in re.finditer(
            r"\\UnicodeMathSymbol\{[^}]+\}\{\s*\\([A-Za-z@]+)",
            tex.read_text(encoding="utf-8"),
        ):
            raw = m.group(1)
            names.add(raw.lower())
            for pfx in ("mup", "up"):
                if raw.startswith(pfx) and len(raw) > len(pfx):
                    names.add(raw[len(pfx) :].lower())
    return names


def is_native_latex(code: str, native: set[str]) -> bool:
    if not code or code.lower() in LATEX_FORCE_ALIAS:
        return False
    if any(ch in code for ch in "^_()[]{}\\"):
        return False
    if not code.isalpha():
        return False
    return code.lower() in native


def split_latex_cell(raw: str, native: set[str]) -> tuple[str, str]:
    keep: list[str] = []
    alias: list[str] = []
    for code in split_codes(raw):
        if is_native_latex(code, native):
            keep.append(code)
        else:
            alias.append(code)
    return merge_codes(*keep), merge_codes(*alias)


def classify_latex_columns(rows: dict[str, dict[str, str]], native: set[str]) -> None:
    for row in rows.values():
        combined = merge_codes(row.get("latex") or "", row.get("latex_alias") or "")
        row["latex"], row["latex_alias"] = split_latex_cell(combined, native)


def empty_row(glyph: str) -> dict[str, str]:
    row = {c: "" for c in WIDE_COLS}
    row["glyph"] = glyph
    return row


def ensure(rows: dict[str, dict[str, str]], glyph: str) -> dict[str, str]:
    if glyph not in rows:
        rows[glyph] = empty_row(glyph)
    return rows[glyph]


def is_lean_shorthand(abbrev: str) -> bool:
    return len(abbrev) <= 2 or not any(c.isalnum() for c in abbrev)


def load_lean(draft: Path) -> dict[str, str]:
    path = draft / "import" / "lean-abbreviations.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("lean-abbreviations.json must be an object", file=sys.stderr)
        raise SystemExit(1)
    return {str(k): str(v) for k, v in data.items()}


def load_mma_named(draft: Path) -> dict[str, str]:
    path = draft / "import" / "mma-named.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("mma-named.json must be an object", file=sys.stderr)
        raise SystemExit(1)
    return {str(k): str(v) for k, v in data.items()}


def apply_lean(rows: dict[str, dict[str, str]], abbrevs: dict[str, str]) -> None:
    seen: dict[str, str] = {}
    dropped = 0
    for abbrev, repl in abbrevs.items():
        if " " in abbrev or "\\" in abbrev:
            print(f"drop lean abbrev {abbrev!r} (space or backslash)", file=sys.stderr)
            dropped += 1
            continue
        glyph = repl.replace("$CURSOR", "")
        if not glyph:
            print(f"drop lean abbrev {abbrev!r} (empty replacement)", file=sys.stderr)
            dropped += 1
            continue
        prev = seen.get(abbrev)
        if prev is not None and prev != glyph:
            print(
                f"lean conflict: {abbrev!r} → {prev!r} and {glyph!r}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        seen[abbrev] = glyph
        row = ensure(rows, glyph)
        col = "lean_shorthand" if is_lean_shorthand(abbrev) else "lean"
        row[col] = merge_codes(row[col], abbrev)
    if dropped:
        print(f"dropped {dropped} lean abbrevs", file=sys.stderr)


def load_katex(draft: Path) -> list[dict[str, str]]:
    path = draft / "import" / "katex-symbols.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("katex-symbols.json must be a list")
    return data


def apply_katex(rows: dict[str, dict[str, str]], symbols: list[dict[str, str]]) -> None:
    seen: dict[str, str] = {}
    for item in symbols:
        code = (item.get("code") or "").strip()
        glyph = item.get("glyph") or ""
        if not code or not glyph or len(glyph) != 1:
            continue
        if " " in code or "\\" in code or code.startswith("@"):
            continue
        prev = seen.get(code)
        if prev and prev != glyph:
            print(f"katex conflict {code!r} -> {prev!r} and {glyph!r}", file=sys.stderr)
            raise SystemExit(1)
        seen[code] = glyph
        row = ensure(rows, glyph)
        row["katex"] = merge_codes(row["katex"], code)


def apply_mma(rows: dict[str, dict[str, str]], named: dict[str, str]) -> None:
    for glyph, row in rows.items():
        name = named.get(glyph)
        if name:
            row["mma"] = merge_codes(row["mma"], name)
    shorthand: set[str] = set()
    for row in rows.values():
        shorthand.update(split_codes(row["typst_shorthand"]))
        shorthand.update(split_codes(row["lean_shorthand"]))
    for alias, glyph in MMA_INPUT_ALIASES.items():
        if glyph not in rows:
            continue
        if alias == "->" or alias == "==>" or alias in shorthand:
            rows[glyph]["mma_alias"] = merge_codes(rows[glyph]["mma_alias"], alias)


def fold_legacy(draft: Path, rows: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    latex_path = draft / "latex.csv"
    catalog_path = draft / "math-catalog.csv"
    shorthand_path = draft / "typst-shorthand.csv"
    extra_path = draft / "typst-extra.csv"
    missing = [p.name for p in (latex_path, catalog_path, shorthand_path) if not p.is_file()]
    if missing:
        print("full fold needs " + ", ".join(missing), file=sys.stderr)
        raise SystemExit(1)

    native = load_latex_native(draft)
    for r in read_csv(latex_path):
        glyph = (r.get("glyph") or "").strip()
        name = (r.get("name") or "").strip()
        if not glyph or not name:
            continue
        row = ensure(rows, glyph)
        if is_native_latex(name, native):
            row["latex"] = merge_codes(row["latex"], name)
        else:
            row["latex_alias"] = merge_codes(row["latex_alias"], name)

    extra = read_csv(extra_path) if extra_path.is_file() else []
    seen_extra = {(e.get("commit") or "", e.get("code") or "") for e in extra}
    for r in read_csv(catalog_path):
        cls = r.get("class") or ""
        name = (r.get("name") or "").strip()
        glyph = (r.get("glyph") or "").strip()
        if cls == "Literal" or not name:
            continue
        if cls == "Op":
            key = (name, name)
            if key not in seen_extra:
                extra.append(
                    {
                        "commit": name,
                        "code": name,
                        "kind": "typst-op",
                        "glyph": "",
                        "comment": "typst op",
                        "source": "math-catalog Op",
                    }
                )
                seen_extra.add(key)
            continue
        if cls == "Symbol":
            if not glyph:
                continue
            row = ensure(rows, glyph)
            row["typst"] = merge_codes(row["typst"], name)

    for r in read_csv(shorthand_path):
        glyph = (r.get("glyph") or "").strip()
        seq = (r.get("seq") or "").strip()
        if not glyph or not seq:
            continue
        row = ensure(rows, glyph)
        row["typst_shorthand"] = merge_codes(row["typst_shorthand"], seq)
        paths = merge_codes(r.get("path") or "", r.get("paths") or "")
        if paths:
            row["typst"] = merge_codes(row["typst"], paths)

    apply_lean(rows, load_lean(draft))
    apply_mma(rows, load_mma_named(draft))
    apply_katex(rows, load_katex(draft))
    return extra


def load_wide(draft: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    path = draft / "math-symbols.csv"
    if not path.is_file():
        return rows
    for r in read_csv(path):
        glyph = r.get("glyph") or ""
        if not glyph:
            continue
        row = empty_row(glyph)
        for col in WIDE_COLS:
            if col != "glyph":
                row[col] = r.get(col) or ""
        rows[glyph] = row
    return rows


def write_wide(draft: Path, rows: dict[str, dict[str, str]]) -> None:
    ordered = [rows[g] for g in sorted(rows, key=lambda g: (len(g), g))]
    write_csv(draft / "math-symbols.csv", WIDE_COLS, ordered)
    print(f"wrote {draft / 'math-symbols.csv'} ({len(ordered)} glyphs)")


def refresh_lean(draft: Path) -> None:
    wide = draft / "math-symbols.csv"
    if not wide.is_file():
        print("math-symbols.csv missing; cannot refresh lean", file=sys.stderr)
        raise SystemExit(1)
    rows = load_wide(draft)
    for row in rows.values():
        row["lean"] = ""
        row["lean_shorthand"] = ""
    apply_lean(rows, load_lean(draft))
    apply_mma(rows, load_mma_named(draft))
    apply_katex(rows, load_katex(draft))
    write_wide(draft, rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument(
        "--lean-only",
        action="store_true",
        help="overwrite lean / lean_shorthand; fill mma for glyphs now in the table",
    )
    p.add_argument(
        "--split-latex",
        action="store_true",
        help="reclassify latex vs latex_alias on the current wide table",
    )
    p.add_argument(
        "--katex-only",
        action="store_true",
        help="fill katex column from import/katex-symbols.json",
    )
    args = p.parse_args()
    draft = Path(args.root).resolve() / "docs" / "drafts"
    if args.split_latex:
        rows = load_wide(draft)
        classify_latex_columns(rows, load_latex_native(draft))
        write_wide(draft, rows)
        return
    if args.katex_only:
        rows = load_wide(draft)
        for row in rows.values():
            row["katex"] = ""
        apply_katex(rows, load_katex(draft))
        write_wide(draft, rows)
        return
    if args.lean_only or not (draft / "latex.csv").is_file():
        refresh_lean(draft)
        return
    rows: dict[str, dict[str, str]] = {}
    extra = fold_legacy(draft, rows)
    write_wide(draft, rows)
    write_csv(draft / "typst-extra.csv", EXTRA_COLS, extra)
    print(f"wrote {draft / 'typst-extra.csv'} ({len(extra)} rows)")


if __name__ == "__main__":
    main()
