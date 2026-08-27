-- Absorb prefix extras before key_binder (page) and punctuator.
-- mint default.yaml: has_menu period/equal → Page_Down; paging minus → Page_Up.
-- ? and - stay out of the pinyin alphabet; they only join encoding after ; / ~ / \.
local kAccepted = 1
local kNoop = 2
local extras = {
  ["\\"] = [=[.-><=!~*:|[]^_+(){}'?/#&`"$%]=],
  [";"] = "?",
  ["~"] = "-",
}
local named = {
  period = ".",
  minus = "-",
  equal = "=",
  greater = ">",
  less = "<",
  exclam = "!",
  asterisk = "*",
  asciitilde = "~",
  colon = ":",
  bar = "|",
  bracketleft = "[",
  bracketright = "]",
  question = "?",
  asciicircum = "^",
  underscore = "_",
  plus = "+",
  parenleft = "(",
  parenright = ")",
  braceleft = "{",
  braceright = "}",
  apostrophe = "'",
  quotedbl = '"',
  slash = "/",
  numbersign = "#",
  ampersand = "&",
  grave = "`",
  dollar = "$",
  percent = "%",
}

local function in_extra(extra, ch)
  return extra:find(ch, 1, true) ~= nil
end

local function command_char(key, extra)
  local r = key:repr() or ""
  if named[r] then
    local ch = named[r]
    if in_extra(extra, ch) then
      return ch
    end
    return nil
  end
  if #r == 1 and in_extra(extra, r) then
    return r
  end
  local code = key.keycode
  if code and code >= 0x20 and code <= 0x7e then
    local ch = string.char(code)
    if in_extra(extra, ch) then
      return ch
    end
  end
  return nil
end

local M = {}

function M.func(key, env)
  if key:release() or key:ctrl() or key:alt() or key:super() then
    return kNoop
  end
  local ctx = env.engine.context
  local input = ctx.input or ""
  local extra = extras[input:sub(1, 1)]
  if not extra then
    return kNoop
  end
  local ch = command_char(key, extra)
  if not ch then
    return kNoop
  end
  ctx:push_input(ch)
  return kAccepted
end

return M
