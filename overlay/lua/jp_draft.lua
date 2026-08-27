-- Romaji Japanese after ~. Keep convert() in sync with gen_overlay.romaji_to_kana.

local ok_feat, feat = pcall(require, "kino_features")
if not ok_feat or not feat then
  feat = { JAPANESE = "kino_japanese", on = function() return true end }
end

local M = {}

local vowels = { a = true, e = true, i = true, o = true, u = true }

local function load_jp(env)
  if env.jp then
    return env.jp
  end
  local dir = rime_api.get_user_data_dir()
  local chunk = loadfile(dir .. "/lua/jp_romaji.lua")
  env.jp = chunk and chunk() or { max_len = 1, map = {} }
  return env.jp
end

local function is_upper(ch)
  return ch:match("%u") ~= nil
end

local function want_kata(ch, script)
  if script == "kata" then
    return true
  end
  if script == "hira" then
    return false
  end
  return is_upper(ch)
end

local function prefer_katakana(s)
  for i = 1, #s do
    local ch = s:sub(i, i)
    if ch:match("%a") then
      return is_upper(ch)
    end
  end
  return false
end

-- Keep convert() in sync with gen_overlay.romaji_to_kana (including script=).
local function convert(s, pack, script)
  local map, max_len = pack.map or {}, pack.max_len or 1
  local n = #s
  local out = {}
  local i = 1
  local pending_n = false
  local pending_n_upper = false

  local function match_at(pos, prefix)
    local blob = (prefix or "") .. s:sub(pos)
    local lim = math.min(max_len, #blob)
    for length = lim, 1, -1 do
      local key = blob:sub(1, length):lower()
      local row = map[key]
      if row then
        return length, row
      end
    end
    return 0, nil
  end

  while i <= n do
    if pending_n then
      local ch = s:sub(i, i)
      local cl = ch:lower()
      if cl == "n" then
        out[#out + 1] = pending_n_upper and "ン" or "ん"
        local nxt = i < n and s:sub(i + 1, i + 1):lower() or ""
        if nxt == "" or (not vowels[nxt] and nxt ~= "y") then
          pending_n = false
          i = i + 1
        else
          pending_n_upper = want_kata(ch, script)
          i = i + 1
        end
      else
        local length, row = match_at(i, "n")
        if length > 0 and row then
          out[#out + 1] = pending_n_upper and row[2] or row[1]
          pending_n = false
          i = i + length - 1
        else
          out[#out + 1] = pending_n_upper and "ン" or "ん"
          pending_n = false
        end
      end
    else
      local ch = s:sub(i, i)
      local cl = ch:lower()
      if cl == "n" then
        pending_n = true
        pending_n_upper = want_kata(ch, script)
        i = i + 1
      elseif cl:match("%a") and not vowels[cl] and cl ~= "y" and i < n and s:sub(i + 1, i + 1):lower() == cl then
        out[#out + 1] = want_kata(ch, script) and "ッ" or "っ"
        i = i + 1
      else
        local length, row = match_at(i)
        if length > 0 and row then
          out[#out + 1] = want_kata(ch, script) and row[2] or row[1]
          i = i + length
        else
          break
        end
      end
    end
  end
  if pending_n then
    out[#out + 1] = pending_n_upper and "ン" or "ん"
  end
  return table.concat(out), s:sub(i)
end

local function tagged_kana(seg)
  if not seg then
    return false
  end
  local ok, v = pcall(function()
    return seg:has_tag("kana")
  end)
  return ok and v
end

local function current_seg(env)
  local ok, seg = pcall(function()
    local comp = env.engine.context.composition
    if not comp or comp:empty() then
      return nil
    end
    return comp:back()
  end)
  if ok then
    return seg
  end
  return nil
end

function M.init(env)
end

function M.fini(env)
  if env.viterbi then
    pcall(function()
      env.viterbi:clear()
    end)
  end
  local mem = env.mem or env.kanji_mem
  if mem then
    pcall(function()
      mem:disconnect()
    end)
  end
  env.viterbi = nil
  env.mem = nil
  env.kanji_mem = nil
  env.matrix_lookup = nil
  env._matrix_rev = nil
end

-- Lazy: Memory(jp) + ReverseLookup(kagiroi_matrix) + kagiroi Viterbi.
-- Same Memory seam as mint unicode_translator. No dummy-segment translator.
-- Do not require the kagiroi translator or kana speller modules.
local function ensure_viterbi(env)
  if env.viterbi then
    return env.viterbi
  end
  if env.viterbi == false then
    return nil
  end
  local ok, vit = pcall(function()
    env.mem = Memory(env.engine, Schema("jp"), "translator")
    env.matrix_lookup = function()
      if not env._matrix_rev then
        env._matrix_rev = ReverseLookup("kagiroi_matrix")
      end
      return env._matrix_rev
    end
    return require("kagiroi/kagiroi_viterbi").new(env)
  end)
  if not ok or not vit then
    env.viterbi = false
    return nil
  end
  env.viterbi = vit
  return vit
end

-- Yield lex.candidate only. Never leak `表面|id id`.
local function sentence_text(lex)
  if not lex then
    return nil
  end
  local text = lex.candidate
  if type(text) ~= "string" or text == "" then
    return nil
  end
  if text:match("|%-?%d+ %-?%d+") then
    return nil
  end
  return text
end

local function yield_sentences(vit, hira, seg, skip)
  if not vit or not hira or hira == "" then
    return
  end
  local ok = pcall(function()
    vit:analyze(hira)
    local iter = vit:best_n()
    local n = 0
    while n < 2 do
      local lex = iter()
      if not lex then
        break
      end
      local text = sentence_text(lex)
      if text and not skip[text] then
        skip[text] = true
        yield(Candidate("jp", seg.start, seg._end, text, hira))
        n = n + 1
      end
    end
  end)
  if not ok then
    pcall(function()
      vit:clear()
    end)
  end
end

function M.func(input, env)
  local ctx = env.engine.context
  if not feat.on(ctx, feat.JAPANESE) then
    return
  end
  local seg = current_seg(env)
  if not seg then
    return
  end
  local q = ctx.input or ""
  if q:sub(1, 1) == "~" then
    q = q:sub(2)
  elseif not tagged_kana(seg) then
    return
  end
  if q == "" then
    return
  end
  local pack = load_jp(env)
  local ok_h, hira, rest = pcall(convert, q, pack, "hira")
  if not ok_h then
    return
  end
  local ok_k, kata = pcall(convert, q, pack, "kata")
  if not ok_k then
    kata = ""
  end
  rest = rest or ""
  hira = hira or ""
  kata = kata or ""
  local kata_first = prefer_katakana(q)
  local first = kata_first and kata or hira
  local second = kata_first and hira or kata
  if first ~= "" then
    yield(Candidate("jp", seg.start, seg._end, first, rest ~= "" and rest or (kata_first and "カナ" or "かな")))
  end
  if second ~= "" and second ~= first then
    yield(Candidate("jp", seg.start, seg._end, second, kata_first and "かな" or "カナ"))
  end
  if hira ~= "" then
    local skip = { [hira] = true, [kata] = true }
    yield_sentences(ensure_viterbi(env), hira, seg, skip)
  end
  if rest ~= "" and hira == "" and kata == "" then
    yield(Candidate("jp", seg.start, seg._end, rest, "…"))
  end
  if input and input.iter then
    for cand in input:iter() do
      yield(cand)
    end
  end
end

return M
