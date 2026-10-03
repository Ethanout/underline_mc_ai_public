param([switch]$Apply, [switch]$Knowledge)

$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent))
$archiveRoot = Join-Path $workspaceRoot '.archive/2026-10-02/legacy-stack'
$phase = if ($Knowledge) { 'knowledge' } else { 'runtime' }
$manifestPath = Join-Path $archiveRoot "manifest-$phase.json"
$movePaths = if ($Knowledge) { @('knowledge') } else {
    @('apps/knowledge-console', 'packages', 'jobs', 'runners', 'docs',
      'external', 'legacy', 'assets', 'config/crawlers', 'runtime/rag',
      'runtime/sources', 'runtime/temp', 'runtime/validation',
      'runtime/private/wheels', 'tests/test_architecture.py',
      'tests/test_console_public.py', 'tests/test_knowledge_contract.py')
}
$copyPaths = if ($Knowledge) { @() } else {
    @('README.md', 'TODO.md', '_PROJECT_REALITY.md', 'app.py',
      'workspace_bootstrap.py', 'pyproject.toml', 'start_ui.bat',
      '.env.example', 'opencode.json', 'runtime/README.md')
}
if (Test-Path -LiteralPath $manifestPath) { throw "Manifest already exists: $manifestPath" }

$plans = @()
foreach ($operation in @('move', 'copy')) {
    $paths = if ($operation -eq 'move') { $movePaths } else { $copyPaths }
    foreach ($relative in $paths) {
        $source = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $relative))
        $target = [IO.Path]::GetFullPath((Join-Path $archiveRoot $relative))
        if (-not $source.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar) -or
            -not $target.StartsWith($archiveRoot + [IO.Path]::DirectorySeparatorChar)) {
            throw "Path outside archive boundary: $relative"
        }
        if (-not (Test-Path -LiteralPath $source)) { continue }
        if (Test-Path -LiteralPath $target) { throw "Archive target exists: $relative" }
        $files = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
        if (Test-Path -LiteralPath $source -PathType Leaf) { $files = @(Get-Item -LiteralPath $source) }
        $inventory = @($files | ForEach-Object {
            [pscustomobject]@{
                path = $_.FullName.Substring($workspaceRoot.Length + 1).Replace('\', '/')
                bytes = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            }
        })
        $plans += [pscustomobject]@{
            source = $relative
            destination = '.archive/2026-10-02/legacy-stack/' + $relative
            operation = $operation
            status = 'planned'
            files = $inventory
        }
    }
}
$plans | Select-Object source, operation, @{Name='files'; Expression={$_.files.Count}} | Format-Table
if (-not $Apply) { return }
New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$manifest = [ordered]@{ date = '2026-10-02'; phase = $phase; entries = $plans }
function Save-Manifest {
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}
Save-Manifest
foreach ($plan in $plans) {
    $target = Join-Path $workspaceRoot $plan.destination
    New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
    $source = Join-Path $workspaceRoot $plan.source
    if ($plan.operation -eq 'move') { Move-Item -LiteralPath $source -Destination $target }
    else { Copy-Item -LiteralPath $source -Destination $target -Recurse }
    $plan.status = 'archived'
    Save-Manifest
}
