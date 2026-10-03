param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$archiveRoot = Join-Path $workspaceRoot '.archive/2026-10-02'
$manifestPath = Join-Path $archiveRoot 'manifest.json'
$targets = @(
    @{ Path = 'external/llm_wiki'; Reason = 'Standalone upstream reference; not imported by the application.' },
    @{ Path = 'external/minecraft-mod-mcp'; Reason = 'Upstream snapshot; runtime uses the published npm package.' },
    @{ Path = 'legacy/mineflayer-bot'; Reason = 'Disabled legacy integration.' },
    @{ Path = '.temp'; Reason = 'Local reference material and experiment output; preserved without deletion.' },
    @{ Path = 'apps/knowledge-console/build'; Reason = 'Generated duplicate package output; runtime uses src.' },
    @{ Path = 'runners/minecraft-validation/src/minecraft_validation/vision'; Reason = 'Standalone vision tools; no application callers.' },
    @{ Path = 'runners/minecraft-validation/src/minecraft_validation/mineflayer_mcp.py'; Reason = 'Unused legacy MCP wrapper; executor and validator remain active.' },
    @{ Path = 'docs/AUTOMATION_SYSTEM_DESIGN.md'; Reason = 'Historical design with obsolete layout and unimplemented capabilities.' },
    @{ Path = 'docs/README_MINECRAFT.md'; Reason = 'Historical integration instructions with obsolete paths.' },
    @{ Path = 'docs/README_VALIDATION.md'; Reason = 'Historical validation instructions with obsolete paths.' },
    @{ Path = 'docs/README_VISION.md'; Reason = 'Instructions for archived standalone vision tools.' }
)

if (Test-Path -LiteralPath $manifestPath) {
    throw 'This archive already has a manifest. Inspect it before another archive run.'
}

$plans = foreach ($target in $targets) {
    $source = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $target.Path))
    $destination = [IO.Path]::GetFullPath((Join-Path $archiveRoot $target.Path))
    if (-not $source.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar)) {
        throw "Source is outside the workspace: $source"
    }
    if (-not $destination.StartsWith($archiveRoot + [IO.Path]::DirectorySeparatorChar)) {
        throw "Destination is outside the archive: $destination"
    }
    if (-not (Test-Path -LiteralPath $source)) { continue }
    if (Test-Path -LiteralPath $destination) { throw "Destination exists: $destination" }
    $files = @(Get-ChildItem -LiteralPath $source -File -Recurse -Force)
    if (Test-Path -LiteralPath $source -PathType Leaf) { $files = @(Get-Item -LiteralPath $source) }
    [pscustomobject]@{
        source = $target.Path
        destination = '.archive/2026-10-02/' + $target.Path
        reason = $target.Reason
        files = $files.Count
        bytes = ($files | Measure-Object -Property Length -Sum).Sum
        status = 'planned'
    }
}

$plans | Format-Table source, files, bytes -AutoSize
if (-not $Apply) { return }

New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$manifest = [ordered]@{ date = '2026-10-02'; entries = @($plans) }
function Save-Manifest {
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}
Save-Manifest
foreach ($plan in $plans) {
    $destination = Join-Path $workspaceRoot $plan.destination
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    Move-Item -LiteralPath (Join-Path $workspaceRoot $plan.source) -Destination $destination
    $plan.status = 'archived'
    Save-Manifest
}
