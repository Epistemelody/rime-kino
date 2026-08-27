# Japanese Viterbi on kino `~`

| Field | Value |
| --- | --- |
| Audience | Anyone changing `scripts/deploy.py` Japanese assets or `overlay/lua/jp_draft.lua` |
| Status | Current |
| Revised | 2026-08-27 |
| This document owns | Deploy/lua contract: Mozc `\|ids`, native weights, lazy Viterbi, candidate text |
| This document does not own | User-visible key order (see `docs/kino.md`); CSV columns (see `docs/drafts/README.md`) |

You can implement or review the Japanese deploy path from this file alone. Product examples below are the acceptance set; the full key contract is `docs/kino.md` §8.3.

kino hangs Japanese on mint as `~`. Romaji becomes hiragana in `jp_draft`, then kagiroi Viterbi (`1e8 * exp(weight)` plus Mozc connection cost). Space still commits the first candidate. Do not add a カギロイ schema.

Source files stay in `proj-ref/Insomnia1437-rime/` (read-only, GPLv3). Deploy copies them into the user Rime dir.

---

## Scenario: Mozc IDs must survive into Viterbi

### 1. Scope / Trigger

- Trigger: any change to `scripts/deploy.py` Japanese assets, `overlay/lua/jp_draft.lua`, `overlay/jp.dict.yaml`, or `overlay/jp.schema.yaml`.
- Cross-layer: `kagiroi.mozc.dict.yaml` text is `表面|left right`. Strip that and Viterbi yields nothing. Yield `entry.text` and the user sees `今日|1913 1913`.

### 2. Signatures

```text
deploy_jp_assets(dest: Path) -> None
has_mozc_ids(path: Path) -> bool
has_legacy_seed_boost(path: Path) -> bool
skip_heavy_jp_dict() -> bool   # SKIP_JP_DICT or (RIME_DIR and not FORCE_JP_DICT)
keep_existing_heavy_dict(path, *, kind, force=False) -> bool

jp_draft.ensure_viterbi(env) -> viterbi | nil
jp_draft.yield_sentences(vit, hira, seg, skip)
kagiroi_viterbi.new(env)       # env.mem, env.matrix_lookup thunk
viterbi:analyze(hira); viterbi:best_n() -> iter of { candidate, surface, cost, left_id, right_id }
```

Environment:

| Key | Effect |
| --- | --- |
| `RIME_DIR` | Deploy target. Skips ~150MB copy unless `FORCE_JP_DICT=1` |
| `SKIP_JP_DICT` | Same skip. Still writes the `jp` import wrapper and deletes `build/jp.*` |
| `FORCE_JP_DICT` | Recopy mozc + matrix even if a large ID-bearing file exists |

### 3. Contracts

| Field / env | Constraint |
| --- | --- |
| Mozc line | `今日\|1913 1913<TAB>きょう<TAB>121` |
| Dest `jp.dict.yaml` | Import wrapper only: `import_tables: [kagiroi.mozc]`. No 90MB body. |
| Dest lex | `kagiroi.mozc.dict.yaml` keeps `\|ids` and **native Mozc weights**. Do not raise 今日/私/東京 to 100000. |
| Native weights that must survive | 今日/きょう `121`；私/わたし `263`；東京/とうきょう `0` |
| Matrix | `kagiroi_matrix.dict.yaml` + `.schema.yaml`. `ReverseLookup("kagiroi_matrix")` key is `"left right"`. |
| Lua allowlist | `kagiroi.lua`, `kagiroi_viterbi.lua`, `segmenter.lua`, `lru.lua`, `priority_queue.lua` |
| Lua forbidden | `kagiroi_translator.lua`, `kagiroi_kana_speller.lua` (delete if present) |
| Candidate | `lex.candidate` only. Drop if it matches `\|-?\d+ -?\d+`. |
| Lazy load | Memory / ReverseLookup / `viterbi.new` on first `~` query, not `init`. |
| Schema list | `rime_mint` + `kana`. Do not add kagiroi. |

### 4. Validation & Error Matrix

| Condition | Behavior |
| --- | --- |
| Viterbi `pcall` fails | Yield 平/片 only; `viterbi:clear()`; no crash |
| `lex.candidate` contains `\|ids` | Skip that candidate |
| Dest `jp.dict.yaml` is old stripped 40MB+ table | Write import wrapper + `invalidate_jp_build` |
| Dest mozc contains `今日\|1913 1913\tきょう\t100000` | Stale boost; recopy from proj-ref |
| Dummy-segment `Component.Translator` on `jp` | Forbidden (librime 1.14: zero hits) |

### 5. Good / Base / Bad Cases

- Good: `~watashiha` → わたしは / ワタシハ / 私は
- Good: `~toukyouni` → とうきょうに / 東京に
- Base: `~kyou` → きょう / キョウ / 今日
- Bad: strip `\|ids`; yield `entry.text`; keep stale `build/jp.table.bin`; boost seeds to 100000 (menu becomes 教 / 渡し / TOKYO)

### 6. Tests Required

- `has_legacy_seed_boost` is true for a fat file containing `今日|1913 1913\tきょう\t100000`; `keep_existing_heavy_dict(..., kind="mozc")` is false
- `FORCE_JP_DICT=1` dest contains `今日|1913 1913\tきょう\t121` and `lua/kagiroi/kagiroi_viterbi.lua`, not translator/speller
- Dry-run `RIME_DIR` without force: no `kagiroi.mozc.dict.yaml`; dest `jp.dict.yaml` is the wrapper
- `jp_draft`: no `Component.Translator`; `ensure_viterbi` not called from `init`

Commands:

```bash
python3 -m pytest tests/test_deploy.py tests/test_jp_romaji.py tests/test_overlay_branding.py -q
```

### 7. Wrong vs Correct

#### Wrong

```python
text = parts[0].split("|", 1)[0]
return f"{text}\t{code}\t{weight}"
```

```lua
yield(Candidate("jp", start, _end, entry.text, reading))
```

#### Correct

```python
shutil.copy2(MOZC, dest / "kagiroi.mozc.dict.yaml")
write_jp_import_wrapper(dest / "jp.dict.yaml")
invalidate_jp_build(dest)
```

```lua
yield(Candidate("jp", seg.start, seg._end, lex.candidate, hira))
```

---

## Related

- `docs/kino.md` — key → commit, including `~` romaji
- `README.md` — install, `RIME_DIR` / `FORCE_JP_DICT`
- `docs/drafts/README.md` — CSV tables (Japanese lex is not a CSV)
