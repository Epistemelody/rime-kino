import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from deploy import fcitx5_themes_dir, rime_user_dir  # noqa: E402


def test_linux_rime_dir(monkeypatch):
    monkeypatch.delenv("RIME_DIR", raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("HOME", "/home/u")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/u")))
    assert rime_user_dir() == Path("/home/u/.local/share/fcitx5/rime")


def test_windows_rime_dir(monkeypatch):
    monkeypatch.delenv("RIME_DIR", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\u\AppData\Roaming")
    assert rime_user_dir() == Path(r"C:\Users\u\AppData\Roaming") / "Rime"


def test_macos_rime_dir(monkeypatch):
    monkeypatch.delenv("RIME_DIR", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/Users/u")))
    assert rime_user_dir() == Path("/Users/u/Library/Rime")


def test_rime_dir_override(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    assert rime_user_dir() == tmp_path


def test_theme_skipped_when_rime_dir_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("RIME_DIR", str(tmp_path))
    monkeypatch.delenv("FCITX5_THEME_DIR", raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    assert fcitx5_themes_dir() is None


def test_classicui_theme_created_when_missing(tmp_path):
    from deploy import patch_classicui_theme

    conf = tmp_path / "classicui.conf"
    patch_classicui_theme(conf)
    text = conf.read_text(encoding="utf-8")
    assert "Theme=kino-dark" in text
    assert "DarkTheme=kino-dark" in text
    assert "UseDarkTheme=False" in text
    assert "UseAccentColor=False" in text


def test_legacy_seed_boost_forces_mozc_recopy(tmp_path):
    from deploy import has_legacy_seed_boost, keep_existing_heavy_dict

    dest = tmp_path / "kagiroi.mozc.dict.yaml"
    dest.write_bytes(
        b"---\nname: kagiroi.mozc\n...\n\n"
        + b"x" * 1_000_001
        + "今日|1913 1913\tきょう\t100000\n".encode()
    )
    assert has_legacy_seed_boost(dest) is True
    assert keep_existing_heavy_dict(dest, kind="mozc") is False


def _stub_kagiroi_sources(tmp_path, monkeypatch):
    import deploy

    src = tmp_path / "kagiroi-src"
    lua = src / "lua" / "kagiroi"
    lua.mkdir(parents=True)
    (src / "kagiroi.mozc.dict.yaml").write_text(
        "---\nname: kagiroi.mozc\n...\n\n今日|1913 1913\tきょう\t121\n",
        encoding="utf-8",
    )
    (src / "kagiroi_matrix.dict.yaml").write_text(
        "---\nname: kagiroi_matrix\n...\n\n1913 1851\t10\n",
        encoding="utf-8",
    )
    (src / "kagiroi_matrix.schema.yaml").write_text(
        "schema:\n  schema_id: kagiroi_matrix\nengine:\ntranslator:\n  dictionary: kagiroi_matrix\n",
        encoding="utf-8",
    )
    (src / "LICENSE").write_text("GNU GENERAL PUBLIC LICENSE\nVersion 3\n", encoding="utf-8")
    (lua / "kagiroi_viterbi.lua").write_text("-- viterbi\n", encoding="utf-8")
    (lua / "kagiroi.lua").write_text("-- kagiroi\n", encoding="utf-8")
    (lua / "segmenter.lua").write_text("-- segmenter\n", encoding="utf-8")
    (lua / "lru.lua").write_text("-- lru\n", encoding="utf-8")
    (lua / "priority_queue.lua").write_text("-- pq\n", encoding="utf-8")
    (lua / "kagiroi_translator.lua").write_text("-- do not copy\n", encoding="utf-8")
    (lua / "kagiroi_kana_speller.lua").write_text("-- do not copy\n", encoding="utf-8")
    monkeypatch.setattr(deploy, "KAGIROI_ROOT", src)
    monkeypatch.setattr(deploy, "MOZC", src / "kagiroi.mozc.dict.yaml")
    monkeypatch.setattr(deploy, "MATRIX_DICT", src / "kagiroi_matrix.dict.yaml")
    monkeypatch.setattr(deploy, "MATRIX_SCHEMA", src / "kagiroi_matrix.schema.yaml")
    monkeypatch.setattr(deploy, "KAGIROI_LUA_DIR", lua)
    monkeypatch.setattr(deploy, "KAGIROI_LICENSE", src / "LICENSE")
    return src


def test_deploy_jp_assets_force_keeps_ids_and_lua(tmp_path, monkeypatch):
    from deploy import deploy_jp_assets

    _stub_kagiroi_sources(tmp_path, monkeypatch)
    monkeypatch.setenv("FORCE_JP_DICT", "1")
    monkeypatch.delenv("SKIP_JP_DICT", raising=False)
    monkeypatch.setenv("RIME_DIR", str(tmp_path / "unused-rime-dir"))
    dest = tmp_path / "dest"
    dest.mkdir()
    leftover = dest / "lua" / "kagiroi"
    leftover.mkdir(parents=True)
    (leftover / "kagiroi_translator.lua").write_text("-- leftover\n", encoding="utf-8")
    deploy_jp_assets(dest)
    mozc = (dest / "kagiroi.mozc.dict.yaml").read_text(encoding="utf-8")
    assert "今日|1913 1913\tきょう\t121" in mozc
    assert "今日|1913 1913\tきょう\t100000" not in mozc
    assert "name: kagiroi_matrix" in (dest / "kagiroi_matrix.dict.yaml").read_text(
        encoding="utf-8"
    )
    assert (dest / "lua" / "kagiroi" / "kagiroi_viterbi.lua").is_file()
    assert (dest / "LICENSE.kagiroi").is_file()
    assert not (dest / "lua" / "kagiroi" / "kagiroi_translator.lua").exists()
    assert not (dest / "lua" / "kagiroi" / "kagiroi_kana_speller.lua").exists()
    wrapper = (dest / "jp.dict.yaml").read_text(encoding="utf-8")
    assert "import_tables:" in wrapper
    assert "kagiroi.mozc" in wrapper
    assert "今日\tきょう" not in wrapper


def test_deploy_jp_assets_rime_dir_skips_heavy(tmp_path, monkeypatch):
    from deploy import deploy_jp_assets

    _stub_kagiroi_sources(tmp_path, monkeypatch)
    monkeypatch.setenv("RIME_DIR", str(tmp_path / "dry"))
    monkeypatch.delenv("FORCE_JP_DICT", raising=False)
    dest = tmp_path / "dry"
    dest.mkdir()
    (dest / "jp.dict.yaml").write_text(
        "---\nname: jp\n...\n\n今日\tきょう\t10\n", encoding="utf-8"
    )
    build = dest / "build"
    build.mkdir()
    stale = build / "jp.table.bin"
    stale.write_bytes(b"stripped-projection")
    (build / "rime_mint.schema.yaml").write_text("keep\n", encoding="utf-8")
    deploy_jp_assets(dest)
    assert not (dest / "kagiroi.mozc.dict.yaml").exists()
    assert not (dest / "lua" / "kagiroi" / "kagiroi_viterbi.lua").exists()
    wrapper = (dest / "jp.dict.yaml").read_text(encoding="utf-8")
    assert "import_tables:" in wrapper
    assert "kagiroi.mozc" in wrapper
    assert "今日\tきょう" not in wrapper
    assert not stale.exists()
    assert (build / "rime_mint.schema.yaml").is_file()


def test_deploy_jp_assets_replaces_stripped_projection(tmp_path, monkeypatch):
    from deploy import deploy_jp_assets

    _stub_kagiroi_sources(tmp_path, monkeypatch)
    monkeypatch.setenv("FORCE_JP_DICT", "1")
    monkeypatch.delenv("SKIP_JP_DICT", raising=False)
    dest = tmp_path / "live"
    dest.mkdir()
    (dest / "jp.dict.yaml").write_text(
        "---\nname: jp\n...\n\n" + ("今日\tきょう\t10\n" * 20),
        encoding="utf-8",
    )
    build = dest / "build"
    build.mkdir()
    (build / "jp.table.bin").write_bytes(b"old")
    (build / "jp.reverse.bin").write_bytes(b"old")
    deploy_jp_assets(dest)
    wrapper = (dest / "jp.dict.yaml").read_text(encoding="utf-8")
    assert "import_tables:" in wrapper
    assert "今日\tきょう" not in wrapper
    assert "今日|1913 1913\tきょう" in (dest / "kagiroi.mozc.dict.yaml").read_text(
        encoding="utf-8"
    )
    assert not (build / "jp.table.bin").exists()
    assert not (build / "jp.reverse.bin").exists()


def test_project_mozc_row_removed():
    import deploy

    assert not hasattr(deploy, "project_mozc_row")
    src = Path(deploy.__file__).read_text(encoding="utf-8")
    assert "def project_mozc_row" not in src
    assert "KAGIROI_LUA_FORBIDDEN" in src
    for name in ("kagiroi_translator.lua", "kagiroi_kana_speller.lua"):
        assert name in deploy.KAGIROI_LUA_FORBIDDEN
        assert name not in deploy.KAGIROI_LUA_FILES


def test_has_mozc_ids_and_keep_predicate(tmp_path):
    from deploy import has_mozc_ids, keep_existing_heavy_dict

    stripped = tmp_path / "jp.dict.yaml"
    stripped.write_text("---\nname: jp\n...\n\n今日\tきょう\t10\n", encoding="utf-8")
    assert has_mozc_ids(stripped) is False
    kept = tmp_path / "kagiroi.mozc.dict.yaml"
    kept.write_text("---\nname: kagiroi.mozc\n...\n\n今日|1913 1913\tきょう\t121\n", encoding="utf-8")
    assert has_mozc_ids(kept) is True
    assert keep_existing_heavy_dict(kept, kind="mozc") is False
    fat = tmp_path / "fat.mozc.yaml"
    fat.write_bytes(
        "---\nname: kagiroi.mozc\n...\n\n今日|1913 1913\tきょう\t121\n".encode() + b"x" * 1_000_001
    )
    assert keep_existing_heavy_dict(fat, kind="mozc") is True
    assert keep_existing_heavy_dict(fat, kind="mozc", force=True) is False


def test_classicui_theme_patches_existing(tmp_path):
    from deploy import patch_classicui_theme

    conf = tmp_path / "classicui.conf"
    conf.write_text("VerticalCandidateList=True\nTheme=default\n", encoding="utf-8")
    patch_classicui_theme(conf)
    text = conf.read_text(encoding="utf-8")
    assert "VerticalCandidateList=True" in text
    assert "Theme=kino-dark" in text
    assert "Theme=default" not in text
    assert "DarkTheme=kino-dark" in text
