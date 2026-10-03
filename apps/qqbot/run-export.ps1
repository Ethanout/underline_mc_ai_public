param(
  [Parameter(Mandatory = $true)]
  [string]$GroupId,
  [string]$Endpoint = "http://127.0.0.1:3000",
  [string]$TokenEnv = "ONEBOT_ACCESS_TOKEN",
  [string]$Action = "get_essence_msg_list",
  [string]$Output = "..\..\runtime\private\qq_group_digest",
  [switch]$Refresh
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$arguments = @(
  (Join-Path $scriptDir "src\qqbot\essence_exporter.py"),
  "--endpoint", $Endpoint,
  "--group-id", $GroupId,
  "--action", $Action,
  "--output", $Output,
  "--token-env", $TokenEnv
)
if ($Refresh) { $arguments += "--refresh" }
python @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
