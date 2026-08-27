from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_init():
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import init_submodules  # noqa: E402

    return init_submodules


def test_runtime_submodules_are_shallow_and_cloned_by_default():
    init = _load_init()
    by_path = {e["path"]: e for e in init.gitmodules_entries()}
    for path in ("proj-ref/oh-my-rime", "proj-ref/Insomnia1437-rime"):
        assert path in by_path, path
        assert by_path[path].get("shallow") == "true", path
        assert by_path[path].get("update") != "none", path
    assert set(init.runtime_paths()) == {
        "proj-ref/oh-my-rime",
        "proj-ref/Insomnia1437-rime",
    }


def test_reference_submodules_skip_default_clone():
    init = _load_init()
    by_path = {e["path"]: e for e in init.gitmodules_entries()}
    refs = {
        "proj-ref/iamcheyan-rime",
        "proj-ref/rime-pinyin-jap",
        "proj-ref/rime-spanish",
        "proj-ref/rime-ice",
    }
    for path in refs:
        assert by_path[path].get("update") == "none", path
        assert by_path[path].get("shallow") == "true", path
    assert set(init.reference_paths()) == refs


def test_readme_clone_is_shallow_runtime_only():
    for name in ("README.md", "README.en.md", "docs/home.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "--shallow-submodules" in text, name
        assert "--recurse-submodules" in text, name
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "--shallow-submodules" in html
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "scripts/init_submodules.py" in readme
    assert "update = none" in readme
