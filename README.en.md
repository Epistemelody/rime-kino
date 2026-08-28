# kino

[简体中文](README.md) | [English](README.en.md) | [Web docs](https://epistemelody.github.io/rime-kino/)

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform: Linux, Windows & macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-informational.svg?style=flat-square)](https://rime.im/download/)
[![Engine: Rime & librime-lua](https://img.shields.io/badge/Engine-Rime%20%2B%20librime--lua-orange.svg?style=flat-square)](https://rime.im/)
[![Tests: 72 Passed](https://img.shields.io/badge/Tests-72%20Passed-brightgreen.svg?style=flat-square)](tests/)

> A multi-channel Rime overlay configuration integrating Chinese Pinyin, Japanese (Kana & Mozc Viterbi Kanji), Latin Diacritics, Math & Commands (LaTeX / Typst / Lean / MMA), and Paired Punctuation.

kino (pronounced `/ˈkiːnoʊ/`, *Kinetic Input Normalized Overlay*) is a multi-channel Rime overlay configuration built on top of [oh-my-rime (Mint Pinyin)](https://github.com/Mintimate/oh-my-rime). Powered by an offline 2-gram inverted index and Lua extensions, it provides specialized input channels for mathematical symbols (LaTeX / KaTeX / Typst / Lean 4 / MMA / Unicode), Japanese Kana and Mozc Viterbi segmentation, Latin diacritics, paired punctuation, and length-gated emoji suggestions alongside standard Pinyin, triggered via designated prefixes (e.g. `\`, `;`, `~`).

<p align="center">
  <img src="assets/kino-preview.png" alt="kino preview" width="100%">
</p>

## Cheat Sheet

| Channel | Example | Notes |
| :--- | :--- | :--- |
| Pinyin | `nihao` → `你好` | No fuzzy pinyin; Space to commit |
| Math (`\`) | `\alpha` → `α` / `\int` → `∫` | LaTeX / Typst / Lean / MMA symbol search |
| Latin Diacritics (`;`) | `;n` → `ñ` / `;;` → `；` | Case-sensitive; double `;;` commits fullwidth `；` |
| Japanese (`~`) | `~ka` → `か` / `~watashiha` → `私は` | Romaji DFA + Mozc Viterbi; supports standalone Kana |
| Paired Punctuation | Double `''` → `「」` / `""` → `“”` | Paired quotes automaton and bracket menu |
| Gated Emoji | `xiao` → `😄` / `pingguo` → `🍎` | CLDR 46 annotations; $\ge 3$ char length gating |

## Quickstart

<details>
<summary>Prerequisites</summary>

Before deploying the kino overlay, ensure your system has the base runtime dependencies installed:

- Python 3.9+ and Git
- Rime input frontend with librime-lua runtime extension support:

### 1. Linux (Fcitx5 Framework)
- Packages (select for your distribution):
  ```bash
  # Fedora / RHEL
  sudo dnf install -y fcitx5 fcitx5-rime librime-lua fcitx5-configtool python3

  # Arch Linux / Manjaro
  sudo pacman -S --needed fcitx5 fcitx5-rime librime-lua fcitx5-configtool python

  # Debian / Ubuntu (>= 24.04)
  sudo apt update && sudo apt install -y fcitx5 fcitx5-rime librime-plugin-lua fcitx5-config-qt python3

  # openSUSE (Tumbleweed / Leap)
  sudo zypper install -y fcitx5 fcitx5-rime librime-lua fcitx5-config-tool python3
  ```
- Environment Variables: Add the following configuration to `~/.config/environment.d/fcitx5.conf` (Wayland/systemd) or `~/.xprofile` (X11) and re-login:
  ```ini
  GTK_IM_MODULE=fcitx
  QT_IM_MODULE=fcitx
  XMODIFIERS=@im=fcitx
  ```
- Add Input Method: Launch `fcitx5-configtool` and add Rime to your active input methods.

### 2. Windows (Weasel)
- Download and install the Weasel installer (version 0.16.0+ recommended, comes pre-bundled with librime-lua) from the [Rime Official Download Page](https://rime.im/download/) or [Weasel GitHub Releases](https://github.com/rime/weasel/releases).
- Upon completion, the Weasel service icon will be visible in the system tray.

### 3. macOS (Squirrel)
- Install via Homebrew: `brew install --cask squirrel`, or download the package from the [Rime Official Download Page](https://rime.im/download/) / [Squirrel Releases](https://github.com/rime/squirrel/releases) (comes pre-bundled with librime-lua).
- After installation, the Squirrel icon appears in the menu bar.

</details>

### 1. Clone Repository & Submodules

Deployment requires only two runtime submodules: `oh-my-rime` (pinyin baseline) and `Insomnia1437-rime` (Japanese Mozc).

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/Epistemelody/rime-kino.git
cd rime-kino
```

> Note: `--shallow-submodules` fetches only the pinned commit. Other research references in `.gitmodules` use `update = none` and are not fetched by `--recurse-submodules`.

For existing clones or missing submodules:

```bash
python3 scripts/init_submodules.py          # runtime only, depth 1
python3 scripts/init_submodules.py --all    # fetch all submodules including research refs
```

### 2. Deploy to System

#### Linux (Fcitx5)
```bash
./scripts/deploy.sh
```
The script compiles tables, synchronizes Mint Pinyin and kino overlay, mounts Mozc dictionary data, installs the Nord theme, and reloads Fcitx5-Rime.

#### Windows (Weasel)
```powershell
.\scripts\deploy.ps1
```
After deployment, right-click the Weasel tray icon and click "Re-deploy".

#### macOS (Squirrel)
```bash
./scripts/deploy.sh
```
After deployment, choose "Deploy" from the Squirrel menu bar icon (user directory: `~/Library/Rime`).

> Advanced Options: The deployment script supports environment variables including `RIME_DIR` (custom target path), `FORCE_JP_DICT=1` (force copy Mozc dictionaries), and `SKIP_JP_DICT=1` (skip dictionary copy), documented in [Documentation Architecture](docs/README.en.md).

## Feature Flags

kino includes 8 orthogonal feature flags enabled by default (`kino_latex`, `kino_katex`, `kino_typst`, `kino_lean`, `kino_mma`, `kino_latin`, `kino_japanese`, and `emoji_suggestion`). They can be toggled via the scheme menu (`Ctrl+\``) or status bar with automatic state persistence. Detailed descriptions and key bindings are specified in [kino Engine Manual](docs/kino.en.md).

## FAQ & Troubleshooting

<details>
<summary>Q1: Why are there no candidates for <code>\alpha</code> or <code>~ka</code>, or why does a Lua error appear?</summary>

- Cause: The host Rime environment is missing the `librime-lua` runtime extension.
- Solution:
  - Linux: Verify that `librime-lua` (or `librime-plugin-lua` on Debian/Ubuntu) is installed.
  - Windows: Ensure Weasel is version $\ge 0.16.0$.
  - macOS: Update Squirrel to the latest version and click "Deploy".
</details>

<details>
<summary>Q2: What is the exact behavior of Shift key toggling?</summary>

- Explanation:
  - When input buffer has characters: Pressing left/right `Shift` triggers Raw Commit (commits the raw ASCII text directly, e.g. `nihao` $\to$ `nihao`).
  - When input buffer is empty: Pressing `Shift` toggles the system Chinese/English input mode.
</details>

<details>
<summary>Q3: Why doesn't the <code>/</code> key output Dunhao <code>、</code>?</summary>

- Explanation: kino maps the ideographic comma to the `\` key (single `\` commits `、`). The `/` key is used for slash `/` and division sign `÷`.
</details>

<details>
<summary>Q4: Why is there a slight delay when typing <code>~</code> for the first time?</summary>

- Explanation: kino uses on-demand loading. The Mozc dictionary (~150MB) and transition matrix are loaded into memory only when `~` is first typed.
</details>

<details>
<summary>Q5: How can I customize math symbols or modify tables?</summary>

- Explanation: Source data is stored in `docs/drafts/*.csv`. Edit the CSV file, run `python3 scripts/gen_overlay.py` to generate overlays, and run `./scripts/deploy.sh` to deploy.
</details>

## Structure

```
rime-kino/
├── docs/            # Technical specifications, contracts & source CSV tables (docs/drafts/)
├── overlay/         # Rime overlay configuration, custom patches & Lua runtime (overlay/lua/)
├── platform/        # Platform configurations & Nord themes (Fcitx5 / Weasel / Squirrel)
├── proj-ref/        # Runtime submodules (oh-my-rime, Insomnia1437-rime) & research refs
├── scripts/         # Offline table compiler (gen_overlay.py) & deploy engine (deploy.py)
└── tests/           # Automated regression test suite (Pytest)
```

## Development & Testing

```bash
# 1. Compile all tables and generate 2-gram inverted index
python3 scripts/gen_overlay.py

# 2. Run automated regression test suite
pytest tests/ -q
# 72 passed in ~5s
```

## Documentation

- [Web documentation](https://epistemelody.github.io/rime-kino/)
- [Documentation Architecture & SSOT Governance](docs/README.en.md) (`docs/README.en.md`)
- [kino Interactive Specification & Engine Manual](docs/kino.en.md) (`docs/kino.en.md`)
- [Data Schemas, 2-Gram Indexing & Performance Specifications](docs/drafts/README.en.md) (`docs/drafts/README.en.md`)
- [Japanese Viterbi Engine & Matrix Backend Specification](docs/jp-viterbi.md) (`docs/jp-viterbi.md`)
- [Math-symbol table and command pipeline](docs/math-symbols.md) (`docs/math-symbols.md`)

## Roadmap

- [ ] Extended multilingual lexicons and European accented vocabulary
- [ ] Adaptive Viterbi local frequency caching for Japanese sentence segmentation
- [ ] Lightweight cross-platform configuration and toggle dashboard (Web / TUI)

## Relevant Projects

- [oh-my-rime (Mint Pinyin)](https://github.com/Mintimate/oh-my-rime): Baseline Chinese pinyin dictionary and schema (`proj-ref/oh-my-rime`).
- [Insomnia1437/rime (Kagiroi)](https://github.com/Insomnia1437/rime): Mozc Japanese dictionaries and Viterbi matrices (`proj-ref/Insomnia1437-rime`).
- [iamcheyan/rime](https://github.com/iamcheyan/rime): Double-pinyin and schema layout reference (`proj-ref/iamcheyan-rime`).
- [tumuyan/rime-pinyin-jap](https://github.com/tumuyan/rime-pinyin-jap): Pinyin-Japanese schema reference (`proj-ref/rime-pinyin-jap`).
- [gkovacs/rime-spanish](https://github.com/gkovacs/rime-spanish): Latin diacritic `;` layout reference (`proj-ref/rime-spanish`).
- [iDvel/rime-ice](https://github.com/iDvel/rime-ice): Rime Ice reference (`proj-ref/rime-ice`).
- [fkxxyz/rime-cloverpinyin](https://github.com/fkxxyz/rime-cloverpinyin): Pinyin habits and paired-punctuation reference.
- [shenlebantongying/rime_latex](https://github.com/shenlebantongying/rime_latex): LaTeX math-symbol schema reference.
- `proj-arc/cloverplus`: Local customized archive based on Clover Pinyin and rime_latex (historical reference, not runtime code).
- [hchunhui/librime-lua](https://github.com/hchunhui/librime-lua): Rime Lua runtime.

## License & Citation

This project is licensed under the [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0) License.

```bibtex
@software{epistemelody2026kino,
  author       = {Felidz and {Epistemelody}},
  title        = {kino: A Modern Table-Driven Multi-Channel Rime Input Overlay Framework},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/Epistemelody/rime-kino}}
}
```
