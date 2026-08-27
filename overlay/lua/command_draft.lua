-- Query generated lua/commands_idx.lua. Only runs on \ prefix.

local ok_feat, feat = pcall(require, "kino_features")
if not ok_feat or not feat then
  feat = { kind_on = function() return true end }
end

local M = {}

local DIALECT_RANK = {
  latex = 1,
  ["latex*"] = 2,
  katex = 3,
  typst = 4,
  lean = 5,
  mma = 6,
  unicode = 7,
}

local function load_idx(env)
  if env.idx then
    return env.idx
  end
  local dir = rime_api.get_user_data_dir()
  local chunk = loadfile(dir .. "/lua/commands_idx.lua")
  if not chunk then
    env.idx = { n = 0, pre1 = {}, pre2 = {}, last1 = {}, last2 = {}, g2 = {}, kinds = {} }
    return env.idx
  end
  env.idx = chunk()
  return env.idx
end

local function row_at(idx, i)
  local g0 = string.unpack("<I4", idx.goff, (i - 1) * 4 + 1)
  local g1 = string.unpack("<I4", idx.goff, i * 4 + 1)
  local c0 = string.unpack("<I4", idx.coff, (i - 1) * 4 + 1)
  local c1 = string.unpack("<I4", idx.coff, i * 4 + 1)
  local glyph = idx.gblob:sub(g0, g1 - 1)
  local code = idx.cblob:sub(c0, c1 - 1)
  local kind = idx.kinds[idx.kid:byte(i)]
  return glyph, code, kind
end

local function each_idx(pack, fn)
  if not pack or pack == "" then
    return
  end
  for p = 1, #pack, 4 do
    fn((string.unpack("<I4", pack, p)))
  end
end

local function posting(idx, map2, map1, q)
  if q == "" then
    return nil
  end
  if #q >= 2 then
    return map2[q:sub(1, 2)]
  end
  return map1[q:sub(1, 1)]
end

local function dialect(kind)
  if not kind or kind == "" then
    return ""
  end
  if kind == "latex-alias" then
    return "latex*"
  end
  if kind == "latex" then
    return "latex"
  end
  if kind == "katex" then
    return "katex"
  end
  if kind:sub(1, 5) == "typst" then
    return "typst"
  end
  if kind:sub(1, 4) == "lean" then
    return "lean"
  end
  if kind:sub(1, 3) == "mma" then
    return "mma"
  end
  if kind == "unicode" then
    return "unicode"
  end
  return kind
end

local function comment_for(idx, ctx, commit, code)
  local kinds = {}
  local pack = posting(idx, idx.pre2, idx.pre1, code)
  each_idx(pack, function(i)
    local g, c, k = row_at(idx, i)
    if g == commit and c == code then
      kinds[#kinds + 1] = k
    end
  end)
  if #kinds == 0 then
    return code
  end
  local seen, dialects = {}, {}
  for i = 1, #kinds do
    local kind = kinds[i]
    if feat.kind_on(ctx, kind) then
      local d = dialect(kind)
      if d ~= "" and not seen[d] then
        seen[d] = true
        dialects[#dialects + 1] = d
      end
    end
  end
  if #dialects == 0 then
    return code
  end
  table.sort(dialects, function(a, b)
    local ra, rb = DIALECT_RANK[a] or 9, DIALECT_RANK[b] or 9
    if ra ~= rb then
      return ra < rb
    end
    return a < b
  end)
  return code .. " [" .. table.concat(dialects, " ") .. "]"
end

local function add_hit(hits, seen, score, i, commit)
  if seen[commit] and seen[commit] <= score then
    return
  end
  seen[commit] = score
  hits[#hits + 1] = { score, i, commit }
end

local function has_tag(seg, tag)
  if not seg then
    return false
  end
  local ok, v = pcall(function()
    return seg:has_tag(tag)
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

function M.func(input, env)
  local ctx = env.engine.context
  local seg = current_seg(env)
  if not seg then
    return
  end
  local q = ctx.input or ""
  if q:sub(1, 1) == "\\" then
    q = q:sub(2)
  elseif not has_tag(seg, "command_draft") then
    return
  end
  q = q:lower()
  if q == "" then
    yield(Candidate("cmd", seg.start, seg._end, "、", "\\"))
    yield(Candidate("cmd", seg.start, seg._end, "\\", "backslash"))
    yield(Candidate("cmd", seg.start, seg._end, "＼", "fullwidth"))
    return
  end
  local idx = load_idx(env)
  local hits, seen = {}, {}

  each_idx(posting(idx, idx.pre2, idx.pre1, q), function(i)
    local commit, code, kind = row_at(idx, i)
    if not feat.kind_on(ctx, kind) then
      return
    end
    if code == q then
      add_hit(hits, seen, 0, i, commit)
    elseif code:sub(1, #q) == q then
      add_hit(hits, seen, 1, i, commit)
    end
  end)

  each_idx(posting(idx, idx.last2, idx.last1, q), function(i)
    local commit, code, kind = row_at(idx, i)
    if not feat.kind_on(ctx, kind) then
      return
    end
    local last = code:match("%.([^%.]+)$")
    if last and last:sub(1, #q) == q then
      add_hit(hits, seen, 2, i, commit)
    end
  end)

  if #q >= 2 then
    each_idx(idx.g2[q:sub(1, 2)], function(i)
      local commit, code, kind = row_at(idx, i)
      if feat.kind_on(ctx, kind) and not (kind == "unicode" and #q < 4) then
        if code:find(q, 1, true) then
          add_hit(hits, seen, 3, i, commit)
        end
      end
    end)
  end

  table.sort(hits, function(a, b)
    if a[1] ~= b[1] then
      return a[1] < b[1]
    end
    return a[3] < b[3]
  end)

  local n = 0
  local yielded = {}
  for _, h in ipairs(hits) do
    local commit, code = row_at(idx, h[2])
    if commit and not yielded[commit] then
      yielded[commit] = true
      yield(Candidate("cmd", seg.start, seg._end, commit, comment_for(idx, ctx, commit, code)))
      n = n + 1
      if n >= 20 then
        break
      end
    end
  end
end

return M
