# kino Interactive Specification & Engine Manual

[简体中文](kino.md) | [English](kino.en.md)

| Attribute | Specification |
| :--- | :--- |
| **Product Scheme** | **kino** (Schema ID: `rime_mint`) |
| **Document Role** | Exhaustive normative specification for keystroke-to-commit interactions, prefix routing, Viterbi segmentation, candidate typography, punctuation, emoji rules, and QA acceptance matrices |
| **Out of Scope** | OS package manager installation guides (see root [`README.en.md`](../README.en.md)), internal CSV data schemas (see [`drafts/README.en.md`](drafts/README.en.md)) |
| **Status** | Active Normative Specification |
| **Revision** | 2026-08-27 |

---

## Table of Contents

1. [Product Identity & Non-Goals](#1-product-identity--non-goals)
2. [Cross-Platform Quickstart Reference](#2-cross-platform-quickstart-reference)
3. [Platform Invariants & Typography Standards](#3-platform-invariants--typography-standards)
4. [Schema List & Feature Toggle Matrix](#4-schema-list--feature-toggle-matrix)
5. [Candidate Window & Preedit Typography](#5-candidate-window--preedit-typography)
6. [ASCII Switching & Commit Semantics](#6-ascii-switching--commit-semantics)
7. [Pinyin Hot-Path & Speller Algebra](#7-pinyin-hot-path--speller-algebra)
8. [Prefixed Channel Specifications](#8-prefixed-channel-specifications)
   - 8.1 [`\` Symbol & Math Command Channel](#81--symbol--math-command-channel-command-draft)
   - 8.2 [`;` Latin Accents Channel](#82--latin-accents-channel-latin-accents)
   - 8.3 [`~` Japanese Kana & Viterbi Kanji Channel](#83--japanese-kana--viterbi-kanji-channel-japanese-kana--viterbi)
9. [Key-Face Punctuation Mapping](#9-key-face-punctuation-mapping)
10. [Emoji Filtering & Injection Rules](#10-emoji-filtering--injection-rules)
11. [Preserved Upstream Utilities](#11-preserved-upstream-utilities)
12. [Source vs. Generated Artifact Boundaries](#12-source-vs-generated-artifact-boundaries)
13. [Test Suite & QA Acceptance Checklist](#13-test-suite--qa-acceptance-checklist)
14. [Associated Documentation](#14-associated-documentation)

---

## 1. Product Identity & Non-Goals

### 1.1 Product Identity Model

| Element | Role | Specification |
| :--- | :--- | :--- |
| **Product Name** | **kino** | Unified display name in UI candidate windows, scheme switchers, and system tray notifications. |
| **Schema ID** | `rime_mint` | Unchanged. Preserves the upstream Mint Pinyin ID to maintain dictionary format and user dictionary compatibility. |
| **Upstream Core** | `proj-ref/oh-my-rime` | Read-only vendor submodule synchronized directly into the user runtime directory during deployment. |
| **Custom Overlay** | `overlay/` | The single base for kino customization, containing patch YAMLs, Lua scripts, and schema wrappers. |
| **Historical Archive**| `proj-arc/cloverplus` | Custom snapshot based on Clover Pinyin and rime_latex; punctuation and symbol history only, not runtime code. |

### 1.2 Explicit Non-Goals

To maintain industrial-grade responsiveness and memory predictability, kino strictly excludes the following:

- **No standalone Kagiroi scheme in the switcher**: Japanese input is handled entirely via the `~` prefix inside the primary `kino` scheme.
- **No remapping of Space to Japanese Henkan (変換)**: Space strictly commits the primary candidate across all language modes.
- **No user dictionary learning / Gikun / Nico table integration**: Prevents large external dictionaries from degrading hot-path pinyin indexing and memory footprints.
- **No exotic double-pinyin variants**: Excludes `sbzr_mix` and Spanish Colemak keyboard layouts.
- **No Typst `frac` interactive structural grids**: Mathematical formulas yield flat Unicode glyphs or macro sequences without editor layout interference.

---

## 2. Cross-Platform Quickstart Reference

On environments with installed dependencies, execute the deployment script:

```bash
# Linux (Fcitx5) / macOS (Squirrel)
./scripts/deploy.sh

# Windows (PowerShell)
.\scripts\deploy.ps1
# After execution, right-click the Weasel tray icon and click "Re-deploy"
```

On macOS, choose **Deploy** from the Squirrel menu-bar icon after the script finishes.

### Target Runtime User Directories

- **Linux**: `~/.local/share/fcitx5/rime`
- **Windows**: `%APPDATA%\Rime`
- **macOS**: `~/Library/Rime`
- **Safe Dry-Run Mode**: Set `RIME_DIR=/tmp/target`; the deployment script will isolate output, skipping theme overrides and the 150MB Japanese dataset.

---

## 3. Platform Invariants & Typography Standards

The following invariants must be maintained across all target environments:

| Platform | Configuration File | Key | Mandatory Value | Technical Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Linux (Fcitx5)** | `platform/fcitx5/conf/rime.conf` | `PreeditMode` | `Do not show` | Disables inline preediting; composition stays strictly within the candidate window. |
| | | `SwitchInputMethodBehavior` | `Commit raw input` | Commits raw ASCII (e.g., `nihao`) on Shift switch without emitting unselected Chinese previews. |
| | `~/.config/fcitx5/conf/classicui.conf` | `Theme` / `DarkTheme` | `kino-dark` | Defaults to the Nord Polar Night dark theme. |
| | | `UseDarkTheme` | `False` | Locks the dark appearance; prevents overrides from desktop light theme toggles. |
| **Windows (Weasel)**| `overlay/weasel.custom.yaml` | `inline_preedit` | `false` | Disables inline composition rendering. |
| | | `preedit_type` | `composition` | Standard composition display in the candidate box. |
| | | `horizontal` | `false` | Enforces vertical candidate list orientation. |
| | | `color_scheme_dark` | `kino_dark` | Activates the matching Nord Dark palette. |
| **macOS (Squirrel)** | `overlay/squirrel.custom.yaml` | `inline_preedit` | `false` | Disables inline composition rendering. |
| | | `horizontal` | `false` | Enforces vertical candidate list orientation. |
| | | `color_scheme` | `kino_dark` | Activates the matching Nord Dark palette. |
| **Rime Global** | `overlay/default.custom.yaml` | `menu/page_size` | `10` | 10 candidates per page (mapped to digits `1`–`9`, `0`). |

---

## 4. Schema List & Feature Toggle Matrix

### 4.1 Scheme Switcher Menu (`schema_list`)

The scheme switcher menu in `overlay/default.custom.yaml` **strictly contains only two options**:

1. **`rime_mint`** (Display Name: `kino`): Default full-featured overlay scheme.
2. **`kana`** (Display Name: `假名` / Kana): Standalone lightweight Japanese syllabary scheme.

> `latin` and `jp` schemas exist solely as internal lazy-loaded modules and are **never exposed** in the scheme switcher.

### 4.2 Feature Toggle Matrix (Feature Flags)

All feature switches are **enabled by default** (`reset: 1`). Users can independently toggle individual channels via hotkeys or the status bar without impacting other channels:

| Flag ID | Hotkey / Trigger | UI State (Off / On) | Managed Channel & Scope |
| :--- | :--- | :--- | :--- |
| `emoji_suggestion` | `Control+Shift+E` | 😺 / 😸 | Controls OpenCC pinyin emoji suggestion filter |
| `kino_typst` | Switcher / Status Bar | 无typst / typst | Controls `typst-*` symbols and macros in `\` channel |
| `kino_latex` | Switcher / Status Bar | 无latex / latex | Controls `latex` and `latex-alias` symbols in `\` channel |
| `kino_katex` | Switcher / Status Bar | 无katex / katex | Controls KaTeX-specific macros in `\` channel |
| `kino_lean` | Switcher / Status Bar | 无lean / lean | Controls Lean abbreviations and shorthands in `\` channel |
| `kino_mma` | Switcher / Status Bar | 无mma / mma | Controls Mathematica `NamedCharacter` symbols in `\` channel |
| `kino_latin` | Switcher / Status Bar | 无latin / latin | Controls Latin diacritic accent channel (`;`) |
| `kino_japanese` | Switcher / Status Bar | 无日语 / 日语 | Controls Japanese kana and Viterbi kanji channel (`~`) (does not affect standalone Kana scheme) |

**Underlying Implementation**: `overlay/lua/kino_features.lua` reads context options. `command_draft` / `jp_draft` / `feature_gate` are Lua filters with C++ `tags` (`lua_filter@*module@namespace`); pinyin `abc` is skipped in `AppliesToSegment`. The command index and Viterbi load on first use of that channel. `feature_gate` is tagged `latin` / `kana` only, so it drops table output when those switches are off.

---

## 5. Candidate Window & Preedit Typography

1. **Zero Inline Pollution**: While composing, uncommitted keystrokes remain confined to the composition area at the top of the candidate window; the target application's text cursor experiences no intermediate character insertion.
2. **Multi-Dialect Annotation Layout**: In the `\` command channel, annotations on the right side of candidates must follow a standardized bracketed syntax, listing all active dialects in a fixed order:
   $$\text{Format:} \quad \text{glyph} \quad \text{code}\ [\text{dialect}_1 \ \text{dialect}_2 \dots]$$
   - **Fixed Dialect Sequence**: `latex` $\rightarrow$ `latex*` $\rightarrow$ `katex` $\rightarrow$ `typst` $\rightarrow$ `lean` $\rightarrow$ `mma` $\rightarrow$ `unicode`
   - **Examples**:
     - Input `\alpha` $\rightarrow$ Displays `α`, annotation `alpha [latex katex typst lean mma]`
     - Input `\plus` $\rightarrow$ Displays `+`, annotation `plus [latex*]` (`latex*` denotes non-TeX native aliases)

---

## 6. ASCII Switching & Commit Semantics

### 6.1 Shift Key State Machine & Raw Input Commitment

In `overlay/rime_mint.custom.yaml` under `ascii_composer`:

| Key Action | Buffer State | Triggered Action & Technical Guarantee |
| :--- | :--- | :--- |
| **`Shift_L` (Left Shift)** | Uncommitted composition present | Executes `commit_code`: **Commits raw ASCII characters directly** (e.g., typing `nihao` and pressing Left Shift inputs `nihao` into the text box; never commits Chinese preview). |
| **`Shift_R` (Right Shift)** | Uncommitted composition present | Also executes `commit_code`, overriding upstream Mint's default `inline_ascii` mode. |
| **`Shift` (Single Press)** | Buffer empty | Triggers global Fcitx5 ASCII/Chinese toggle (`SwitchInputMethodBehavior="Commit raw input"`). |

### 6.2 Selection & Pagination Keys

- **Space (`Space`)**: Always commits candidate #1 (consistent across Pinyin, English, Commands, and Japanese).
- **Digit Keys (`1`–`9`, `0`)**: Selects candidate items 1 through 10 on the active page.
- **Pagination**: `-` / `=` and `,` / `.` (when candidate menu is active), Up/Down arrow keys, mouse scroll wheel.

---

## 7. Pinyin Hot-Path & Speller Algebra

### 7.1 Input Buffer & Spelling Configuration

1. **Alphabet Set (`alphabet`)**:
   $$\{ \text{a–z},\ \text{A–Z},\ \backslash,\ \sim,\ ; \}$$
   Prefix characters `\`, `~`, and `;` must be registered in `alphabet` to prevent segmentors from committing them as punctuation immediately.
2. **Buffer Limit Expansion**: Upstream Mint's default `codeLengthLimit_processor: 25` drops characters beyond length 25; kino expands this limit to **256** characters.
3. **Strict Zero-Correction Policy**: Enforces `translator/enable_correction: false`.
4. **Speller Algebra (`speller/algebra`) Matrix**:

```yaml
speller/algebra:
  - xlit|āáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜü|aaaaooooeeeeiiiiuuuuvvvvv| # Flatten pinyin tones
  - xform/^ng$/eng/                                          # ng special rule
  - xform/^([n])([g])$/$1e$2/
  - xform/^([ńňǹ])g$/eng/
  - xform/^[ńňǹ]$/en/
  - erase/^xx$/                                              # Remove placeholder tokens
  - derive/^([zcs]h).+$/$1/                                  # Abbreviation: zh, ch, sh
  - abbrev/^([a-z]).+$/$1/                                   # Abbreviation: first initials
```

> **Strictly Prohibited**: No fuzzy rules such as `derive/...ng$/$1gn/` (e.g., `negn` $\rightarrow$ `neng`), `hzi` $\rightarrow$ `zhi`, or `en` / `eng` merges. Typing `nihao` yields `你好`, while `negn` is strictly rejected as invalid pinyin and will never produce `能`.

---

## 8. Prefixed Channel Specifications

### Pipeline Flow: Processors & Segmentors

To ensure dots `.` and hyphens `-` in command channels are not intercepted by pagination keybinds, `overlay/rime_mint.custom.yaml` restructures the pipeline:

```
[Raw Key Input]
      │
      ▼
1. lua_processor (Length limiter, etc.)
2. ascii_composer & recognizer
3. lua_processor@*command_keys  <── Critical: Precedes key_binder to intercept `\arrow.l` dots and `~-` hyphens
4. key_binder (Hotkeys and pagination)
5. speller / punctuator / selector
      │
      ▼
[Segmentor Pipeline]
1. ascii_segmentor / matcher
2. affix_segmentor@commands     <── Critical: Precedes abc_segmentor
3. affix_segmentor@latin
4. affix_segmentor@kana
5. abc_segmentor (Primary Chinese pinyin segmentor)
6. punct_segmentor / fallback_segmentor
```

---

### 8.1 `\` Symbol & Math Command Channel (Command Draft)

- **Trigger Pattern**: Regex `^\\[A-Za-z0-9.\\-=><!*~:|\\[\\]^_+(){}'?/#&`"]*$`
- **Status Bar Tip**: `[cmd]`
- **Core Engine**: `overlay/lua/command_draft.lua` loading the generated `lua/commands_idx.lua` 2-gram inverted index.

#### A. Empty Query Behavior (Single Press `\`)

| Rank | Output Character | Annotation | Role |
| :--- | :--- | :--- | :--- |
| **1** | `、` | `\` | **Primary Dunhao Punctuation** (instant access via single `\`) |
| **2** | `\` | `backslash` | ASCII Backslash character |
| **3** | `＼` | `fullwidth` | Fullwidth Backslash character |

> The `/` key is decoupled and **never** outputs Dunhao `、`.

#### B. 4-Tier Non-Empty Query Score Ranking

Queries perform ASCII `lower()` matching and rank candidates in ascending score order (lower score = higher priority), yielding up to **20** deduplicated candidates:

| Score | Tier | Matching Rule | Example Input $\rightarrow$ Target Match |
| :--- | :--- | :--- | :--- |
| **0** | **Exact** | Full code equality | `\alpha` $\rightarrow$ `α`; `\to` $\rightarrow$ `→` |
| **1** | **Prefix** | Code starts with query | `\alp` $\rightarrow$ `α` (`alpha`) |
| **2** | **Dotted** | For codes with `.`, last segment prefix match | `\l` $\rightarrow$ `←` (`arrow.l`) |
| **3** | **Infix** | For query length $\ge 2$, 2-gram inverted index search | `\pha` $\rightarrow$ `α` (`alpha`) |

**Unicode Search Constraints**: Unicode descriptions participate in Infix search only when query length $\ge 4$, with 20 high-frequency English stopwords (e.g., `of`, `the`, `symbol`) stripped during index construction.

---

### 8.2 `;` Latin Accents Channel (Latin Accents)

- **Trigger Pattern**: Regex `^;[A-Za-z?;]+$`
- **Status Bar Tip**: `[á]`
- **Data Source**: `docs/drafts/latin-accents.csv`

| Input Keystrokes | Output | Description |
| :--- | :--- | :--- |
| **Single `;`** | *(No output)* | Remains pending without polluting the document |
| **`;n` / `;N`** | `ñ` / `Ñ` | Spanish / Latin accented character |
| **`;a` / `;A`** | `á` / `Á` | Case-sensitive mapping |
| **`;;`** | `；` | Double-tap `;` outputs fullwidth Chinese semicolon |
| **`;?`** | `¿` | Inverted Spanish question mark |

---

### 8.3 `~` Japanese Kana & Viterbi Kanji Channel (Japanese Kana & Viterbi)

- **Trigger Pattern**: Regex `^~[A-Za-z~-]+$`
- **Status Bar Tip**: `[かな]`
- **Dual Pipeline Engine**:
  1. `lua_filter@*jp_draft`: Romaji longest-match state machine + Mozc Viterbi sentence segmentation (C++ `tags: [kana]`; pinyin segments never enter).
  2. `table_translator@kana`: Fallback syllable dictionary translator (`enable_sentence: false`).

#### A. Romaji State Machine Core Contracts

1. **Pending-N Logic**: Enters pending on `n`. If followed by a vowel or `y`, merges into a combined syllable (e.g., `nni` $\rightarrow$ `ん` + `に`); if followed by a consonant or end of string, resolves as single `ん`.
2. **Sokuon (っ) Detection**: Double non-`n/y` consonants (e.g., `kka`) consume the first letter to emit `っ`.
3. **Case-Driven Primary Candidate**: Lowercase inputs prioritize Hiragana; uppercase inputs prioritize Katakana (`~ka` $\rightarrow$ `か`/`カ`; `~KA` $\rightarrow$ `カ`/`か`).
4. **Chouonpu (ー)**: Hyphens following `~` automatically resolve to Japanese long-vowel mark `ー` (e.g., `~-` $\rightarrow$ `ー`).

#### B. Kagiroi Mozc Viterbi Kanji Segmentation

Hiragana sequences are submitted to Kagiroi Viterbi segmentation. The engine operates on **Lazy Loading**: the 90MB+ dictionary is not loaded during Rime startup, but instantiated on the first `~` keypress.

- **Weight Model**: Preserves native Mozc weights (`cost = 1e8 * exp(weight)`). Artificially inflating seed word weights to 100000 is **strictly prohibited**.
- **Candidate Presentation**: Primary candidates display Hiragana/Katakana, followed by up to 2 top-ranked Viterbi-segmented Kanji phrases.

| Input Sequence | Kana Candidates | Kanji Candidates (Select via Digits) |
| :--- | :--- | :--- |
| `~watashiha` | `わたしは` / `ワタシハ` | `私は` |
| `~toukyouni` | `とうきょうに` / `トウキョウニ` | `東京に` |
| `~kyou` | `きょう` / `キョウ` | `今日` |
| `~konnichiha` | `こんにちは` / `コンニチハ` | `今日は` |

#### C. Standalone Scheme "Kana" (假名)

Selectable via `Ctrl+\``. Requires no `~` prefix; typing `ka` directly emits `か`/`カ`. Designed for dedicated Japanese syllabary input.

---

## 9. Key-Face Punctuation Mapping

Authoritatively defined by `proj-arc/cloverplus` `half_shape` settings and patched in `rime_mint.custom.yaml`:

| Physical Key | Default Output | Extended Candidate Menu / Paired State Machine | Special Invariants |
| :--- | :--- | :--- | :--- |
| `,` | `，` | - | Vendor commit |
| `.` | `。` | - | Vendor commit |
| `/` | `/` | `/`, `÷` | **Strictly prohibited from mapping to Dunhao** |
| `\` | `、` | Enters `\` command channel (§8.1) | Registered in `alphabet` |
| `;` | Enters Latin | Enters `;` Latin channel (§8.2) | Registered in `alphabet` |
| `~` | Enters Japanese | Enters `~` Japanese channel (§8.3) | Single press does not emit `～` |
| `'` | Paired `「」` | 1st press emits `「`, 2nd press emits `」` | Mint corner quote style |
| `"` | Paired `“”` | 1st press emits `“`, 2nd press emits `”` | Standard double quotes |
| `[` | `「` | Menu: `「 『 〚 〘 〖 【 〔 ［` | Bracket menu, primary corner quote |
| `]` | `」` | Menu: `」 』 〛 〙 〗 】 〕 ］` | Closing bracket menu |
| `{` / `}` | `『` / `』` | Menu: `『 〖 ｛` / `』 〗 ｝` | Curly bracket menu |
| `<` / `>` | `《` / `》` | Standard book title marks |  |
| `_` | `——` | Double em-dash |  |
| `*` | `×` | Multiplication sign |  |
| `$` | `￥` | Candidate includes `$` |  |
| `^` | `……` | Six-dot ellipsis |  |

---

## 10. Emoji Filtering & Injection Rules

Emoji support builds upon Mint's baseline `opencc/emoji.txt`, with extended annotations dynamically injected from CLDR 46 by `scripts/gen_overlay.py`:

1. **Length Gating Policy**: Injections require trigger keywords to have length $\ge 3$ for Chinese terms (e.g., `开心果`) and Latin terms (e.g., `happy`). Injecting emojis for 1–2 character high-frequency Chinese words (e.g., `你`, `好`, `中国`) is **strictly forbidden**.
2. **Switch Governance**: Controlled independently by `emoji_suggestion` (toggleable globally via `Control+Shift+E`).

---

## 11. Preserved Upstream Utilities

kino fully retains upstream oh-my-rime utilities:

| Feature | Trigger Prefix / Key | Example & Output |
| :--- | :--- | :--- |
| **Built-in Calculator** | `=` | `=128*1024` $\rightarrow$ `131072` |
| **Lunar Calendar Converter** | `N` + Digits | `N20260827` $\rightarrow$ Displays Lunar date and cyclical calendar tokens |
| **Wubi Reverse Lookup** | `Uw` | Lookup Chinese characters via Wubi codes |
| **Stroke & Decomposition** | `Uu` / `Ui` | Lookup characters via strokes or visual component decomposition |
| **Unicode Reverse Lookup** | `Uc` | Query characters via hexadecimal Unicode code points |
| **Fullwidth / Halfwidth Toggle** | `Shift+Space` / `Ctrl+Shift+3` | Toggle fullwidth character mode |
| **Simplified / Traditional Toggle** | `Ctrl+Shift+1` | Toggle Simplified/Traditional Chinese output |

---

## 12. Source vs. Generated Artifact Boundaries

| Asset Type | File List | Governance Rule |
| :--- | :--- | :--- |
| **Tracked Handcrafted Sources** | `overlay/*.custom.yaml`<br>`overlay/lua/*.lua`<br>`overlay/jp.dict.yaml`<br>`docs/drafts/*.csv`<br>`platform/` | All configuration patches, Lua logic improvements, and CSV lexicon additions must be made here and committed to Git. |
| **Ignored Compiled Artifacts** | `overlay/*.dict.yaml` (except `jp.dict.yaml`)<br>`overlay/lua/commands_idx.lua`<br>`overlay/lua/jp_romaji.lua`<br>`overlay/opencc/emoji.txt`<br>`docs/drafts/commands.csv` | Compiled by `scripts/gen_overlay.py`. Tracked in `.gitignore`. Manual editing or committing is strictly prohibited. |

---

## 13. Test Suite & QA Acceptance Checklist

### 13.1 Automated Test Suite Execution

Run pytest from the repository root:

```bash
python3 -m pytest tests/test_tables.py tests/test_gen_overlay.py tests/test_command_index.py tests/test_jp_romaji.py tests/test_emoji_opencc.py tests/test_overlay_branding.py tests/test_deploy.py -v
```

### 13.2 Manual QA Acceptance Checklist

In an active text editor with kino deployed:

- [ ] **1. Pinyin Hot-Path & Long Input**: Typing `nihao` yields `你好`; typing > 25 characters continues without truncation (limit: 256).
- [ ] **2. Strict Segmentation**: Typing `negn` does NOT yield `能`.
- [ ] **3. Raw Shift Commit**: Typing `nihao` and pressing Left `Shift` commits `nihao` directly.
- [ ] **4. Symbols & Commands Channel**:
  - [ ] Single `\` yields `、` as candidate #1; `/` does not yield `、`.
  - [ ] `\alpha` and `\Alpha` yield `α` and `Α` respectively with source dialect annotations.
  - [ ] `\a` yields `α` (`a [lean]`); `\pha` yields `α` (2-gram infix active).
  - [ ] `\arrow.l` accepts the dot cleanly and outputs `←` as candidate #1.
  - [ ] `\->` yields `→`; `\forall` yields `∀`; `\^2` yields `²`.
- [ ] **5. Latin Accents Channel**: `;n` yields `ñ`; `;;` yields `；`; Latin does not appear in scheme switcher.
- [ ] **6. Japanese & Viterbi Segmentation**:
  - [ ] `~ka` yields `か`; `~KA` yields `カ`.
  - [ ] `~watashiha` candidate list contains `わたしは` and `私は`.
  - [ ] `~toukyouni` contains `東京に`; `~kyou` contains `今日`.
  - [ ] Candidate texts are pure without internal dictionary IDs like `|1913`.
- [ ] **7. Punctuation State Machine**: `'` outputs `「` on first press and `」` on second; `[` opens corner bracket menu.
- [ ] **8. Standalone Kana Scheme**: Switch via `Ctrl+\`` to "Kana"; typing `ka` directly outputs `か`.
- [ ] **9. Layout Specifications**: 10 candidates per page; dark vertical Nord layout.
- [ ] **10. Feature Switch Isolation**: Disabling `kino_typst` removes Typst symbols from `\`; disabling `kino_japanese` disables `~`, while standalone Kana remains operational.

---

## 14. Associated Documentation

- [System Installation, Platform Deployment & OS Troubleshooting](../README.en.md) (`README.en.md`)
- [Documentation Architecture & SSOT Governance](README.en.md) (`docs/README.en.md`)
- [Data Pipeline, Indexing & Performance Specification](drafts/README.en.md) (`docs/drafts/README.en.md`)
- [Japanese Viterbi Engine & Matrix Backend Specification](jp-viterbi.md) (`docs/jp-viterbi.md`)
