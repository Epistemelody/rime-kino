-- Pinyin/abc caps at 25 (mint). Prefixed channels keep the 256 hard cap.
local kAccepted = 1
local kNoop = 2
local PINYIN_CAP = 25
local PREFIX_CAP = 256
local PREFIX = {
  ["\\"] = true,
  ["~"] = true,
  [";"] = true,
}

local M = {}

function M.func(key, env)
  if key:release() or key:ctrl() or key:alt() or key:super() then
    return kNoop
  end
  local r = key:repr() or ""
  if not (#r == 1 and r:match("%a")) then
    return kNoop
  end
  local ctx = env.engine.context
  local input = ctx.input or ""
  local cap = PREFIX[input:sub(1, 1)] and PREFIX_CAP or PINYIN_CAP
  if #input >= cap then
    ctx:pop_input(1)
    return kAccepted
  end
  return kNoop
end

return M
