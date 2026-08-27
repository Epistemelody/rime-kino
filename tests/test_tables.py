import csv
from pathlib import Path

DRAFT = Path(__file__).resolve().parents[1] / "docs" / "drafts"

WIDE_COLS = {
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
}


def rows(name):
    with (DRAFT / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def r_codes(r):
    return [c.strip() for c in r["codes"].split(" | ") if c.strip()]


def cell_codes(raw):
    return [c.strip() for c in (raw or "").split(" | ") if c.strip()]


def test_required_tables_exist():
    for n in [
        "kana.csv",
        "latin-accents.csv",
        "math-symbols.csv",
        "typst-extra.csv",
        "punctuation.csv",
        "brackets.csv",
        "emoji.csv",
    ]:
        assert (DRAFT / n).is_file(), n
    assert (DRAFT / "import" / "lean-abbreviations.json").is_file()
    assert (DRAFT / "import" / "mma-named.json").is_file()
    assert (DRAFT / "import" / "katex-symbols.json").is_file()
    for retired in ("latex.csv", "math-catalog.csv", "typst-shorthand.csv"):
        assert not (DRAFT / retired).exists(), retired
    assert not (DRAFT / "commands.csv").exists()
    assert not (DRAFT / "kana.expanded.csv").exists()
    assert not (DRAFT / "emoji.core.csv").exists()


def test_math_symbols_alpha_arrow_forall():
    rs = rows("math-symbols.csv")
    assert len(rs) > 2000
    assert WIDE_COLS <= set(rs[0].keys())
    alpha = next(r for r in rs if r["glyph"] == "α")
    assert "alpha" in cell_codes(alpha["latex"])
    assert "alpha" in cell_codes(alpha["katex"])
    assert "alpha" not in cell_codes(alpha["latex_alias"])
    plus = next(r for r in rs if r["glyph"] == "+")
    assert "plus" in cell_codes(plus["latex_alias"])
    assert "plus" not in cell_codes(plus["latex"])
    clam = next(r for r in rs if r["glyph"] == "!")
    assert "clam" in cell_codes(clam["latex_alias"])
    assert "a" in cell_codes(alpha["lean_shorthand"])
    assert "alpha" in cell_codes(alpha["lean"])
    assert "Alpha" in cell_codes(alpha["mma"])
    assert not any(c.startswith("[") for c in cell_codes(alpha["mma"]))
    cap = next(r for r in rs if r["glyph"] == "Α")
    assert "Alpha" in cell_codes(cap["latex"]) or "Alpha" in cell_codes(cap["lean"])
    assert "CapitalAlpha" in cell_codes(cap["mma"])
    arrow = next(r for r in rs if r["glyph"] == "→")
    assert "->" in cell_codes(arrow["typst_shorthand"])
    lean_arrow = cell_codes(arrow["lean"]) + cell_codes(arrow["lean_shorthand"])
    assert "to" in lean_arrow or "->" in lean_arrow
    assert "->" in cell_codes(arrow["mma_alias"]) or "->" in cell_codes(arrow["typst_shorthand"])
    forall = next(r for r in rs if r["glyph"] == "∀")
    lean_fa = cell_codes(forall["lean"]) + cell_codes(forall["lean_shorthand"])
    assert "forall" in lean_fa and "all" in lean_fa


def test_math_symbols_codes_have_no_backslash():
    for r in rows("math-symbols.csv"):
        for col in WIDE_COLS - {"glyph"}:
            for code in cell_codes(r[col]):
                assert "\\" not in code, (r["glyph"], col, code)
                assert " " not in code, (r["glyph"], col, code)


def test_kana_has_hira_and_codes():
    rs = rows("kana.csv")
    assert len(rs) >= 390
    assert {"hira", "kata", "codes", "family"} <= set(rs[0].keys())
    ka = next(r for r in rs if r["kata"] == "カ")
    assert "ka" in r_codes(ka)
    shi = next(r for r in rs if r["kata"] == "シ")
    assert "si" in r_codes(shi) and "shi" in r_codes(shi)


def test_brackets_follow_cloverplus():
    rs = rows("brackets.csv")
    corner = next(r for r in rs if r["kind"] == "corner")
    assert corner["primary_left"] == "「"
    white = next(r for r in rs if r["kind"] == "white-corner")
    assert white["primary_left"] == "『"
    paren = next(r for r in rs if r["kind"] == "paren")
    assert paren["primary_left"] == "（"
    rec = {r["key"]: r["recommend"] for r in rows("punctuation.csv")}
    assert rec["["].startswith("「")
    assert rec["'"].startswith("「")
    qs = next(r for r in rs if r["kind"] == "quote-single")
    assert qs["primary_left"] == "「"
    assert qs["primary_right"] == "」"


def test_typst_extra_has_frac_and_sin():
    rs = rows("typst-extra.csv")
    assert any(r["code"] == "frac" and r["kind"] == "typst-fn" for r in rs)
    assert any(r["code"] == "sin" and r["kind"] == "typst-op" for r in rs)


def test_math_symbols_shorthand_arrows():
    by_glyph = {r["glyph"]: r for r in rows("math-symbols.csv")}
    assert "->" in cell_codes(by_glyph["→"]["typst_shorthand"])
    assert "..." in cell_codes(by_glyph["…"]["typst_shorthand"])
    assert "!=" in cell_codes(by_glyph["≠"]["typst_shorthand"])
    assert "|->" in cell_codes(by_glyph["↦"]["typst_shorthand"])


def test_mint_custom_wires_command_and_latin():
    root = Path(__file__).resolve().parents[1]
    text = (root / "overlay" / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert "command_draft" in text
    assert "table_translator@latin" in text
    assert "lua_filter@*jp_draft@jp_draft" in text
    assert "lua_translator@*jp_draft" not in text
    assert "「" in text
    assert 'pair: ["「", "」"]' in text
    assert 'pair: ["[", "]"]' not in text


def test_latin_accents_semicolon_prefix():
    rs = rows("latin-accents.csv")
    enye = next(r for r in rs if r["glyph"] == "ñ")
    assert ";n" in r_codes(enye)
    aacute = next(r for r in rs if r["glyph"] == "á")
    assert ";a" in r_codes(aacute)
    semi = next(r for r in rs if r["glyph"] == "；")
    assert ";;" in r_codes(semi)
