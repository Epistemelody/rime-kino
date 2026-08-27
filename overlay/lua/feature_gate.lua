-- Drop latin / japanese / disabled command-table candidates when switches are off.
-- Command table_translator leaks are keyed by (glyph, matched code), not glyph
-- alone: α has latex/unicode kinds, but \a is only lean-shorthand.

local ok_feat, feat = pcall(require, "kino_features")
if not ok_feat or not feat then
  feat = {
    LATIN = "kino_latin",
    JAPANESE = "kino_japanese",
    on = function() return true end,
    kind_on = function() return true end,
  }
end

local M = {}

local function load_kinds(env)
  if env.kinds_by_code then
    return
  end
  env.kinds_by_code = {}
  local dir = rime_api.get_user_data_dir()
  local chunk = loadfile(dir .. "/lua/commands_idx.lua")
  local idx = chunk and chunk() or { rows = {} }
  for _, row in ipairs(idx.rows or {}) do
    local commit, code, kind = row[1], row[2], row[3]
    local by_code = env.kinds_by_code[commit]
    if not by_code then
      by_code = {}
      env.kinds_by_code[commit] = by_code
    end
    local list = by_code[code]
    if not list then
      list = {}
      by_code[code] = list
    end
    list[#list + 1] = kind
  end
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

local function has_tag(seg, tag)
  if not seg then
    return false
  end
  local ok, v = pcall(function()
    return seg:has_tag(tag)
  end)
  return ok and v
end

local function command_query(ctx)
  local raw = ctx.input or ""
  if raw:sub(1, 1) == "\\" then
    raw = raw:sub(2)
  end
  return raw:lower()
end

function M.init(env)
  load_kinds(env)
end

function M.func(input, env)
  load_kinds(env)
  local ctx = env.engine.context
  local seg = current_seg(env)
  local latin_on = feat.on(ctx, feat.LATIN)
  local jp_on = feat.on(ctx, feat.JAPANESE)
  local cmd = has_tag(seg, "command_draft")
  local latin = has_tag(seg, "latin")
  local kana = has_tag(seg, "kana")

  for cand in input:iter() do
    local keep = true
    if latin and not latin_on then
      keep = false
    elseif kana and not jp_on then
      keep = false
    elseif cand.type == "jp" and not jp_on then
      keep = false
    elseif cmd and cand.type ~= "cmd" then
      local by_code = env.kinds_by_code[cand.text]
      if by_code then
        keep = false
        local kinds = by_code[command_query(ctx)]
        if kinds then
          for i = 1, #kinds do
            if feat.kind_on(ctx, kinds[i]) then
              keep = true
              break
            end
          end
        end
      end
    end
    if keep then
      yield(cand)
    end
  end
end

return M
