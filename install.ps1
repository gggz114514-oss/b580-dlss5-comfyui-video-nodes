param([string]$AssetDirectory = '')
$ErrorActionPreference = 'Stop'
# Avoid optional PowerShell modules: a parent pwsh/Comfy environment can pass a
# PSModulePath which excludes Windows PowerShell's modules.
$env:PSModulePath = Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Get-ArchiveSha256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant()
    } finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}
$nodeRoot = $PSScriptRoot
$manifestPath = Join-Path $nodeRoot 'release-assets.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw 'This checkout has no tested runtime release yet. Do not treat a source-only snapshot as a complete package.'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$runtimeRoot = Join-Path $nodeRoot '.runtime'
if (Test-Path -LiteralPath $runtimeRoot) {
    throw 'An existing .runtime directory is present. Keep it intact; install a newer release in a separate node folder.'
}
$stagingRoot = Join-Path $nodeRoot ('.runtime-staging-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stagingRoot | Out-Null
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
foreach ($asset in $manifest.assets) {
    $uri = [uri]$asset.url
    if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'github.com') { throw 'Unexpected runtime asset host' }
    if ([IO.Path]::GetFileName($asset.name) -ne $asset.name) { throw 'Invalid asset filename' }
    $archive = Join-Path $stagingRoot $asset.name
    $pieces = @($asset)
    if ($asset.parts) { $pieces = @($asset.parts) }
    $joined = [IO.File]::Create($archive)
    try {
        foreach ($piece in $pieces) {
            $pieceUri = [uri]$piece.url
            if ($pieceUri.Scheme -ne 'https' -or $pieceUri.Host -ne 'github.com' -or
                [IO.Path]::GetFileName($piece.name) -ne $piece.name) { throw 'Invalid runtime part' }
            $partPath = Join-Path $stagingRoot ($piece.name + '.download')
            if ($AssetDirectory) {
                Write-Host ('Using local part ' + $piece.name)
                Copy-Item -LiteralPath (Join-Path $AssetDirectory $piece.name) -Destination $partPath
            } else {
                Write-Host ('Downloading ' + $piece.name)
                Invoke-WebRequest -Uri $piece.url -OutFile $partPath -UseBasicParsing
            }
            if ((Get-ArchiveSha256 $partPath) -ne $piece.sha256) { throw ('Part checksum mismatch: ' + $piece.name) }
            $partStream = [IO.File]::OpenRead($partPath)
            try { $partStream.CopyTo($joined) } finally { $partStream.Dispose() }
            Remove-Item -LiteralPath $partPath
        }
    } finally { $joined.Dispose() }
    if ((Get-ArchiveSha256 $archive) -ne $asset.sha256) {
        throw ('Runtime archive checksum mismatch: ' + $asset.name)
    }
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $stagingRoot)
    Remove-Item -LiteralPath $archive
}
$python = Join-Path $stagingRoot 'python/python.exe'
& $python -B -X utf8 (Join-Path $stagingRoot 'setup_runtime.py')
if ($LASTEXITCODE -ne 0) { throw 'NR model/runtime preparation failed; logs above. Staging files retained.' }
# Final path is chosen only after successful extraction and model verification.
$resolvedNodeRoot = [IO.Path]::GetFullPath($nodeRoot).TrimEnd('\')
$resolvedStagingRoot = (Resolve-Path -LiteralPath $stagingRoot).Path
$resolvedRuntimeRoot = [IO.Path]::GetFullPath($runtimeRoot)
if ([IO.Path]::GetDirectoryName($resolvedStagingRoot) -ne $resolvedNodeRoot -or
    [IO.Path]::GetDirectoryName($resolvedRuntimeRoot) -ne $resolvedNodeRoot -or
    [IO.Path]::GetFileName($resolvedStagingRoot) -notlike '.runtime-staging-*' -or
    [IO.Path]::GetFileName($resolvedRuntimeRoot) -ne '.runtime') {
    throw 'Runtime move target is outside the node directory'
}
Move-Item -LiteralPath $stagingRoot -Destination $runtimeRoot
& (Join-Path $runtimeRoot 'python/python.exe') -B -X utf8 (Join-Path $runtimeRoot 'relocate.py')
if ($LASTEXITCODE -ne 0) { throw 'NR final path preparation failed' }
Write-Host 'NR runtime installed. Restart ComfyUI.'
