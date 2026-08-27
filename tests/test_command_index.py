import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_overlay import (  # noqa: E402
    COMMAND_EXTRA,
    GRAM_N,
    SKIP_UNICODE_WORDS,
    collect_command_rows,
    command_code,
    iter_source_command_codes,
    pack_command_index,
    prefix_postings,
    split_codes,
    unicode_gram_source,
)


DRAFT = ROOT / "docs" / "drafts"


def _lua_lookup(packed, g2, q: str, *, kind_on=lambda k: True):
    """Mirror command_draft.lua infix: 2-gram posting then code:find."""
    q = q.lower()
    gram = q[:GRAM_N]
    hits = []
    for i in g2.get(gram, []):
        commit, code, kind = packed[i]
        if not kind_on(kind):
            continue
        if kind == "unicode" and len(q) < 4:
            continue
        if q in code:
            hits.append((commit, code, kind))
    return hits


def _scan_hits(packed, g2, q: str, *, kind_on=lambda k: True, limit=20):
    """Full-table scan; oracle for prefix-posting equality."""
    q = q.lower()
    scored: list[tuple[int, int, str]] = []
    seen: dict[str, int] = {}

    def add(score: int, i: int, commit: str) -> None:
        if commit in seen and seen[commit] <= score:
            return
        seen[commit] = score
        scored.append((score, i, commit))

    for i, (commit, code, kind) in enumerate(packed):
        if not kind_on(kind):
            continue
        if code == q:
            add(0, i, commit)
        elif code.startswith(q):
            add(1, i, commit)
        elif "." in code:
            last = code.rsplit(".", 1)[-1]
            if last.startswith(q):
                add(2, i, commit)

    if len(q) >= 2:
        for i in g2.get(q[:GRAM_N], []):
            commit, code, kind = packed[i]
            if not kind_on(kind):
                continue
            if kind == "unicode" and len(q) < 4:
                continue
            if q in code:
                add(3, i, commit)

    scored.sort(key=lambda h: (h[0], h[2]))
    out = []
    yielded: set[str] = set()
    for _score, i, _commit in scored:
        row = packed[i]
        if row[0] in yielded:
            continue
        yielded.add(row[0])
        out.append(row)
        if len(out) >= limit:
            break
    return out


def _command_hits(packed, g2, q: str, *, kind_on=lambda k: True, limit=20):
    """Mirror command_draft.lua four layers via prefix/last/g2 postings."""
    q = q.lower()
    maps = prefix_postings(packed)
    scored: list[tuple[int, int, str]] = []
    seen: dict[str, int] = {}

    def add(score: int, i: int, commit: str) -> None:
        if commit in seen and seen[commit] <= score:
            return
        seen[commit] = score
        scored.append((score, i, commit))

    if q:
        key = q[:2] if len(q) >= 2 else q[:1]
        bucket = maps["pre2" if len(q) >= 2 else "pre1"].get(key, [])
        for i in bucket:
            commit, code, kind = packed[i]
            if not kind_on(kind):
                continue
            if code == q:
                add(0, i, commit)
            elif code.startswith(q):
                add(1, i, commit)
        last_bucket = maps["last2" if len(q) >= 2 else "last1"].get(key, [])
        for i in last_bucket:
            commit, code, kind = packed[i]
            if not kind_on(kind):
                continue
            if "." in code:
                last = code.rsplit(".", 1)[-1]
                if last.startswith(q):
                    add(2, i, commit)

    if len(q) >= 2:
        for i in g2.get(q[:GRAM_N], []):
            commit, code, kind = packed[i]
            if not kind_on(kind):
                continue
            if kind == "unicode" and len(q) < 4:
                continue
            if q in code:
                add(3, i, commit)

    scored.sort(key=lambda h: (h[0], h[2]))
    out = []
    yielded: set[str] = set()
    for _score, i, _commit in scored:
        row = packed[i]
        if row[0] in yielded:
            continue
        yielded.add(row[0])
        out.append(row)
        if len(out) >= limit:
            break
    return out


def _packed():
    return pack_command_index(collect_command_rows(DRAFT))


def test_split_codes_keeps_pipe_arrows():
    assert split_codes("-> | |->") == ["->", "|->"]
    assert split_codes("si | shi") == ["si", "shi"]
    assert split_codes("|") == ["|"]
    assert split_codes("|| | ||||") == ["||", "||||"]


def test_gram_width_matches_lua_lookup():
    assert GRAM_N == 2


def test_unicode_infix_finds_kept_name_words_not_filler():
    packed, g2 = _packed()
    alpha = next(r for r in packed if r[1] == "greeksmallletteralpha" and r[2] == "unicode")
    src = unicode_gram_source("α")
    assert "alpha" in src
    assert "letter" not in src
    assert "small" not in src
    hits = _lua_lookup(packed, g2, "alpha")
    assert any(h[0] == alpha[0] and h[2] == "unicode" for h in hits)
    filler = _lua_lookup(packed, g2, "letter")
    assert not any(h[1] == "greeksmallletteralpha" for h in filler)


def test_skip_words_are_the_unicode_filler_inventory():
    for w in ("of", "small", "letter", "capital"):
        assert w in SKIP_UNICODE_WORDS


def test_prefix_postings_match_full_scan():
    packed, g2 = _packed()
    for q in ("a", "al", "alpha", "l", "arrow", "pha", "sin", "frac", "rightarrow"):
        scan = [h[0] for h in _scan_hits(packed, g2, q)]
        pref = [h[0] for h in _command_hits(packed, g2, q)]
        assert scan == pref, q


def test_infix_postings_are_not_capped():
    packed, g2 = _packed()
    assert max(len(v) for v in g2.values()) > 80
    late = next(i for i, row in enumerate(packed) if row[2].startswith("typst") and i > 80)
    commit, code, kind = packed[late]
    if len(code) >= GRAM_N:
        gram = code[:GRAM_N]
        assert late in g2[gram], (code, kind, gram)


def test_latex_superscript_codes_are_command_codes():
    assert command_code("^2")
    assert command_code("_2")
    packed, _ = _packed()
    codes = {row[1] for row in packed}
    assert "^2" in codes
    assert "_2" in codes


def test_lean_mma_kinds_and_no_bracket_alpha():
    packed, _ = _packed()
    kinds = {row[2] for row in packed}
    assert "latex-alias" in kinds
    assert "lean" in kinds
    assert "lean-shorthand" in kinds
    assert "mma" in kinds
    assert "katex" in kinds
    codes = {row[1] for row in packed}
    assert "[alpha]" not in codes
    assert not any(c == f"[{name}]" for c in codes for name in ("alpha", "Alpha"))


def test_plus_is_latex_alias_not_native():
    packed, _ = _packed()
    kinds = {row[2] for row in packed if row[0] == "+" and row[1] == "plus"}
    assert "latex-alias" in kinds
    assert "latex" not in kinds
    alpha_alias = {row[2] for row in packed if row[0] == "α" and row[1] == "alpha"}
    assert "latex-alias" not in alpha_alias


def test_alpha_code_has_multiple_dialects():
    packed, _ = _packed()
    kinds = {row[2] for row in packed if row[0] == "α" and row[1] == "alpha"}
    assert {"latex", "katex", "typst-sym", "lean", "mma"} <= kinds
    a_kinds = {row[2] for row in packed if row[0] == "α" and row[1] == "a"}
    assert a_kinds == {"lean-shorthand"}


def test_alpha_query_yields_both_greek_glyphs():
    packed, g2 = _packed()
    for q in ("alpha", "Alpha"):
        hits = _command_hits(packed, g2, q)
        glyphs = {h[0] for h in hits}
        assert "α" in glyphs, q
        assert "Α" in glyphs, q
    a_hits = _command_hits(packed, g2, "a")
    assert any(h[0] == "α" for h in a_hits)


def test_arrow_and_relation_codes():
    packed, g2 = _packed()
    def glyphs(q):
        return {h[0] for h in _command_hits(packed, g2, q)}

    assert "→" in glyphs("->")
    assert "→" in glyphs("to")
    assert "≠" in glyphs("!=")
    assert "↦" in glyphs("|->")
    assert "∀" in glyphs("forall")
    assert "∀" in glyphs("all")
    assert "²" in glyphs("^2")


def test_frac_sin_pha_still_resolve():
    packed, g2 = _packed()
    frac = _command_hits(packed, g2, "frac")
    assert any(h[0] in {"frac", "⁄"} or h[1] == "frac" for h in frac)
    sin = _command_hits(packed, g2, "sin")
    assert any(h[0] == "sin" or h[1] == "sin" for h in sin)
    pha = _command_hits(packed, g2, "pha")
    assert any(h[0] == "α" for h in pha)


def test_every_source_code_is_in_the_index():
    packed, _ = _packed()
    idx = {row[1] for row in packed}
    missing = []
    for code in iter_source_command_codes(DRAFT):
        if code.lower() not in idx:
            missing.append(code)
    assert missing == []


def test_command_extra_covers_source_punct_and_runtime():
    punct = set()
    for code in iter_source_command_codes(DRAFT):
        for c in code:
            if c and not c.isalnum() and c not in " \\":
                punct.add(c)
                assert c in COMMAND_EXTRA, (c, code)
    keys = (ROOT / "overlay" / "lua" / "command_keys.lua").read_text(encoding="utf-8")
    extras_m = re.search(r'\["\\\\"\]\s*=\s*\[=\[(.*?)\]=\]', keys, re.S)
    assert extras_m, keys
    extras = extras_m.group(1)
    assert extras == COMMAND_EXTRA
    mint = (ROOT / "overlay" / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    line = next(ln for ln in mint.splitlines() if "recognizer/patterns/command_draft:" in ln)
    raw = json.loads(line.split(": ", 1)[1])
    pat = re.compile(raw)
    assert pat.match("\\")
    assert pat.match("\\alpha")
    assert pat.match("\\Alpha")
    assert pat.match("\\->")
    assert not pat.match("alpha")
    for c in COMMAND_EXTRA:
        assert pat.match("\\" + c), (c, raw)


def _table_fallback_keep(packed, commit: str, q: str, kind_on) -> bool:
    """Mirror feature_gate: table_translator exact code, gated by that code's kinds."""
    q = q.lower()
    kinds = [k for c, code, k in packed if c == commit and code == q]
    return any(kind_on(k) for k in kinds)


def test_lean_off_keeps_latex_alpha():
    packed, g2 = _packed()
    nolean = lambda k: not k.startswith("lean")
    hits = _command_hits(packed, g2, "alpha", kind_on=nolean)
    assert any(h[0] == "α" and h[2] == "latex" for h in hits)
    a_lean = _command_hits(packed, g2, "a")
    assert any(h[2] == "lean-shorthand" and h[0] == "α" for h in a_lean)
    a_off = _command_hits(packed, g2, "a", kind_on=nolean)
    assert not any(h[2].startswith("lean") for h in a_off)
    a_kinds = {k for c, code, k in packed if c == "α" and code == "a"}
    assert a_kinds == {"lean-shorthand"}
    assert _table_fallback_keep(packed, "α", "a", lambda k: True)
    assert not _table_fallback_keep(packed, "α", "a", nolean)
    assert _table_fallback_keep(packed, "α", "alpha", nolean)


def test_unicode_stays_when_dialects_off():
    packed, g2 = _packed()
    only_unicode = lambda k: k == "unicode"
    hits = _command_hits(packed, g2, "alpha", kind_on=only_unicode)
    assert any(h[0] == "α" and h[2] == "unicode" for h in hits)
    assert not _table_fallback_keep(packed, "α", "alpha", only_unicode)
    assert not _table_fallback_keep(packed, "α", "a", only_unicode)
    compact = next(
        code for commit, code, kind in packed if commit == "α" and kind == "unicode"
    )
    assert _table_fallback_keep(packed, "α", compact, only_unicode)
    assert any(h[0] == "α" for h in _command_hits(packed, g2, compact, kind_on=only_unicode))
