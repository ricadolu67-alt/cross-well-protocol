$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $repoRoot "reproduction\recompute_headline.py")
