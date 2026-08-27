from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "overlay"


def test_preedit_stays_in_candidate_window():
    default = (OVERLAY / "default.custom.yaml").read_text(encoding="utf-8")
    assert "style/inline_preedit: false" in default
    weasel = (OVERLAY / "weasel.custom.yaml").read_text(encoding="utf-8")
    assert "inline_preedit: false" in weasel
    rime_conf = (ROOT / "platform" / "fcitx5" / "conf" / "rime.conf").read_text(
        encoding="utf-8"
    )
    assert 'PreeditMode="Do not show"' in rime_conf
    assert 'SwitchInputMethodBehavior="Commit raw input"' in rime_conf
    assert "ascii_composer/switch_key/Shift_L: commit_code" in default


def test_kino_feature_switches_default_on():
    mint = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    default = (OVERLAY / "default.custom.yaml").read_text(encoding="utf-8")
    feat = (OVERLAY / "lua" / "kino_features.lua").read_text(encoding="utf-8")
    cmd = (OVERLAY / "lua" / "command_draft.lua").read_text(encoding="utf-8")
    jp = (OVERLAY / "lua" / "jp_draft.lua").read_text(encoding="utf-8")
    gate = (OVERLAY / "lua" / "feature_gate.lua").read_text(encoding="utf-8")
    for name in (
        "kino_typst",
        "kino_latex",
        "kino_katex",
        "kino_lean",
        "kino_mma",
        "kino_latin",
        "kino_japanese",
    ):
        assert f"name: {name}" in mint
        assert "reset: 1" in mint.split(f"name: {name}", 1)[1][:80]
        assert name in default
        assert name in feat
    assert "emoji_suggestion" in mint
    assert "lua_filter@*feature_gate" in mint
    assert "feat.kind_on" in cmd
    assert 'pcall(require, "kino_features")' in cmd
    assert "feat.JAPANESE" in jp
    assert "feat.LATIN" in gate
    assert "kinds_by_code" in gate
    assert "command_query" in gate
    assert 'kind:sub(1, 5) == "typst"' in feat
    assert 'kind:sub(1, 5) == "latex"' in feat
    assert 'kind == "katex"' in feat
    assert 'kind:sub(1, 4) == "lean"' in feat
    assert 'kind:sub(1, 3) == "mma"' in feat


def test_mint_display_name_is_kino_and_page_size_is_full():
    text = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert "schema/name: kino" in text
    assert "menu/page_size: 10" in text


def test_repository_name_is_rime_kino():
    files = [
        ROOT / "README.md",
        ROOT / "README.en.md",
        ROOT / "docs" / "README.md",
        ROOT / "docs" / "README.en.md",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "rime-epic" not in text, path
        assert "rime-kino" in text, path
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/Epistemelody/rime-kino.git" in readme
    assert "https://epistemelody.github.io/rime-kino/" in readme
    assert "https://github.com/gkovacs/rime-spanish" in readme
    assert "fvalle1/rime-spanish" not in readme
    assert "https://github.com/iamcheyan/rime" in readme
    assert "https://github.com/tumuyan/rime-pinyin-jap" in readme
    assert "https://github.com/fkxxyz/rime-cloverpinyin" in readme
    assert "https://github.com/shenlebantongying/rime_latex" in readme
    assert "proj-arc/cloverplus" in readme
    assert "本地定制归档" in readme
    assert "不是对其中任一上游的完整依赖" in (ROOT / "docs" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "Linux%20%7C%20Windows%20%7C%20macOS" in readme
    assert "author       = {Felidz and {Epistemelody}}" in readme
    assert "github.com/felidz/rime-kino" not in readme
    assert "cofelid@" not in readme
    en = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert "https://github.com/gkovacs/rime-spanish" in en
    assert "fvalle1/rime-spanish" not in en
    assert "https://github.com/shenlebantongying/rime_latex" in en
    assert "Linux%20%7C%20Windows%20%7C%20macOS" in en
    assert "author       = {Felidz and {Epistemelody}}" in en
    assert "github.com/felidz/rime-kino" not in en
    assert "cofelid@" not in en


def test_no_personal_repo_or_email_in_tracked_files():
    import subprocess

    listed = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT, text=True
    ).split("\0")
    hits = []
    for rel in listed:
        if not rel or rel.startswith("proj-ref/") or rel.startswith("tests/"):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "github.com/felidz/rime-kino" in text or "cofelid@" in text.lower():
            hits.append(rel)
    assert hits == []


def test_web_docs_site_files_and_sidebar_targets():
    assert (ROOT / "index.html").is_file()
    assert (ROOT / ".nojekyll").is_file()
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "docsify" in html
    assert 'homepage: "docs/home.md"' in html
    assert (ROOT / "docs" / "home.md").is_file()
    assert (OVERLAY / "squirrel.custom.yaml").is_file()
    sidebar = (ROOT / "_sidebar.md").read_text(encoding="utf-8")
    targets = []
    for line in sidebar.splitlines():
        if "](" not in line:
            continue
        path = line.split("](", 1)[1].rsplit(")", 1)[0].strip()
        if path.startswith("http") or path == "/":
            continue
        targets.append(path.lstrip("/"))
    assert targets, sidebar
    for path in targets:
        assert (ROOT / path).is_file(), path


def test_gitignore_excludes_agent_tooling():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for name in (
        ".agents/",
        ".claude/",
        ".cursor/",
        ".pi/",
        ".trellis/",
        "docs/superpowers/",
        "AGENTS.md",
    ):
        assert name in text, name


def test_mint_disables_fuzzy_pinyin_and_typo_algebra():
    text = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert "translator/enable_correction: false" in text
    assert "speller/algebra:" in text
    assert "$1gn" not in text
    assert "hzi" not in text
    assert "abbrev/^([a-z]).+$/$1/" in text
    assert "xlit/" in text


def test_mint_input_length_is_not_capped_at_25():
    text = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert "codeLengthLimit_processor: 256" in text


def test_command_candidate_comment_is_code_and_dialect():
    cmd = (OVERLAY / "lua" / "command_draft.lua").read_text(encoding="utf-8")
    assert "comment_for(idx, ctx, row[1], row[2])" in cmd
    assert 'table.concat(dialects, " ")' in cmd
    assert 'Candidate("cmd", seg.start, seg._end, row[1], row[2])' not in cmd
    assert 'Candidate("cmd", seg.start, seg._end, row[1], row[3])' not in cmd


def test_backslash_offers_ideographic_comma_not_slash():
    mint = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert '"/": "、"' not in mint
    assert '"/": ["/", "÷"]' in mint or '"/": ["/", "／", "÷"]' in mint
    cmd = (OVERLAY / "lua" / "command_draft.lua").read_text(encoding="utf-8")
    assert "、" in cmd
    kana = (OVERLAY / "kana.schema.yaml").read_text(encoding="utf-8")
    assert "- recognizer" in kana
    assert "table_translator@kana" in mint


def test_command_and_jp_lua_accept_stripped_prefix():
    cmd = (OVERLAY / "lua" / "command_draft.lua").read_text(encoding="utf-8")
    assert 'has_tag("command_draft")' in cmd
    jp = (OVERLAY / "lua" / "jp_draft.lua").read_text(encoding="utf-8")
    assert 'has_tag("kana")' in jp
    # Kanji: lazy Memory(jp) + ReverseLookup(kagiroi_matrix) + kagiroi Viterbi.
    # Component.Translator+dummy Segment yields no candidates on librime 1.14.
    assert "Memory(" in jp
    assert 'require("kagiroi/kagiroi_viterbi")' in jp
    assert "best_n" in jp
    assert "ReverseLookup" in jp
    assert "Component.Translator" not in jp
    assert 'require("kagiroi/kagiroi_translator")' not in jp
    assert 'require("kagiroi/kagiroi_kana_speller")' not in jp
    init_fn = jp.split("function M.init", 1)[1].split("function M.fini", 1)[0]
    assert "Memory(" not in init_fn
    assert "ReverseLookup" not in init_fn
    assert 'require("kagiroi/kagiroi_viterbi")' not in init_fn
    assert "lex.candidate" in jp
    assert 'text:match("|%-?%d+ %-?%d+")' in jp


def test_kana_is_hung_on_mint_with_tilde_prefix():
    text = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert "lua_translator@*jp_draft" in text
    assert "table_translator@kana" in text
    assert "affix_segmentor@kana" in text
    assert 'prefix: "~"' in text
    assert "recognizer/patterns/kana:" in text
    assert "kagiroi_matrix" in text
    jp_schema = (OVERLAY / "jp.schema.yaml").read_text(encoding="utf-8")
    assert "kagiroi_matrix" in jp_schema
    assert "enable_user_dict: false" in jp_schema
    jp_dict = (OVERLAY / "jp.dict.yaml").read_text(encoding="utf-8")
    assert "import_tables:" in jp_dict
    assert "kagiroi.mozc" in jp_dict
    default = (ROOT / "overlay" / "default.custom.yaml").read_text(encoding="utf-8")
    assert "- schema: kagiroi" not in default
    assert "- schema: jp" not in default


def test_latin_and_kana_affix_before_abc_and_latin_not_in_switcher():
    mint = (OVERLAY / "rime_mint.custom.yaml").read_text(encoding="utf-8")
    assert mint.find("affix_segmentor@latin") < mint.find("- abc_segmentor")
    assert mint.find("affix_segmentor@kana") < mint.find("- abc_segmentor")
    assert '"punctuator/full_shape/~": "~"' in mint
    assert '"punctuator/full_shape/;": ";"' in mint
    assert '"punctuator/full_shape/\\\\": "\\\\"' in mint
    default = (OVERLAY / "default.custom.yaml").read_text(encoding="utf-8")
    assert "- schema: latin" not in default
    assert "lua_processor@*command_keys" in mint
    assert mint.find("lua_processor@*command_keys") < mint.find("- punctuator")
    # mint default.yaml binds period/equal to page while has_menu; command_keys
    # must see those keys first or Typst names like arrow.l lose the dot.
    assert mint.find("lua_processor@*command_keys") < mint.find("- key_binder")
    keys = (OVERLAY / "lua" / "command_keys.lua").read_text(encoding="utf-8")
    assert 'period = "."' in keys
    assert 'question = "?"' in keys
    assert "asciicircum" in keys
    assert "braceleft" in keys
    assert "slash" in keys
    assert '[";"]' in keys
    assert '["~"]' in keys
    alpha = next(
        line for line in mint.splitlines() if line.startswith("  speller/alphabet:")
    )
    suffix = alpha.split("CBA", 1)[1]
    assert "?" not in suffix
    assert "-" not in suffix
    assert "~" in suffix and ";" in suffix
    kana_block = mint.split("  kana:\n", 1)[1].split("  punctuator", 1)[0]
    assert "enable_sentence: false" in kana_block
    assert "enable_sentence: true" not in kana_block
    assert "^_+" in mint


def test_weasel_has_dark_nord_scheme():
    text = (OVERLAY / "weasel.custom.yaml").read_text(encoding="utf-8")
    assert "color_scheme: kino_dark" in text
    assert "color_scheme_dark: kino_dark" in text
    assert "kino_dark:" in text
    assert "0xECEFF4" in text
    assert "0x2E3440" in text


def test_deploy_forces_kino_dark_theme():
    deploy = (ROOT / "scripts" / "deploy.py").read_text(encoding="utf-8")
    assert '"Theme": "kino-dark"' in deploy
    assert '"DarkTheme": "kino-dark"' in deploy
    assert "def patch_classicui_theme" in deploy


def test_fcitx5_dark_theme_ports_nord_night():
    conf = (
        ROOT / "platform" / "fcitx5" / "themes" / "kino-dark" / "theme.conf"
    ).read_text(encoding="utf-8")
    assert "Name=kino-dark" in conf
    assert "#ECEFF4" in conf
    assert "#2E3440" in conf
    assert "#8FBCBB" in conf


def test_default_and_extra_schemas_page_size_10():
    default = (OVERLAY / "default.custom.yaml").read_text(encoding="utf-8")
    assert "menu/page_size: 10" in default
    for name in ("kana.schema.yaml", "latin.schema.yaml"):
        body = (OVERLAY / name).read_text(encoding="utf-8")
        assert "page_size: 10" in body


def test_weasel_custom_uses_cloverplus_nord_as_kino():
    text = (OVERLAY / "weasel.custom.yaml").read_text(encoding="utf-8")
    assert "color_scheme: kino" in text
    assert "0x2E3440" in text
    assert "0x8fbcbbba" in text or "0x8FBCBB" in text
    assert "0xeceff4c2" in text or "0xECEFF4" in text


def test_fcitx5_theme_ports_same_nord():
    conf = (ROOT / "platform" / "fcitx5" / "themes" / "kino" / "theme.conf").read_text(
        encoding="utf-8"
    )
    assert "Name=kino" in conf
    assert "#2E3440" in conf
    assert "#ECEFF4" in conf
    assert "#8FBCBB" in conf
