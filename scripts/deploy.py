#!/usr/bin/env python3
"""Copy oh-my-rime + overlay into the platform Rime user dir."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "proj-ref" / "oh-my-rime"
OVERLAY = ROOT / "overlay"
THEMES_SRC = ROOT / "platform" / "fcitx5" / "themes"
KAGIROI_ROOT = ROOT / "proj-ref" / "Insomnia1437-rime"
MOZC = KAGIROI_ROOT / "kagiroi.mozc.dict.yaml"
MATRIX_DICT = KAGIROI_ROOT / "kagiroi_matrix.dict.yaml"
MATRIX_SCHEMA = KAGIROI_ROOT / "kagiroi_matrix.schema.yaml"
KAGIROI_LUA_DIR = KAGIROI_ROOT / "lua" / "kagiroi"
KAGIROI_LICENSE = KAGIROI_ROOT / "LICENSE"
KAGIROI_LUA_FILES = (
    "kagiroi.lua",
    "kagiroi_viterbi.lua",
    "segmenter.lua",
    "lru.lua",
    "priority_queue.lua",
)
KAGIROI_LUA_FORBIDDEN = (
    "kagiroi_translator.lua",
    "kagiroi_kana_speller.lua",
)
MIN_KEPT_DICT_BYTES = 1_000_000
JP_IMPORT_WRAPPER = (
    "---\n"
    "name: jp\n"
    'version: "1"\n'
    "sort: by_weight\n"
    "use_preset_vocabulary: false\n"
    "import_tables:\n"
    "  - kagiroi.mozc\n"
    "...\n"
)


def rime_user_dir() -> Path:
    override = os.environ.get("RIME_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise SystemExit("APPDATA is unset")
        return Path(appdata) / "Rime"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Rime"
    return Path.home() / ".local/share/fcitx5/rime"


def fcitx5_themes_dir() -> Path | None:
    override = os.environ.get("FCITX5_THEME_DIR")
    if override:
        return Path(override)
    if os.environ.get("RIME_DIR"):
        return None
    if sys.platform.startswith("linux"):
        return Path.home() / ".local/share/fcitx5/themes"
    return None


# Old exact-lookup path raised seed rows to 100000. Viterbi cost is
# 1e8 * exp(weight); that boost makes 今日/私/東京 worse than 教/渡し/TOKYO.
LEGACY_SEED_BOOST = "今日|1913 1913\tきょう\t100000"


def skip_heavy_jp_dict() -> bool:
    if os.environ.get("SKIP_JP_DICT"):
        return True
    return bool(os.environ.get("RIME_DIR") and not os.environ.get("FORCE_JP_DICT"))


def _dict_sample(path: Path, limit: int = 256_000) -> str:
    return path.read_bytes()[:limit].decode("utf-8", errors="replace")


def has_mozc_ids(path: Path) -> bool:
    """True if a dict body line keeps Mozc `surface|left right`."""
    if not path.is_file():
        return False
    sample = _dict_sample(path)
    body = sample.split("\n...\n", 1)
    text = body[1] if len(body) == 2 else sample
    for line in text.splitlines():
        if not line.strip() or line.startswith("#") or "\t" not in line:
            continue
        if "|" in line.split("\t", 1)[0]:
            return True
    return False


def has_legacy_seed_boost(path: Path) -> bool:
    if not path.is_file():
        return False
    return LEGACY_SEED_BOOST.encode() in path.read_bytes()


def keep_existing_heavy_dict(path: Path, *, kind: str, force: bool = False) -> bool:
    """Skip recopy of a large ID-bearing mozc table or a compiled-size matrix."""
    if force or not path.is_file() or path.stat().st_size <= MIN_KEPT_DICT_BYTES:
        return False
    if kind == "mozc":
        return has_mozc_ids(path) and not has_legacy_seed_boost(path)
    if kind == "matrix":
        return "name: kagiroi_matrix" in _dict_sample(path, 4096)
    return False


def write_jp_import_wrapper(dest_jp: Path) -> None:
    dest_jp.write_text(JP_IMPORT_WRAPPER, encoding="utf-8")


def invalidate_jp_build(dest: Path) -> None:
    """Drop compiled jp artifacts so a stripped projection cannot keep serving."""
    build = dest / "build"
    if not build.is_dir():
        return
    for path in build.glob("jp.*"):
        if path.is_file():
            path.unlink()


def copy_kagiroi_lua(dest: Path) -> None:
    out = dest / "lua" / "kagiroi"
    out.mkdir(parents=True, exist_ok=True)
    allowed = set(KAGIROI_LUA_FILES) - set(KAGIROI_LUA_FORBIDDEN)
    for name in KAGIROI_LUA_FILES:
        if name not in allowed:
            continue
        src = KAGIROI_LUA_DIR / name
        if src.is_file():
            shutil.copy2(src, out / name)
    for name in KAGIROI_LUA_FORBIDDEN:
        leftover = out / name
        if leftover.is_file():
            leftover.unlink()
    if KAGIROI_LICENSE.is_file():
        shutil.copy2(KAGIROI_LICENSE, dest / "LICENSE.kagiroi")


def _copy_heavy(src: Path, dest: Path, *, kind: str, force: bool) -> None:
    if not src.is_file():
        return
    if keep_existing_heavy_dict(dest, kind=kind, force=force):
        print(f"keep existing {dest.name} ({dest.stat().st_size} bytes)")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"copied {src.name} to {dest}")


def deploy_jp_assets(dest: Path) -> None:
    """Copy Mozc lex (keep |ids), matrix, and kagiroi Viterbi lua. No ID strip."""
    if skip_heavy_jp_dict():
        # Overlay may have just replaced a 90MB stripped jp.dict.yaml. Keep the
        # dest wrapper ID-free and drop the old compiled table even when the
        # 150MB copy is skipped (RIME_DIR / SKIP_JP_DICT).
        write_jp_import_wrapper(dest / "jp.dict.yaml")
        invalidate_jp_build(dest)
        return
    force = bool(os.environ.get("FORCE_JP_DICT"))
    _copy_heavy(MOZC, dest / "kagiroi.mozc.dict.yaml", kind="mozc", force=force)
    _copy_heavy(MATRIX_DICT, dest / "kagiroi_matrix.dict.yaml", kind="matrix", force=force)
    if MATRIX_SCHEMA.is_file():
        shutil.copy2(MATRIX_SCHEMA, dest / "kagiroi_matrix.schema.yaml")
    copy_kagiroi_lua(dest)
    write_jp_import_wrapper(dest / "jp.dict.yaml")
    invalidate_jp_build(dest)
    print(f"jp dict imports kagiroi.mozc at {dest / 'jp.dict.yaml'}")


def _copytree(src: Path, dest: Path, *, ignore=None) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True, ignore=ignore)


_RIME_CONF_KEYS = {
    "PreeditMode": '"Do not show"',
    "SwitchInputMethodBehavior": '"Commit raw input"',
}


def _patch_rime_preedit() -> None:
    conf = Path.home() / ".config/fcitx5/conf/rime.conf"
    conf.parent.mkdir(parents=True, exist_ok=True)
    src = ROOT / "platform" / "fcitx5" / "conf" / "rime.conf"
    if not conf.is_file() and src.is_file():
        shutil.copy2(src, conf)
        return
    text = conf.read_text(encoding="utf-8") if conf.is_file() else ""
    lines = text.splitlines() if text else []
    found: set[str] = set()
    out: list[str] = []
    for line in lines:
        key = next((k for k in _RIME_CONF_KEYS if line.lstrip().startswith(f"{k}=")), None)
        if key:
            out.append(f"{key}={_RIME_CONF_KEYS[key]}")
            found.add(key)
        else:
            out.append(line)
    for key, val in _RIME_CONF_KEYS.items():
        if key not in found:
            out.append(f"{key}={val}")
    conf.write_text("\n".join(out) + "\n", encoding="utf-8")


_CLASSICUI_KEYS = {
    "Theme": "kino-dark",
    "DarkTheme": "kino-dark",
    "UseDarkTheme": "False",
    "UseAccentColor": "False",
}


def patch_classicui_theme(conf: Path) -> None:
    conf.parent.mkdir(parents=True, exist_ok=True)
    text = conf.read_text(encoding="utf-8") if conf.is_file() else ""
    found: set[str] = set()
    out: list[str] = []
    for line in text.splitlines():
        key = next((k for k in _CLASSICUI_KEYS if line.lstrip().startswith(f"{k}=")), None)
        if key:
            out.append(f"{key}={_CLASSICUI_KEYS[key]}")
            found.add(key)
        else:
            out.append(line)
    for key, val in _CLASSICUI_KEYS.items():
        if key not in found:
            out.append(f"{key}={val}")
    body = "\n".join(out)
    if not body.endswith("\n"):
        body += "\n"
    conf.write_text(body, encoding="utf-8")


def _patch_classicui_theme() -> None:
    patch_classicui_theme(Path.home() / ".config/fcitx5/conf/classicui.conf")


def deploy() -> None:
    if not VENDOR.is_dir():
        raise SystemExit(f"missing vendor: {VENDOR}")
    dest = rime_user_dir()
    dest.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(".git", "build", "*.userdb", "*.userdb.*")
    _copytree(VENDOR, dest, ignore=ignore)
    _copytree(OVERLAY, dest)
    deploy_jp_assets(dest)
    print(f"deployed rime overlay to {dest}")
    themes_dest = fcitx5_themes_dir()
    if themes_dest is not None:
        for src in THEMES_SRC.iterdir():
            if src.is_dir():
                _copytree(src, themes_dest / src.name)
        print(f"deployed fcitx5 themes to {themes_dest}")
        live_themes = Path.home() / ".local/share/fcitx5/themes"
        if themes_dest.resolve() == live_themes.resolve():
            _patch_classicui_theme()
            _patch_rime_preedit()
    live_rime = Path.home() / ".local/share/fcitx5/rime"
    if dest.resolve() == live_rime.resolve() and sys.platform.startswith("linux"):
        _restage_fcitx5_rime()


def _reload_fcitx5_addon(name: str) -> None:
    subprocess.run(
        [
            "dbus-send",
            "--print-reply",
            "--dest=org.fcitx.Fcitx5",
            "/controller",
            "org.fcitx.Fcitx.Controller1.ReloadAddonConfig",
            f"string:{name}",
        ],
        check=False,
        capture_output=True,
    )


def _restage_fcitx5_rime() -> None:
    _reload_fcitx5_addon("rime")
    _reload_fcitx5_addon("classicui")
    subprocess.run(["fcitx5-remote", "-s", "rime"], check=False, capture_output=True)
    time.sleep(0.3)
    subprocess.run(
        [
            "dbus-send",
            "--print-reply",
            "--dest=org.fcitx.Fcitx5",
            "/rime",
            "org.fcitx.Fcitx.Rime1.SetSchema",
            "string:rime_mint",
        ],
        check=False,
        capture_output=True,
    )


if __name__ == "__main__":
    deploy()
