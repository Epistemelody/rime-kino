import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_overlay import build_romaji_map, gen_overlay, romaji_to_kana  # noqa: E402

DRAFT = ROOT / "docs" / "drafts"


def conv(s: str) -> str:
    hira, rest = romaji_to_kana(s, build_romaji_map(DRAFT))
    return hira + rest


def test_project_mozc_row_is_gone():
    import deploy

    assert not hasattr(deploy, "project_mozc_row")


def test_romaji_sentences():
    assert conv("konnichiha") == "こんにちは"
    assert conv("konnichiwa") == "こんにちわ"
    assert conv("toukyou") == "とうきょう"
    assert conv("shi") == "し"
    assert conv("si") == "し"
    assert conv("tsu") == "つ"
    assert conv("tu") == "つ"


def test_n_pending_and_sokuon():
    assert conv("n") == "ん"
    assert conv("nn") == "ん"
    assert conv("nna") == "んな"
    assert conv("kan") == "かん"
    assert conv("naka") == "なか"
    assert conv("kka") == "っか"
    assert conv("ka") == "か"


def test_gen_writes_jp_romaji(tmp_path):
    out = tmp_path / "overlay"
    gen_overlay(ROOT, out)
    text = (out / "lua" / "jp_romaji.lua").read_text(encoding="utf-8")
    assert '["ka"]' in text
    assert "か" in text
    assert "カ" in text


def test_uppercase_katakana():
    hira, rest = romaji_to_kana("KA", build_romaji_map(DRAFT))
    assert rest == ""
    assert hira == "カ"


def test_romaji_script_force_both_kana():
    mapping = build_romaji_map(DRAFT)
    assert romaji_to_kana("ka", mapping, script="kata") == ("カ", "")
    assert romaji_to_kana("KA", mapping, script="hira") == ("か", "")
    assert romaji_to_kana("konnichiha", mapping, script="kata") == ("コンニチハ", "")
    assert romaji_to_kana("kka", mapping, script="kata") == ("ッカ", "")
    assert romaji_to_kana("n", mapping, script="kata") == ("ン", "")
