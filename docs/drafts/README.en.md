# Lexicon Data Schemas & Table Compiler Engineering Specification

[简体中文](README.md) | [English](README.en.md)

| Attribute | Specification |
| :--- | :--- |
| **Subsystem** | **kino** Data Engineering & Table Compilation Subsystem |
| **Document Role** | Governs `docs/drafts/*.csv` data schemas, compiler pipeline contracts, 2-gram inverted index algorithms, OpenCC injection rules, and runtime performance budgets |
| **Out of Scope** | Candidate UI typography (see [`../kino.en.md`](../kino.en.md)), OS-level installation steps (see root [`../../README.en.md`](../../README.en.md)) |
| **Status** | Active Normative Data Specification |
| **Revision** | 2026-08-27 |

---

## 1. Compilation Pipeline & Architecture Topology

kino implements an **offline-compiled, zero-runtime-parsing** data architecture. All structured symbols, syllabaries, and key-mapping source datasets are maintained within `docs/drafts/*.csv` and pre-compiled offline by `scripts/gen_overlay.py` into native Rime dictionaries, Lua inverted indexes, and OpenCC lexicon tables:

```
[Source Layer] docs/drafts/*.csv
   ├── kana.csv             (Japanese syllabary source)
   ├── latin-accents.csv    (Latin diacritics snapshot)
   ├── math-symbols.csv     (Math/command multi-dialect table)
   ├── typst-extra.csv      (Typst functions & spaces)
   ├── punctuation.csv      (Punctuation mappings)
   ├── brackets.csv         (Bracket menu definitions)
   └── emoji.csv            (CLDR 46 annotations)
                 │
                 ▼ Offline Pre-compilation (scripts/gen_overlay.py)
[Generated Layer] overlay/
   ├── kana.dict.yaml          (Syllabary dictionary, .gitignore)
   ├── latin.dict.yaml         (Latin accents dictionary, .gitignore)
   ├── commands.dict.yaml      (Short ASCII exact fallback table, .gitignore)
   ├── lua/commands_idx.lua    (2-gram inverted index table, .gitignore)
   ├── lua/jp_romaji.lua       (Romaji state machine longest-match table, .gitignore)
   └── opencc/emoji.txt        (Emoji patch dictionary, .gitignore)
                 │
                 ▼ Deployment & Asset Distribution (scripts/deploy.py)
[Runtime Layer] User Rime Directory (~/.local/share/fcitx5/rime or %APPDATA%\Rime)
   ├── Synchronizes upstream oh-my-rime base lexicons
   ├── Overlays compiled overlay/ configurations
   └── Mounts kagiroi.mozc.dict.yaml (~58MB) & kagiroi_matrix (~98MB)
```

### Core Engineering Invariants

1. **Strictly Prohibit Manual Editing of Artifacts**: All compiled files under `overlay/` marked in `.gitignore` must be generated exclusively via build scripts.
2. **Never Export to Legacy Merged Files**: Re-exporting multi-dialect wide tables back into the legacy `docs/drafts/commands.csv` format is strictly forbidden.
3. **Do Not Commit Intermediate Artifacts**: Intermediate files such as `kana.expanded.csv` and `emoji.core.csv` have been consolidated into main tables and must never be committed to Git.
4. **Standardized Multi-Value Delimiter**: Equivalent aliases or multi-dialect codes within a single CSV cell must be separated by ` | ` (a pipe surrounded by spaces).

---

## 2. Source Datasets Catalog & Roles

| Data File | Asset Category | Core Schema Fields | Governance Role |
| :--- | :--- | :--- | :--- |
| **`math-symbols.csv`** | Handcrafted SSOT Wide Table | `glyph,latex,latex_alias,katex,typst,typst_shorthand,lean,lean_shorthand,mma,mma_alias` | Single source of truth for math symbols. Each row defines a unique Unicode glyph, horizontally mapping aliases across major ecosystems. |
| **`typst-extra.csv`** | Handcrafted Extension | `code,kind,preview,description` | Dedicated to Typst functions (`typst-fn`), spaces (`typst-space`), and operators (`typst-op`) lacking single-character glyph definitions. |
| **`kana.csv`** | Handcrafted SSOT | `hira,kata,codes,family,notes` | Baseline Japanese syllabary and Romaji correspondence table. |
| **`punctuation.csv`** | Handcrafted SSOT | `key,half,full,notes,recommend` | Key-face halfwidth/fullwidth punctuation mappings and recommended candidate sets. |
| **`brackets.csv`** | Handcrafted SSOT | `type,left,right,notes` | Brackets, quotation marks, and enclosing enclosure pairs. |
| **`latin-accents.csv`** | Imported Snapshot | `glyph,codes` | Latin diacritics and accented characters mapping table. |
| **`emoji.csv`** | Imported Snapshot | `emoji,codes_zh,codes_en` | Multi-language annotation snapshot based on Unicode CLDR 46. |
| **`import/lean-abbreviations.json`** | Official Snapshot | JSON Key-Value Map | Official Lean abbreviations snapshot, consumed exclusively by `import_math_symbols.py`. |
| **`import/mma-named.json`** | Official Snapshot | JSON Key-Value Map | Mathematica `NamedCharacter` snapshot, consumed exclusively by the import script. |
| **`import/katex-symbols.json`** | Official Snapshot | JSON Struct | Snapshot extracted from KaTeX `symbols.ts`, used for symbol synchronization. |

---

## 3. Schema & Field Contract Specifications

### 3.1 `kana.csv` (Japanese Syllabary Source)

- **`codes`**: Supports concurrent Kunrei-shiki and Hepburn Romanization, separated by ` | ` (e.g., `si | shi`).
- **`family`**: Syllabary family classification; valid values are `gojuon` (五十音), `youon` (拗音), `sokuon` (促音), and `small` (小假名).
- **Sanitization & Filtering Rules**:
  - Rows with `kata == "?"` are skipped during generation (special loanword kana are defined in dedicated entries).
  - Legacy dirty entry `ccye` is filtered out.
  - Isolated `n` / `nn` entries are omitted from the longest-match dictionary (managed at runtime by `jp_draft.lua`'s Pending-N state machine).
  - Rows where `family == "sokuon"` and `codes` begins with `nn` are excluded to prevent faulty sokuon splitting (e.g., preventing `konnichiha` $\rightarrow$ `こっにちは`).

### 3.2 `latin-accents.csv` (Latin Accents)

- **Code Structure**: Source CSV `codes` contain a leading semicolon (e.g., `;a` $\rightarrow$ `á`, `;;` $\rightarrow$ `；`).
- **Compiler Stripping**: `gen_overlay.py` strips the leading `;` and configures `prefix: ";"` in the generated `overlay/latin.dict.yaml`.
- **Case Mapping**: Uppercase input codes map directly to their uppercase accented counterparts (e.g., `;A` $\rightarrow$ `Á`).
- **Identity Filtering**: Rows where the glyph is an ASCII `;` are filtered out.

### 3.3 `math-symbols.csv` & `typst-extra.csv` (Math & Command Wide Table)

`math-symbols.csv` defines 10 standard columns, expanded horizontally by the compiler into normalized kinds:

| Normalized Kind | Data Column Source | Associated Toggle Flag | Dialect & Annotation Notes |
| :--- | :--- | :--- | :--- |
| **`latex`** | `latex` column | `kino_latex` | TeX/AMS/unicode-math native control sequences (e.g., `\alpha`) |
| **`latex-alias`** | `latex_alias` column | `kino_latex` | Community convenience macros and aliases (annotated as `[latex*]`) |
| **`katex`** | `katex` column | `kino_katex` | Dedicated math macros supported by KaTeX |
| **`typst-sym`** | `typst` column | `kino_typst` | Standard Typst symbol identifiers (e.g., `arrow.r`) |
| **`typst-shorthand`** | `typst_shorthand` column | `kino_typst` | Typst shorthand notations (e.g., `->`, `=>`) |
| **`typst-fn` / `typst-space` / `typst-op`** | `typst-extra.csv` | `kino_typst` | Typst functions and space formatting macros (e.g., `sin`, `quad`) |
| **`lean`** | `lean` column | `kino_lean` | Official Lean 4 input abbreviations |
| **`lean-shorthand`** | `lean_shorthand` column | `kino_lean` | Lean shorthand aliases |
| **`mma`** | `mma` column | `kino_mma` | Mathematica `NamedCharacter` identifiers (e.g., `Alpha`, unbracketed) |
| **`mma-alias`** | `mma_alias` column | `kino_mma` | Mathematica symbol shorthands (e.g., `->`) |
| **`unicode`** | `unicodedata` Compact Name | Always Enabled | Compact names derived from standard Unicode character names |

#### 2-Gram Inverted Index Generation Rules

1. **Tokenization & Normalization**: All ASCII characters undergo `lower()` normalization during index building and runtime query lookup.
2. **2-Gram Substring Window**: Fixed sliding window parameter $\text{GRAM\_N} = 2$. Posting lists are constructed for all contiguous substrings of length $\ge 2$.
3. **Unicode Stopwords List**: When building indexes for Unicode character descriptions, the following 20 high-frequency stopwords and words of length $< 4$ are strictly omitted:
   ```
   of, the, and, or, to, in, on, a, an, with, for, from, by, at, as, is, small, letter, capital, sign, symbol
   ```
4. **Uncapped Postings**: To maximize mathematical symbol recall, inverted index posting lists are fully preserved without truncation.

### 3.4 `emoji.csv` (CLDR 46 Annotations)

1. **Base Lexicon Inheritance**: The compiler first duplicates the upstream baseline `proj-ref/oh-my-rime/opencc/emoji.txt`.
2. **High-Frequency Collision Gating**: When appending annotations from `emoji.csv`, strict length filters are applied:
   - Pure Chinese keywords must have length $\ge 3$ (e.g., `开心果` $\rightarrow$ 🥑).
   - Pure Latin keywords must have length $\ge 3$ (e.g., `cat` $\rightarrow$ 🐱).
   - Binding emojis to 1–2 character high-frequency Chinese words (e.g., `你`, `好`, `大`, `中`) is **strictly forbidden**, completely eliminating emoji noise in the pinyin hot-path.

---

## 4. Build, Deployment, and Verification Workflow

### 4.1 Compilation Pipeline

```bash
# 1. (Optional) Refresh Lean/MMA columns from offline snapshots (no network calls)
python3 scripts/import_math_symbols.py --lean-only

# 2. Execute full table compilation and 2-gram index generation
python3 scripts/gen_overlay.py --root . --overlay overlay

# 3. Sanity check: Ensure no legacy merged files are produced
test ! -f docs/drafts/commands.csv && echo "Sanity Check Passed."

# 4. Run automated test suite
python3 -m pytest tests/ -v

# 5. Execute deployment
./scripts/deploy.sh
```

---

## 5. Command Search Algorithm & Performance Budget

### 5.1 4-Tier Score Ranking Model

In `overlay/lua/command_draft.lua`, candidate matches are scored into four tiers (lower score = higher priority):

```
[User Keystroke \query]
      │
      ├── 0: Exact Match   ──> Code equals query (e.g., \alpha == alpha)
      │
      ├── 1: Prefix Match  ──> Code starts with query (e.g., \alp -> alpha)
      │
      ├── 2: Dotted Match  ──> For codes with '.', last segment prefix match (e.g., \l -> arrow.l)
      │
      └── 3: Infix (2-gram)──> Intersect 2-gram inverted index postings (e.g., \pha -> alpha)
```

### 5.2 Runtime Performance Budgets

| Metric | Budget Limit | Anti-Patterns & Prohibited Operations |
| :--- | :--- | :--- |
| **Pinyin Hot-Path Latency** | $\le 1.0\text{ ms}$ | No global Lua filters attached to pinyin; no runtime edit-distance algorithms. |
| **`\` Command Search Time** | $\le 5.0\text{ ms}$ | No dynamic CSV scanning during runtime; all queries hit pre-indexed `commands_idx.lua` tables in memory. |
| **Memory Footprint** | $\le 30\text{ MB}$ (Baseline) | No brute-force infix enumeration inside `commands.dict.yaml`; no `enable_completion` on large command dictionaries. |

---

## 6. Japanese Model Datasets & Distribution Contracts

Large Japanese datasets are supplied by `proj-ref/Insomnia1437-rime` and bypass the CSV compilation pipeline:

| Source File | Destination in User Directory | Specification & Contract |
| :--- | :--- | :--- |
| `proj-ref/Insomnia1437-rime/kagiroi.mozc.dict.yaml` | `kagiroi.mozc.dict.yaml` (~58MB) | Must preserve the `surface\|left right` format and native Mozc weights; **stripping IDs or inflating seed weights is strictly prohibited**. |
| `proj-ref/Insomnia1437-rime/kagiroi_matrix.dict.yaml` | `kagiroi_matrix.dict.yaml` (~98MB) | Mozc Bigram connection cost matrix. Initial compilation takes 1–2 minutes. |
| `proj-ref/Insomnia1437-rime/lua/kagiroi/*` | `lua/kagiroi/` | Contains `kagiroi_viterbi`, `segmenter`, `lru`, and `priority_queue`. Standalone translator wrappers are omitted. |

`overlay/jp.dict.yaml` serves as a wrapper declaring `import_tables: [kagiroi.mozc]`. For detailed interface contracts, see [`jp-viterbi.md`](../jp-viterbi.md).

---

## 7. Upstream & Reference Sources

- **[`proj-ref/oh-my-rime`](https://github.com/Mintimate/oh-my-rime)**: Upstream Mint Pinyin repository (synchronized as runtime baseline).
- **[`proj-ref/Insomnia1437-rime`](https://github.com/Insomnia1437/rime)**: Japanese Mozc dictionary and Viterbi connection matrix repository.
- **[`proj-ref/rime-spanish`](https://github.com/gkovacs/rime-spanish)**: Latin diacritics QWERTY layout reference.
- **`proj-arc/cloverplus`**: Historical Cloverplus archive (upstream [fkxxyz/rime-cloverpinyin](https://github.com/fkxxyz/rime-cloverpinyin)) for punctuation and mathematical symbol reference.

---

## 8. Associated Documentation

- [System Installation, Platform Deployment & OS Troubleshooting](../../README.en.md) (`README.en.md`)
- [Documentation Architecture & SSOT Governance](../README.en.md) (`docs/README.en.md`)
- [kino Key Interaction Specification & Engine Manual](../kino.en.md) (`docs/kino.en.md`)
- [Japanese Viterbi Engine & Matrix Backend Specification](../jp-viterbi.md) (`docs/jp-viterbi.md`)
- [Command wide-table and feature_gate kind contract](../math-symbols.md) (`docs/math-symbols.md`)
