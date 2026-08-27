-- Feature switches for kino. Default on via schema reset: 1.
-- Names must match rime_mint.custom.yaml switches and switcher/save_options.

local M = {}

M.TYPST = "kino_typst"
M.LATEX = "kino_latex"
M.KATEX = "kino_katex"
M.LEAN = "kino_lean"
M.MMA = "kino_mma"
M.LATIN = "kino_latin"
M.JAPANESE = "kino_japanese"
M.EMOJI = "emoji_suggestion"

function M.on(ctx, name)
  if not ctx or not name then
    return true
  end
  local ok, v = pcall(function()
    return ctx:get_option(name)
  end)
  if not ok or v == nil then
    return true
  end
  return not not v
end

function M.kind_on(ctx, kind)
  if not kind or kind == "" then
    return true
  end
  if kind:sub(1, 5) == "latex" then
    return M.on(ctx, M.LATEX)
  end
  if kind == "katex" then
    return M.on(ctx, M.KATEX)
  end
  if kind:sub(1, 5) == "typst" then
    return M.on(ctx, M.TYPST)
  end
  if kind:sub(1, 4) == "lean" then
    return M.on(ctx, M.LEAN)
  end
  if kind:sub(1, 3) == "mma" then
    return M.on(ctx, M.MMA)
  end
  return true
end

return M
