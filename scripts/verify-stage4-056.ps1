param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$BaseUrl = 'http://localhost:8000',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$manifestPath = Join-Path $PSScriptRoot 'stage4-manifest.json'
$requestPath = Join-Path $PSScriptRoot '04.en.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    $manifestPath = Join-Path $PSScriptRoot '..\examples\quality\stage4-056-manifest.json'
    $requestPath = Join-Path $PSScriptRoot '..\tests\fixtures\stage04.en.json'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.application_version -ne '0.5.6' -or $manifest.diagnostic_version -ne 'provider-output-4') {
    throw 'Unexpected verification package. No inference started.'
}
$scriptPath = Join-Path $PSScriptRoot 'diagnose_provider_output_v4.py'
foreach ($pair in @(
    @{ Path = $scriptPath; Hash = $manifest.diagnostic_sha256 },
    @{ Path = $requestPath; Hash = $manifest.request_sha256 }
)) {
    if ((Get-FileHash -LiteralPath $pair.Path -Algorithm SHA256).Hash -ne $pair.Hash) {
        throw "File hash mismatch: $($pair.Path). No inference started."
    }
}
Push-Location -LiteralPath $RepoPath
try {
    if (-not (Test-Path -LiteralPath '.\compose.yaml' -PathType Leaf)) {
        throw 'Run from the sana-alignment repository or set -RepoPath.'
    }
    $version = (Invoke-RestMethod -Uri ($BaseUrl.TrimEnd('/') + '/openapi.json') -TimeoutSec 10).info.version
    if ($version -ne '0.5.6') { throw "Expected app 0.5.6, received $version. No inference started." }
    Write-Host 'App: 0.5.6; diagnostic: provider-output-4; stage: 4; input hashes verified.'
    if ($CheckOnly) { return }
    $runId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
    $runDir = Join-Path $PSScriptRoot (Join-Path 'results' $runId)
    New-Item -ItemType Directory -Path $runDir | Out-Null
    Copy-Item -LiteralPath $requestPath -Destination (Join-Path $runDir '04.request.json')
    $packet = @{
        script = [Convert]::ToBase64String([IO.File]::ReadAllBytes($scriptPath))
        request = [Convert]::ToBase64String([IO.File]::ReadAllBytes($requestPath))
        diagnostic_sha256 = $manifest.diagnostic_sha256
        request_sha256 = $manifest.request_sha256
    } | ConvertTo-Json -Compress
    $runner056 = @'
import asyncio,base64,hashlib,json,sys
import httpx
packet=json.load(sys.stdin)
script=base64.b64decode(packet['script'])
request_bytes=base64.b64decode(packet['request'])
if hashlib.sha256(script).hexdigest()!=packet['diagnostic_sha256'] or hashlib.sha256(request_bytes).hexdigest()!=packet['request_sha256']:
    raise SystemExit('Input hash mismatch; no inference started.')
scope={'__name__':'provider_diagnostic'}
exec(compile(script,'diagnose_provider_output_v4.py','exec'),scope)
async def run():
    request=scope['AlignRequest'].model_validate_json(request_bytes.decode('utf-8-sig'))
    settings=scope['Settings'].from_env()
    async with httpx.AsyncClient(follow_redirects=False) as client:
        report=await scope['diagnose'](request,scope['Provider'](settings,client),settings.timeout)
    report['verification_inputs']={k:packet[k] for k in ('diagnostic_sha256','request_sha256')}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['outcome']=='success' else 2
sys.exit(asyncio.run(run()))
'@
    $previousEncoding = [Console]::OutputEncoding
    try {
        [Console]::OutputEncoding = $utf8
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $output = @($packet | docker compose exec -T -w /app sana python -c $runner056)
        $dockerExit = $LASTEXITCODE
        $watch.Stop()
    } finally {
        [Console]::OutputEncoding = $previousEncoding
    }
    $reportPath = Join-Path $runDir '04.diagnostic.json'
    [IO.File]::WriteAllText($reportPath, ($output -join "`n"), $utf8)
    Write-Host "Report: $reportPath"
    Write-Host "docker_exit=$dockerExit elapsed_seconds=$([math]::Round($watch.Elapsed.TotalSeconds,3))"
    if ($dockerExit -ne 0) {
        Write-Warning 'Diagnostic returned an error. Share the saved report before another inference.'
        return
    }
    $report = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host "outcome=$($report.outcome) status=$($report.result.status)"
} finally {
    Pop-Location
}
