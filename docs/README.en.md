# kino Documentation Architecture & Governance

[简体中文](README.md) | [English](README.en.md)

| Attribute | Specification |
| :--- | :--- |
| **Project** | **kino** (Rime Overlay Architecture, Schema ID: `rime_mint`) |
| **Repository** | `rime-kino` |
| **Document Role** | Defines documentation topology, Single Source of Truth (SSOT) hierarchy, conflict arbitration rules, and role-based reading journeys |
| **Out of Scope** | OS-specific package manager commands (see root `README.md`), exhaustive keystroke interaction rules (see `kino.md`), CSV column definitions (see `drafts/README.md`) |
| **Status** | Active Normative |
| **Revision** | 2026-08-27 |

---

## 1. Architecture Positioning & Documentation Philosophy

The kino project enforces strict **Single Source of Truth (SSOT)** and **modular self-containment** principles across its technical documentation suite:

1. **Self-Contained Modules**: Each document is fully self-sufficient within its designated technical boundary. Readers can execute the complete technical workflow promised by a document's scope without cross-document step hunting.
2. **Separation of Authority**: Every technical decision, contract interface, and configuration parameter has exactly one authoritative reference document.
3. **Zero Divergence**: Duplicating or re-interpreting rules in non-authoritative documents is strictly prohibited; cross-domain dependencies are managed exclusively via explicit links.

---

## 2. Documentation Topology & Responsibility Matrix

```
                                  docs/README.md
                        (Doc Topology Map & SSOT Hub)
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
     README.md                      docs/kino.md               docs/drafts/README.md
(Install/Deploy/OS Triage)     (Interaction/Channel Contracts)   (Data Schema/Compiler/Perf)
         │                               │                               │
         ▼                               ▼                               ▼
System Env / Packages          Keystroke Commit / Lua Pipeline    CSV Columns / 2-gram Index
```

### Responsibility & Boundary Definitions

| Document Path | Target Audience | Authoritative Scope | Explicit Non-Responsibilities |
| :--- | :--- | :--- | :--- |
| **[`../README.md`](../README.en.md)**<br>([简体中文](../README.md)) | New users, system administrators, CI/CD maintainers | Repository cloning, submodule management, cross-platform configuration, deployment automation, minimal verification matrix, OS triage | Exhaustive keystroke mappings, internal CSV database schemas |
| **[`kino.md`](kino.en.md)**<br>([简体中文](kino.md)) | End users, UX/engine developers, QA validation engineers | Complete keystroke-to-commit contracts, prefix channels (`\` / `;` / `~`), candidate window typography, punctuation and emoji rules, full manual test matrix | Package installation commands, shell environment variable exports |
| **[`drafts/README.md`](drafts/README.en.md)**<br>([简体中文](drafts/README.md)) | Lexicon contributors, data engineers, compiler maintainers | `docs/drafts/*.csv` schema definitions, compilation pipeline, 2-gram inverted index architecture, OpenCC transformations, build performance budgets | UI visual styling and candidate window layout (governed by `kino.md`) |
| **[`jp-viterbi.md`](jp-viterbi.md)** | Engine maintainers | Mozc dictionary format, Viterbi connection costs, Japanese Lua deploy contract | User-visible key order (governed by `kino.md`) |
| **`drafts/*.csv`** | Automation compilers, data maintainers | Raw tabular source datasets for lexicons and symbols | Interaction narrative and UI logic specifications |

---

## 3. Authority Hierarchy & Single Source of Truth (SSOT)

When technical discrepancies arise across documentation, code comments, or historical configs, the following hierarchy is binding:

| Technical Domain / Decision Topic | Authoritative SSOT | Arbitration Rule |
| :--- | :--- | :--- |
| **System dependencies, deploy scripts, environment variables, OS troubleshooting** | Root `README.md` | Governed exclusively by the root README; other documents must not specify installation dependencies. |
| **Keystroke sequences, prefix channels, candidate window behavior, Shift semantics** | `docs/kino.md` | User interactions, shortcuts, candidate formatting, and annotation syntax are strictly defined by `kino.md`. |
| **CSV schemas, git-tracked file whitelists, 2-gram indexing, OpenCC rules** | `docs/drafts/README.md` | Data pipeline layouts, field mapping rules, commit boundaries, and compiler budgets are governed by `drafts/README.md`. |
| **Mozc dictionary format, Viterbi connection costs, Japanese Lua memory management** | `docs/jp-viterbi.md` | Boundary contracts between deploy scripts and Lua Viterbi engines are governed by the Viterbi specification (raw weights must remain unmodified). |

---

## 4. Role-Based Reading Journeys

### Journey A: End Users & Daily Typists
1. Consult the root **[`README.md`](../README.en.md)** to install dependencies and execute the one-click deployment.
2. Read **[`docs/kino.md`](kino.en.md)** to master prefix channels (LaTeX/Typst math symbols, Latin accents, Japanese kana, and Viterbi kanji).

### Journey B: Lexicon & Symbol Contributors
1. Review **[`docs/drafts/README.md`](drafts/README.en.md)** to understand CSV schemas and categorization criteria.
2. Cross-reference **[`docs/kino.md`](kino.en.md)** to verify candidate formatting, annotations, and deduplication behavior in the UI.
3. Execute `python3 scripts/gen_overlay.py` and run `pytest tests/` for regression validation.

### Journey C: Core Engine & Cross-Platform Maintainers
1. Study **[`README.md`](../README.en.md)** and **[`docs/kino.md`](kino.en.md)** to enforce platform invariants (`PreeditMode="Do not show"`, `SwitchInputMethodBehavior="Commit raw input"`).
2. Read **[`jp-viterbi.md`](jp-viterbi.md)** to inspect Mozc dictionary integration and connection matrix lifecycle management.

---

## 5. External & Upstream References

Rendered site: [epistemelody.github.io/rime-kino](https://epistemelody.github.io/rime-kino/).

- **Mint Pinyin Upstream**: [`proj-ref/oh-my-rime`](https://github.com/Mintimate/oh-my-rime) (read-only vendor submodule for baseline Chinese lexicons and the main schema).
- **Mozc Japanese Model**: [`proj-ref/Insomnia1437-rime`](https://github.com/Insomnia1437/rime) (read-only vendor submodule for dictionaries and bigram connection-cost matrices).
- **Double-pinyin layout**: [`proj-ref/iamcheyan-rime`](https://github.com/iamcheyan/rime)
- **Pinyin-Japanese reference**: [`proj-ref/rime-pinyin-jap`](https://github.com/tumuyan/rime-pinyin-jap)
- **Latin diacritics**: [`proj-ref/rime-spanish`](https://github.com/gkovacs/rime-spanish)
- **Cloverplus Archive**: `proj-arc/cloverplus` (historical reference, not runtime code; upstream [fkxxyz/rime-cloverpinyin](https://github.com/fkxxyz/rime-cloverpinyin)).
