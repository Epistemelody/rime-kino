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
    env.idx = { rows = {}, g2 = {}, kinds_by_code = {} }
    return env.idx
  end
  local idx = chunk()
  idx.rows = idx.rows or {}
  idx.g2 = idx.g2 or {}
  local kinds_by_code = {}
  for _, row in ipairs(idx.rows) do
    local commit, code, kind = row[1], row[2], row[3]
    local by_code = kinds_by_code[commit]
    if not by_code then
      by_code = {}
      kinds_by_code[commit] = by_code
    end
    local list = by_code[code]
    if not list then
      list = {}
      by_code[code] = list
    end
    list[#list + 1] = kind
  end
  idx.kinds_by_code = kinds_by_code
  env.idx = idx
  return env.idx
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
  local by_code = idx.kinds_by_code and idx.kinds_by_code[commit]
  local kinds = by_code and by_code[code]
  if not kinds then
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
  local ctx = env.engine.context
  local idx = load_idx(env)
  local rows, g2 = idx.rows or {}, idx.g2 or {}
  local hits, seen = {}, {}

  for i, row in ipairs(rows) do
    local code, kind = row[2], row[3]
    if feat.kind_on(ctx, kind) then
      if code == q then
        add_hit(hits, seen, 0, i, row[1])
      elseif code:sub(1, #q) == q then
        add_hit(hits, seen, 1, i, row[1])
      else
        local last = code:match("%.([^%.]+)$")
        if last and last:sub(1, #q) == q then
          add_hit(hits, seen, 2, i, row[1])
        end
      end
    end
  end

  if #q >= 2 then
    local gram = q:sub(1, 2)
    local posting = g2[gram]
    if posting then
      for _, i in ipairs(posting) do
        local row = rows[i]
        if row then
          local code, kind = row[2], row[3]
          if feat.kind_on(ctx, kind) and not (kind == "unicode" and #q < 4) then
            if code:find(q, 1, true) then
              add_hit(hits, seen, 3, i, row[1])
            end
          end
        end
      end
    end
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
    local row = rows[h[2]]
    if row and not yielded[row[1]] then
      yielded[row[1]] = true
      yield(Candidate("cmd", seg.start, seg._end, row[1], comment_for(idx, ctx, row[1], row[2])))
      n = n + 1
      if n >= 20 then
        break
      end
    end
  end
end

return M
