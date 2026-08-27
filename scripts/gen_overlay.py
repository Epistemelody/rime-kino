#!/usr/bin/env python3
"""Generate overlay/ from docs/drafts tables. Do not write back to drafts."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

SKIP_UNICODE_WORDS = frozenset(
    {
        "of",
        "the",
        "and",
        "or",
        "to",
        "in",
        "on",
        "a",
        "an",
        "with",
        "for",
        "from",
        "by",
        "at",
        "as",
        "is",
        "small",
        "letter",
        "capital",
        "sign",
        "symbol",
    }
)

# Same width command_draft.lua uses: gram = q:sub(1, GRAM_N).
GRAM_N = 2
# Keep in sync with command_keys.lua ["\\"] extras and recognizer/patterns/command_draft.
# Space and embedded \ are not extra keys (import drops those codes).
COMMAND_EXTRA = ".-><=!~*:|[]^_+(){}'?/#&`\"$%"
_CJK_KEY = re.compile(r"^[\u4e00-\u9fff]+$")
MATH_CODE_COLS = (
    ("latex", "latex"),
    ("latex_alias", "latex-alias"),
    ("katex", "katex"),
    ("typst", "typst-sym"),
    ("typst_shorthand", "typst-shorthand"),
    ("lean", "lean"),
    ("lean_shorthand", "lean-shorthand"),
    ("mma", "mma"),
    ("mma_alias", "mma-alias"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def yaml_header(name: str, extra: str = "") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        'version: "1"\n'
        "sort: original\n"
        "use_preset_vocabulary: false\n"
        "columns:\n"
        "  - text\n"
        "  - code\n"
        f"{extra}"
        "...\n\n"
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def lua_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def uname(ch: str) -> str:
    if not ch:
        return ""
    try:
        return unicodedata.name(ch[0])
    except ValueError:
        return ""


def is_ascii_glyph(g: str) -> bool:
    return bool(g) and all(ord(c) < 128 for c in g)


def split_codes(raw: str) -> list[str]:
    """Alias cells use ' | ' so codes like |-> stay intact."""
    return [c.strip() for c in (raw or "").split(" | ") if c.strip()]


VOWELS = frozenset("aeiou")


def kana_code_entries(hira: str, kata: str, code: str) -> list[tuple[str, str]]:
    """Both scripts for one romaji code. Case only orders the menu, not availability."""
    lo, hi = code.lower(), code.upper()
    hira, kata = hira.strip(), kata.strip()
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(text: str, key: str) -> None:
        if not text:
            return
        pair = (text, key)
        if pair in seen:
            return
        seen.add(pair)
        out.append(pair)

    add(hira, lo)
    add(kata, lo)
    if hi != lo:
        add(kata, hi)
        add(hira, hi)
    return out


def _want_kata(ch: str, script: str | None) -> bool:
    if script == "kata":
        return True
    if script == "hira":
        return False
    return ch.isupper()


def build_romaji_map(draft: Path) -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for r in read_csv(draft / "kana.csv"):
        kata = (r.get("kata") or "").strip()
        hira = (r.get("hira") or "").strip()
        family = (r.get("family") or "").strip()
        if kata == "?" or not hira:
            continue
        for code in split_codes(r.get("codes") or ""):
            if code == "ccye":
                continue
            lo = code.lower()
            if lo in {"n", "nn"}:
                continue
            if family == "sokuon" and lo.startswith("nn"):
                continue
            mapping[lo] = (hira, kata if kata else hira)
    mapping["-"] = ("ー", "ー")
    return mapping


def romaji_to_kana(
    s: str,
    mapping: dict[str, tuple[str, str]],
    script: str | None = None,
) -> tuple[str, str]:
    """IME-style romaji: pending n, sokuon doubling, longest mora match.

    script=None follows per-mora letter case; "hira"/"kata" force one script.
    """
    n = len(s)
    max_len = max((len(k) for k in mapping), default=1)
    out: list[str] = []
    i = 0
    pending_n = False
    pending_n_upper = False

    def match_at(pos: int, prefix: str = "") -> tuple[int, tuple[str, str] | None]:
        blob = prefix + s[pos:]
        lim = min(max_len, len(blob))
        for length in range(lim, 0, -1):
            key = blob[:length].lower()
            row = mapping.get(key)
            if row:
                return length, row
        return 0, None

    while i < n:
        if pending_n:
            ch = s[i]
            cl = ch.lower()
            if cl == "n":
                nxt = s[i + 1].lower() if i + 1 < n else ""
                out.append("ン" if pending_n_upper else "ん")
                if nxt == "" or (nxt not in VOWELS and nxt != "y"):
                    pending_n = False
                    i += 1
                    continue
                pending_n_upper = _want_kata(ch, script)
                i += 1
                continue
            length, row = match_at(i, "n")
            if length and row:
                use_kata = pending_n_upper
                out.append(row[1] if use_kata else row[0])
                pending_n = False
                i += length - 1
                continue
            out.append("ン" if pending_n_upper else "ん")
            pending_n = False
            continue
        ch = s[i]
        cl = ch.lower()
        if cl == "n":
            pending_n = True
            pending_n_upper = _want_kata(ch, script)
            i += 1
            continue
        if (
            cl.isalpha()
            and cl not in VOWELS
            and cl != "y"
            and i + 1 < n
            and s[i + 1].lower() == cl
        ):
            out.append("ッ" if _want_kata(ch, script) else "っ")
            i += 1
            continue
        length, row = match_at(i)
        if length and row:
            use_kata = _want_kata(ch, script)
            out.append(row[1] if use_kata else row[0])
            i += length
            continue
        break
    if pending_n:
        out.append("ン" if pending_n_upper else "ん")
        pending_n = False
    rest = s[i:]
    return "".join(out), rest


def gen_jp_romaji(draft: Path, overlay: Path) -> None:
    mapping = build_romaji_map(draft)
    max_len = max((len(k) for k in mapping), default=1)
    lines = ["-- generated from docs/drafts/kana.csv; do not edit", "return {", f"  max_len = {max_len},", "  map = {"]
    for key in sorted(mapping, key=lambda k: (-len(k), k)):
        hira, kata = mapping[key]
        lines.append(f"    [{lua_str(key)}] = {{{lua_str(hira)}, {lua_str(kata)}}},")
    lines.append("  },")
    lines.append("}")
    lines.append("")
    write_text(overlay / "lua" / "jp_romaji.lua", "\n".join(lines))


def gen_kana(draft: Path, overlay: Path) -> None:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for r in read_csv(draft / "kana.csv"):
        kata = (r.get("kata") or "").strip()
        hira = (r.get("hira") or "").strip()
        if kata == "?":
            continue
        for code in split_codes(r.get("codes") or ""):
            if code == "ccye":
                continue
            for text, key in kana_code_entries(hira, kata, code):
                pair = (text, key)
                if pair in seen:
                    continue
                seen.add(pair)
                lines.append(f"{text}\t{key}")
    if ("ー", "-") not in seen:
        lines.append("ー\t-")
    write_text(overlay / "kana.dict.yaml", yaml_header("kana") + "\n".join(lines) + "\n")


def gen_latin(draft: Path, overlay: Path) -> None:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for r in read_csv(draft / "latin-accents.csv"):
        glyph = r["glyph"]
        if glyph == ";":
            continue
        for code in split_codes(r["codes"]):
            rest = code[1:] if code.startswith(";") else code
            if rest == "":
                continue
            key = (glyph, rest)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"{glyph}\t{rest}")
    write_text(overlay / "latin.dict.yaml", yaml_header("latin") + "\n".join(lines) + "\n")


def iter_source_command_codes(draft: Path):
    """Every non-empty code in the wide table and typst-extra (not unicodedata)."""
    for r in read_csv(draft / "math-symbols.csv"):
        for col, _kind in MATH_CODE_COLS:
            yield from split_codes(r.get(col) or "")
    for r in read_csv(draft / "typst-extra.csv"):
        code = (r.get("code") or "").strip()
        if code:
            yield code


def collect_command_rows(draft: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(commit: str, code: str, kind: str, glyph: str = "") -> None:
        code = code.strip()
        if not code:
            return
        if kind == "mma" and code.startswith("[") and code.endswith("]"):
            return
        rows.append(
            {
                "commit": commit,
                "code": code,
                "kind": kind,
                "glyph": glyph or (commit if len(commit) == 1 else ""),
            }
        )

    for r in read_csv(draft / "math-symbols.csv"):
        glyph = r.get("glyph") or ""
        if not glyph:
            continue
        for col, kind in MATH_CODE_COLS:
            for code in split_codes(r.get(col) or ""):
                add(glyph, code, kind, glyph)

    for r in read_csv(draft / "typst-extra.csv"):
        add(r["commit"], r["code"], r["kind"], r.get("glyph") or "")

    glyphs: set[str] = set()
    for r in rows:
        g = r["glyph"]
        if g and len(g) == 1:
            glyphs.add(g)
    for g in sorted(glyphs):
        nm = uname(g)
        if not nm:
            continue
        compact = re.sub(r"[^a-z0-9]+", "", nm.lower())
        if compact:
            add(g, compact, "unicode", g)
    return rows


def ascii_code(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9.]*", code))


def command_code(code: str) -> bool:
    return bool(code) and all(c.isalnum() or c in COMMAND_EXTRA for c in code)


def unicode_gram_source(ch: str) -> str:
    """Index unicode names by content words, not filler (small/letter/of)."""
    nm = uname(ch)
    if not nm:
        return ""
    words = re.findall(r"[a-z]+", nm.lower())
    kept = [w for w in words if len(w) >= 4 and w not in SKIP_UNICODE_WORDS]
    return "".join(kept)


def pack_command_index(
    rows: list[dict[str, str]],
) -> tuple[list[tuple[str, str, str]], dict[str, list[int]]]:
    packed: list[tuple[str, str, str]] = []
    seen_p: set[tuple[str, str, str]] = set()
    for r in rows:
        t = (r["commit"], r["code"].lower(), r["kind"])
        if t in seen_p:
            continue
        seen_p.add(t)
        packed.append(t)

    g2: dict[str, list[int]] = defaultdict(list)
    for i, (commit, code, kind) in enumerate(packed):
        if kind == "unicode":
            if len(code) < 4:
                continue
            src = unicode_gram_source(commit if len(commit) == 1 else "")
        else:
            src = code.replace(".", "")
        if len(src) < GRAM_N:
            continue
        seen_g: set[str] = set()
        for j in range(0, len(src) - GRAM_N + 1):
            g = src[j : j + GRAM_N]
            if g in seen_g:
                continue
            seen_g.add(g)
            g2[g].append(i)
    return packed, dict(g2)


def prefix_postings(
    packed: list[tuple[str, str, str]],
) -> dict[str, dict[str, list[int]]]:
    """First-char / first-2-char buckets for exact, prefix, and dotted-last."""
    pre1: dict[str, list[int]] = defaultdict(list)
    pre2: dict[str, list[int]] = defaultdict(list)
    last1: dict[str, list[int]] = defaultdict(list)
    last2: dict[str, list[int]] = defaultdict(list)
    for i, (_commit, code, _kind) in enumerate(packed):
        if code:
            pre1[code[:1]].append(i)
        if len(code) >= 2:
            pre2[code[:2]].append(i)
        if "." in code:
            last = code.rsplit(".", 1)[-1]
            if last:
                last1[last[:1]].append(i)
            if len(last) >= 2:
                last2[last[:2]].append(i)
    return {
        "pre1": dict(pre1),
        "pre2": dict(pre2),
        "last1": dict(last1),
        "last2": dict(last2),
    }


def _u32_blob(nums: list[int]) -> bytes:
    import struct

    return struct.pack("<" + "I" * len(nums), *nums) if nums else b""


def _lua_bin(data: bytes) -> str:
    return '"' + "".join(f"\\x{b:02x}" for b in data) + '"'


def emoji_cldr_key_ok(key: str) -> bool:
    """CLDR annotations that are ordinary 1–2 character words rewrite IME candidates."""
    key = key.strip()
    if len(key) < 2:
        return False
    if _CJK_KEY.fullmatch(key) and len(key) < 3:
        return False
    if key.isascii() and key.isalpha() and len(key) < 3:
        return False
    return True


def gen_commands(draft: Path, overlay: Path) -> None:
    rows = collect_command_rows(draft)
    dict_lines: list[str] = []
    seen_dict: set[tuple[str, str]] = set()
    for r in rows:
        if not command_code(r["code"]):
            continue
        key = (r["commit"], r["code"])
        if key in seen_dict:
            continue
        seen_dict.add(key)
        dict_lines.append(f"{r['commit']}\t{r['code']}")
    write_text(
        overlay / "commands.dict.yaml",
        yaml_header("commands") + "\n".join(dict_lines) + "\n",
    )

    packed, g2 = pack_command_index(rows)
    maps = prefix_postings(packed)
    kinds: list[str] = []
    kind_id: dict[str, int] = {}
    gblob = bytearray()
    cblob = bytearray()
    goff = [1]
    coff = [1]
    kid = bytearray()
    for commit, code, kind in packed:
        gb, cb = commit.encode("utf-8"), code.encode("utf-8")
        gblob.extend(gb)
        cblob.extend(cb)
        goff.append(goff[-1] + len(gb))
        coff.append(coff[-1] + len(cb))
        if kind not in kind_id:
            kind_id[kind] = len(kinds) + 1
            kinds.append(kind)
        kid.append(kind_id[kind])

    def emit_map(name: str, posting: dict[str, list[int]]) -> list[str]:
        out = [f"local {name} = {{\n"]
        for gram in sorted(posting):
            raw = _u32_blob([i + 1 for i in posting[gram]])
            out.append(f"  [{lua_str(gram)}] = {_lua_bin(raw)},\n")
        out.append("}\n")
        return out

    parts = [
        "-- generated by scripts/gen_overlay.py; do not edit\n",
        f"local n = {len(packed)}\n",
        "local kinds = {",
        ", ".join(lua_str(k) for k in kinds),
        "}\n",
        f"local gblob = {_lua_bin(bytes(gblob))}\n",
        f"local cblob = {_lua_bin(bytes(cblob))}\n",
        f"local goff = {_lua_bin(_u32_blob(goff))}\n",
        f"local coff = {_lua_bin(_u32_blob(coff))}\n",
        f"local kid = {_lua_bin(bytes(kid))}\n",
    ]
    parts.extend(emit_map("pre1", maps["pre1"]))
    parts.extend(emit_map("pre2", maps["pre2"]))
    parts.extend(emit_map("last1", maps["last1"]))
    parts.extend(emit_map("last2", maps["last2"]))
    parts.extend(emit_map("g2", g2))
    parts.append(
        "return { n = n, kinds = kinds, gblob = gblob, cblob = cblob, "
        "goff = goff, coff = coff, kid = kid, "
        "pre1 = pre1, pre2 = pre2, last1 = last1, last2 = last2, g2 = g2 }\n"
    )
    write_text(overlay / "lua" / "commands_idx.lua", "".join(parts))


def gen_emoji(draft: Path, overlay: Path, mint_emoji: Path | None = None) -> None:
    lines: list[str] = []
    seen_keys: set[str] = set()
    if mint_emoji is not None and mint_emoji.is_file():
        for line in mint_emoji.read_text(encoding="utf-8").splitlines():
            lines.append(line)
            if "\t" in line:
                seen_keys.add(line.split("\t", 1)[0])
    seen_rows: set[str] = set(lines)
    for r in read_csv(draft / "emoji.csv"):
        glyph = r["glyph"]
        if is_ascii_glyph(glyph):
            continue
        keys: list[str] = []
        for field in ("zh_tts", "zh_keywords", "en_tts"):
            raw = r.get(field) or ""
            for part in re.split(r"[|,]", raw):
                kw = part.strip()
                if not kw or not emoji_cldr_key_ok(kw):
                    continue
                keys.append(kw)
        for kw in keys:
            if kw in seen_keys:
                continue
            row = f"{kw}\t{kw} {glyph}"
            if row in seen_rows:
                continue
            seen_keys.add(kw)
            seen_rows.add(row)
            lines.append(row)
    write_text(overlay / "opencc" / "emoji.txt", "\n".join(lines) + "\n")


def gen_overlay(root: Path, overlay: Path | None = None) -> None:
    root = root.resolve()
    draft = root / "docs" / "drafts"
    overlay = (overlay or (root / "overlay")).resolve()
    overlay.mkdir(parents=True, exist_ok=True)
    gen_kana(draft, overlay)
    gen_jp_romaji(draft, overlay)
    gen_latin(draft, overlay)
    gen_commands(draft, overlay)
    gen_emoji(draft, overlay, root / "proj-ref" / "oh-my-rime" / "opencc" / "emoji.txt")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--overlay", default=None)
    args = p.parse_args()
    root = Path(args.root)
    overlay = Path(args.overlay) if args.overlay else None
    gen_overlay(root, overlay)
    print("wrote", overlay or (root / "overlay"))


if __name__ == "__main__":
    main()
