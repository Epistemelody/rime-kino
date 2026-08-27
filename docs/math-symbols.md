# Command math-symbols table

| Field | Value |
| --- | --- |
| Audience | Anyone changing `docs/drafts/math-symbols.csv`, `typst-extra.csv`, `scripts/gen_overlay.py`, `scripts/import_math_symbols.py`, or command lua |
| Status | Current |
| Revised | 2026-08-27 |
| This document owns | Wide-table columns → kinds → `commands_idx` → switches / `feature_gate`; command punct extras |
| This document does not own | User-visible menu order (see `docs/kino.md`); CSV file list narrative (see `docs/drafts/README.md`) |

You can implement or review the `\` command pipeline from this file. Product examples are the acceptance set; the full key contract is `docs/kino.md` §8.

---

## Scenario: glyph-primary wide table into command draft

### 1. Scope / Trigger

- Trigger: any change to `math-symbols.csv`, `typst-extra.csv`, `import_math_symbols.py`, `collect_command_rows`, `COMMAND_EXTRA`, `command_keys.lua`, `command_draft.lua`, `feature_gate.lua`, or `kino_features.lua` kinds.
- Cross-layer: a CSV code that never appears in `commands_idx` cannot match. A punct char missing from extras/`recognizer` cannot be typed after `\`. Gating the fallback `table_translator` by **glyph kinds** lets `\a` leak as α while `kino_lean` is off.

### 2. Signatures

```text
iter_source_command_codes(draft: Path) -> iter[str]
collect_command_rows(draft: Path) -> list[{commit, code, kind, glyph}]
pack_command_index(rows) -> (packed[(commit, code.lower(), kind)], g2)
command_code(code: str) -> bool          # alnum or COMMAND_EXTRA
split_codes(cell: str) -> list[str]      # split on " | "

import_math_symbols.py [--lean-only]
  # offline. --lean-only rewrites lean columns and apply_mma on current glyphs.

kino_features.kind_on(ctx, kind) -> bool
feature_gate kinds_by_code[glyph][query] -> [kind]
```

`MATH_CODE_COLS` (column → kind):

| column | kind | switch |
| --- | --- | --- |
| `latex` | `latex` | `kino_latex` |
| `latex_alias` | `latex-alias` | `kino_latex` |
| `katex` | `katex` | `kino_katex` |
| `typst` | `typst-sym` | `kino_typst` |
| `typst_shorthand` | `typst-shorthand` | `kino_typst` |
| `lean` | `lean` | `kino_lean` |
| `lean_shorthand` | `lean-shorthand` | `kino_lean` |
| `mma` | `mma` | `kino_mma` |
| `mma_alias` | `mma-alias` | `kino_mma` |

`typst-extra.csv` keeps its own `kind` (`typst-fn` / `typst-space` / `typst-op`). unicodedata compact names are kind `unicode` (always on).

### 3. Contracts

| Field | Constraint |
| --- | --- |
| SoT | `docs/drafts/math-symbols.csv`: one row per glyph. Aliases ` \| `. |
| Generator inputs | That file + `typst-extra.csv` + unicodedata. Do **not** read `latex.csv` / `math-catalog.csv` / `typst-shorthand.csv`. |
| Forbidden commit | `docs/drafts/commands.csv` |
| MMA | Store `Alpha`, never `[Alpha]`. `collect_command_rows` drops `mma` codes that are `[...]`. |
| Case | Index and query `lower()` letters only. Punct stays. Dedup by **glyph**, not by code: `\alpha` / `\Alpha` must yield α **and** Α. |
| Lean shorthand | `len(abbrev) <= 2` or no alnum. Drop abbrevs with space or embedded `\`. |
| Import | No network. Lean JSON + `mma-named.json` live under `docs/drafts/import/`. `gen_overlay.py` does not read them. |
| MMA scope | NamedCharacter ∩ table glyphs only. No Wolf / currency zoo. |
| `COMMAND_EXTRA` | Must equal punct in `iter_source_command_codes` (except space / `\`). Same set in `command_keys` extras for `\` and `recognizer/patterns/command_draft`. |
| Comment | Winning **code** + all enabled dialects that share that exact code: `alpha [latex katex typst lean mma]`. Order: latex, latex*, katex, typst, lean, mma, unicode. `latex*` is `latex-alias` (`proj-arc` custom latex / `^2`). Do not merge different codes (`a` vs `alpha`) into one bracket. |
| latex vs latex_alias | Native = unicode-math-table (+ mup/up strip) ∪ LATEX_CLASSIC_EXTRA, minus LATEX_FORCE_ALIAS and any code with `^_()[]`. Re-run `--split-latex`. |
| Fallback gate | `feature_gate` on `command_draft` + non-`cmd` cand: keep iff some kind of `(glyph, lower(query))` is on. Not “any kind on this glyph”. |
| Switches | `kino_lean` / `kino_mma` in mint (`reset: 1`) and `switcher/save_options`. |

### 4. Validation & Error Matrix

| Condition | Behavior |
| --- | --- |
| Same Lean abbrev → two glyphs | `import_math_symbols.py` exits non-zero |
| `mma` cell is `[Alpha]` | Dropped at generate; tests forbid `[alpha]` in the index |
| `kino_lean` off | `\a` must not yield α from lua **or** `table_translator` |
| All dialect switches off | unicode names and empty `\` (`、`) still work |
| New Lean punct not in extras | `test_command_index` extras equality fails — update the three copies together |
| Old split CSVs still listed as required | `test_tables` must fail |

### 5. Good / Base / Bad Cases

- Good: `\a` → α (lean-shorthand); `\alpha` / `\Alpha` → α and Α
- Good: `\->` / `\to` → →; `\forall` / `\all` → ∀; `\!=` → ≠; `\|->` → ↦; `\^2` → ²
- Base: `\frac` still frac or ⁄; `\sin` still sin; `\pha` still α
- Bad: index `[alpha]`; gate by glyph kinds so `\a` leaks; read `latex.csv` in `collect_command_rows`; raise Japanese Mozc seed weights while touching this path

### 6. Tests Required

```bash
python3 -m pytest tests/test_tables.py tests/test_gen_overlay.py tests/test_command_index.py tests/test_overlay_branding.py -q
python3 scripts/gen_overlay.py --root . --overlay overlay
test ! -f docs/drafts/commands.csv
```

Assert: every source code is in the packed index (lowered); source punct ⊆ `COMMAND_EXTRA` and matches lua/recognizer; no `[alpha]`; `alpha` hits α and Α; `\a` kinds are lean-shorthand only for the gate.

### 7. Wrong vs Correct

#### Wrong

```lua
-- feature_gate: any kind on glyph α is enough
for i = 1, #kinds_by_commit[cand.text] do
  if feat.kind_on(ctx, kinds[i]) then keep = true end
end
```

`\a` stays if latex or unicode is on.

#### Correct

```lua
local kinds = env.kinds_by_code[cand.text][command_query(ctx)]
-- only kinds that actually produced this query
```

---

## Common Mistake: extras drift

**Symptom**: Lean `{` / `'` / `/` is in the CSV but `\` + that key never joins the encoding.

**Cause**: `COMMAND_EXTRA`, `command_keys.lua` extras, and the mint recognizer were edited separately.

**Fix**: Change all three in one commit. Tests compare them to `iter_source_command_codes`.

**Prevention**: Do not recompute extras only in the import script.

---

## Don't: treat old split tables as SoT

`latex.csv` / `math-catalog.csv` / `typst-shorthand.csv` were folded once. Git history can restore them for a full fold; `gen_overlay.py` must not read them. Refresh Lean with `python3 scripts/import_math_symbols.py --lean-only`.
