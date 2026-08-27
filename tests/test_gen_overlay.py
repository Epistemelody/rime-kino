import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_overlay import gen_overlay, kana_code_entries  # noqa: E402


def test_kana_code_entries_exposes_both_scripts():
    assert kana_code_entries("か", "カ", "ka") == [
        ("か", "ka"),
        ("カ", "ka"),
        ("カ", "KA"),
        ("か", "KA"),
    ]
    assert kana_code_entries("ー", "ー", "-") == [("ー", "-")]
    assert kana_code_entries("し", "シ", "si") == [
        ("し", "si"),
        ("シ", "si"),
        ("シ", "SI"),
        ("し", "SI"),
    ]


def test_gen_writes_kana_commands_emoji(tmp_path):
    out = tmp_path / "overlay"
    gen_overlay(ROOT, out)
    kana = (out / "kana.dict.yaml").read_text(encoding="utf-8")
    assert "name: kana" in kana
    assert "あ\ta" in kana
    assert "ア\tA" in kana
    assert "ア\ta" in kana
    assert "あ\tA" in kana
    assert kana.index("か\tka") < kana.index("カ\tka")
    assert kana.index("カ\tKA") < kana.index("か\tKA")
    assert "シ\tsi" in kana
    assert "し\tSI" in kana
    assert "っか\tkka" in kana
    assert "ッカ\tkka" in kana
    assert "っか\tKKA" in kana
    cmds = (out / "commands.dict.yaml").read_text(encoding="utf-8")
    assert "name: commands" in cmds
    assert "α\talpha" in cmds
    assert "α\ta" in cmds
    assert "→\t->" in cmds
    assert "…\t..." in cmds
    body = cmds.split("...", 1)[-1]
    assert "\\alpha" not in body
    latin = (out / "latin.dict.yaml").read_text(encoding="utf-8")
    assert "name: latin" in latin
    assert "ñ\tn" in latin
    assert "；\t;" in latin
    latin_body = latin.split("...", 1)[-1]
    assert ";\t;" not in latin_body
    assert "～\t~" not in kana
    emoji = (out / "opencc" / "emoji.txt").read_text(encoding="utf-8")
    assert "嘿嘿" in emoji
    idx = (out / "lua" / "commands_idx.lua").read_text(encoding="utf-8")
    assert "alpha" in idx
    assert "pha" in idx or "[\"ph\"]" in idx or "['ph']" in idx
    assert not (ROOT / "docs" / "drafts" / "commands.csv").exists()
