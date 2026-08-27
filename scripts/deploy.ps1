$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
python "$Root/scripts/gen_overlay.py" --root "$Root" --overlay "$Root/overlay"
python "$Root/scripts/deploy.py"
