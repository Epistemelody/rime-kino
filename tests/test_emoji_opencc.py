import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gen_overlay import emoji_cldr_key_ok, gen_overlay  # noqa: E402

MINT_EMOJI = ROOT / "proj-ref" / "oh-my-rime" / "opencc" / "emoji.txt"


def _keys(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        if "\t" not in line:
            continue
        out.add(line.split("\t", 1)[0])
    return out


def test_cldr_keys_reject_short_language_tokens():
    assert not emoji_cldr_key_ok("你")
    assert not emoji_cldr_key_ok("人")
    assert not emoji_cldr_key_ok("中国")
    assert not emoji_cldr_key_ok("ha")
    assert not emoji_cldr_key_ok("元")
    assert emoji_cldr_key_ok("inverted exclamation mark")
    assert emoji_cldr_key_ok("人民币")


def test_generated_emoji_keeps_mint_and_drops_short_cldr(tmp_path):
    out = tmp_path / "overlay"
    gen_overlay(ROOT, out)
    got = (out / "opencc" / "emoji.txt").read_text(encoding="utf-8")
    mint = MINT_EMOJI.read_text(encoding="utf-8")
    mint_keys = _keys(mint)
    got_keys = _keys(got)
    assert "哈哈" in got_keys
    assert "嘿嘿" in got_keys
    assert mint_keys <= got_keys
    for line in mint.splitlines():
        if "\t" in line:
            assert line in got.splitlines()
    extra = got_keys - mint_keys
    cjk_re = re.compile(r"^[\u4e00-\u9fff]+$")
    for key in extra:
        assert emoji_cldr_key_ok(key), key
        if cjk_re.fullmatch(key):
            assert len(key) >= 3
        assert key not in {"你", "人", "是", "元"}
