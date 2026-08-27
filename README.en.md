# kino

[简体中文](README.md) | [English](README.en.md) | [Web docs](https://epistemelody.github.io/rime-kino/)

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform: Linux, Windows & macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-informational.svg?style=flat-square)](https://rime.im/download/)
[![Engine: Rime & librime-lua](https://img.shields.io/badge/Engine-Rime%20%2B%20librime--lua-orange.svg?style=flat-square)](https://rime.im/)
[![Tests: 68 Passed](https://img.shields.io/badge/Tests-68%20Passed-brightgreen.svg?style=flat-square)](tests/)

> A high-performance, multi-channel Rime overlay framework seamlessly integrating **Chinese Pinyin, Japanese (Kana & Viterbi Kanji), Latin Diacritics, Multi-Ecosystem Math & Commands (LaTeX / Typst / Lean / MMA), and Paired Punctuation**.

**kino** (pronounced `/ˈkiːnoʊ/`, *Kinetic Input Normalized Overlay*) is a modern, high-performance multi-channel Rime overlay framework built on top of [oh-my-rime (Mint Pinyin)](https://github.com/Mintimate/oh-my-rime). While preserving native sub-millisecond pinyin responsiveness, kino delivers out-of-the-box support for **Chinese-English mixing, Japanese Kana & Viterbi Kanji segmentation, direct Latin diacritics, multi-dialect math & command search (LaTeX / KaTeX / Typst / Lean 4 / Mathematica / Unicode), paired punctuation automata, and gated emoji suggestions** via an offline 2-gram inverted index and lock-free Lua runtime.

<p align="center">
  <img src="assets/kino-preview.png" alt="kino preview" width="100%">
</p>

---

## Features

- **Strict Phonetic Hot-Path**: Disables all fuzzy pinyin and transposition algebra (`negn` strictly rejects `能`); input buffer expanded to 256 characters.
- **Multi-Dialect Math & Commands (`\`)**: Unified coverage for LaTeX / KaTeX / Typst / Lean 4 / Mathematica / Unicode with 4-tier score ranking (Exact / Prefix / Dotted / 2-gram Infix); single `\` commits Dunhao `、`.
- **Direct Latin Diacritics (`;`)**: `;n` $\to$ `ñ`, `;a` $\to$ `á`, `;?` $\to$ `¿`; double `;` outputs fullwidth `；`; single `;` remains pending without polluting text.
- **Viterbi Japanese Engine (`~`)**: Deterministic Romaji DFA state machine (Pending-N, sokuon, chouonpu, case script priority) + Mozc transition matrix for global optimal Viterbi segmentation; includes standalone "Kana" scheme.
- **Paired Punctuation & Smart Brackets**: `'` sequentially emits `「` and `」`; `"` sequentially emits `“` and `”`; `[` opens corner/academic bracket menus.
- **Gated Emoji Suggestions**: Integrates CLDR 46 with a $\ge 3$ character length gating policy, eliminating emoji clutter on high-frequency 1–2 character Chinese words.
- **Orthogonal Feature Flags**: 8 independent runtime feature toggles with persistent state storage.
- **Unified Nord Dark Aesthetic**: Linux (Fcitx5), Windows (Weasel), and macOS (Squirrel) share the Nord Polar Night dark theme with a clean 10-candidate vertical layout and zero inline preedit pollution.

---

## Prerequisites

Before deploying the kino overlay, ensure your operating system has a compatible Rime frontend and Lua runtime engine installed:

### 1. Linux (Fcitx5 Framework)
- **Input Framework**: Requires `fcitx5` and `fcitx5-rime`.
- **Lua Runtime Support**: kino requires `librime-lua` to execute the 2-gram inverted index search and Viterbi algorithm. Ensure this package is installed.
- **Environment Variables**: Add the following configuration to `~/.config/environment.d/fcitx5.conf` (or `~/.pam_environment` / `~/.xprofile`) and log out/in:
  ```ini
  GTK_IM_MODULE=fcitx
  QT_IM_MODULE=fcitx
  XMODIFIERS=@im=fcitx
  ```
- **Add Input Method**: Launch `fcitx5-configtool` and add **Rime (中州韵)** to your active input methods.

### 2. Windows (Weasel / 小狼毫)
- Download and install the latest **Weasel installer** (version 0.16.0+ recommended, comes pre-bundled with librime-lua) from the [Rime Official Download Page](https://rime.im/download/) or [Weasel GitHub Releases](https://github.com/rime/weasel/releases).
- Upon completion, the Weasel service icon will be visible in the system tray.

### 3. macOS (Squirrel / 鼠须管)
- Install via Homebrew: `brew install --cask squirrel`, or download the latest package from the [Rime Official Download Page](https://rime.im/download/) / [Squirrel Releases](https://github.com/rime/squirrel/releases) (a recent build with bundled librime-lua is recommended).
- After installation, the Squirrel icon appears in the menu bar.

---

## Structure

```
rime-kino/
├── assets/                       # Project visual previews & media assets (kino-preview.png)
├── overlay/                      # Overlay configuration & Lua extensions (custom.yaml, lua/)
├── platform/fcitx5/              # Linux Fcitx5 configs & Nord themes
├── docs/                         # Project technical documentation (kino.en.md, drafts/README.en.md)
├── scripts/                      # Table compiler (gen_overlay.py) & deploy engine (deploy.py)
├── proj-ref/                     # Submodule vendors (oh-my-rime, Insomnia1437-rime)
└── tests/                        # Automated regression test suite
```

---

## Quickstart

### 1. Clone Repository & Submodules

```bash
git clone --recurse-submodules https://github.com/Epistemelody/rime-kino.git
cd rime-kino
```

### 2. Deploy to System

#### Linux (Major Distributions)

Install the required packages for your distribution (**librime-lua** is strictly required):

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

Execute the automated compile and deployment script:

```bash
./scripts/deploy.sh
```

#### Windows (Weasel / 小狼毫)

```powershell
# Run in PowerShell, then right-click Weasel tray icon and click "Re-deploy"
.\scripts\deploy.ps1
```

#### macOS (Squirrel / 鼠须管)

```bash
./scripts/deploy.sh
```

Then choose **Deploy** from the Squirrel menu-bar icon. The user directory is `~/Library/Rime`.

---

## Cheat Sheet

| Channel | Keystroke Example | Output | Interaction Notes |
| :--- | :--- | :--- | :--- |
| **Pinyin Hot-Path** | `nihao` | `你好` | Composition in window header; Space to commit |
| **ASCII Toggle** | Type, then press `Shift_L` | `nihao` | **Raw Commit**: Commits raw ASCII directly without pollution |
| **Dunhao & Commands** | Single `\` / `\alpha` / `\->` | `、` / `α` / `→` | Annotation: `[latex katex typst lean mma]`; `/` remains slash |
| **Typst Period** | `\arrow.l` | `←` | Dot parsed as part of token, not pagination |
| **Latin Diacritics** | `;n` / `;a` / `;;` | `ñ` / `á` / `；` | Single `;` remains pending without committing |
| **Japanese Kana/Kanji** | `~ka` / `~watashiha` | `か` / `私は` | Romaji DFA + Mozc Viterbi bigram segmentation |
| **Paired Quotes/Brackets** | Double-tap `'` / Press `[` | `「」` / Menu | Paired corner quotes; `[` opens bracket menu |
| **Scheme Switcher** | `Ctrl+\`` | `kino` / `Kana` | Toggle primary overlay or standalone Kana scheme |

---

## Roadmap

- [ ] **Multilingual Lexicons & Phrases**:
  - Integrate high-frequency modern **English phrases and domain terminology** with intelligent prefix completion.
  - Support direct output for common vocabulary, accented phrases, and technical terms in **French, German, Spanish**, and other European languages.
- [ ] **Adaptive Viterbi & Learning Cache**:
  - Introduce local frequency priority caching for Japanese long-sentence segmentation to minimize candidate re-selection overhead.
- [ ] **Interactive Configuration Dashboard**:
  - Provide a lightweight Web/TUI dashboard for one-click toggling and hot-reloading of the 8 Feature Flags and UI themes.

---

## Testing

```bash
.venv/bin/pytest tests/ -q
# 65 passed in ~3s
```

---

## Documentation

- [Web documentation](https://epistemelody.github.io/rime-kino/)
- [Documentation Architecture & SSOT Governance](docs/README.en.md) (`docs/README.en.md`)
- [kino Interactive Specification & Engine Manual](docs/kino.en.md) (`docs/kino.en.md`)
- [Data Schemas, 2-Gram Indexing & Performance Specifications](docs/drafts/README.en.md) (`docs/drafts/README.en.md`)
- [Japanese Viterbi Engine & Matrix Backend Specification](docs/jp-viterbi.md) (`docs/jp-viterbi.md`)
- [Math-symbol table and command pipeline](docs/math-symbols.md) (`docs/math-symbols.md`)

---

## Relevant Projects

- [oh-my-rime (Mint Pinyin)](https://github.com/Mintimate/oh-my-rime): Baseline Chinese pinyin dictionary and schema (`proj-ref/oh-my-rime`).
- [Insomnia1437/rime (Kagiroi)](https://github.com/Insomnia1437/rime): Mozc Japanese dictionaries and Viterbi matrices (`proj-ref/Insomnia1437-rime`).
- [iamcheyan/rime](https://github.com/iamcheyan/rime): Double-pinyin and schema layout reference (`proj-ref/iamcheyan-rime`).
- [tumuyan/rime-pinyin-jap](https://github.com/tumuyan/rime-pinyin-jap): Pinyin-Japanese schema reference (`proj-ref/rime-pinyin-jap`).
- [gkovacs/rime-spanish](https://github.com/gkovacs/rime-spanish): Latin diacritic `;` layout reference (`proj-ref/rime-spanish`).
- [fkxxyz/rime-cloverpinyin](https://github.com/fkxxyz/rime-cloverpinyin): Historical punctuation and symbol reference (`proj-arc/cloverplus`).
- [hchunhui/librime-lua](https://github.com/hchunhui/librime-lua): Rime Lua runtime.

---

## License & Citation

This project is licensed under the **[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0)** License.

```bibtex
@software{epistemelody2026kino,
  author       = {{Epistemelody} and kino contributors},
  title        = {kino: A Modern Table-Driven Multi-Channel Rime Input Overlay Framework},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub repository},
  howpublished = {\url{https://github.com/Epistemelody/rime-kino}}
}
```
