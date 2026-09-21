param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$BaseUrl = 'http://localhost:8000',
    [ValidateSet('low','medium','high')][string]$Mode = 'low',
    [string]$ApiToken = $env:SANA_API_TOKEN,
    [switch]$Greeting,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$sourcePath = Join-Path $PSScriptRoot '04.en.json'
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    $sourcePath = Join-Path $PSScriptRoot '..\tests\fixtures\stage04.en.json'
}
$sourceHash = 'feb95a60f6cf826f2a10576cd7d3f27dbe4ef101a3d67641a2e692f55d9f2b42'
if (-not $Greeting -and (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne $sourceHash) {
    throw 'Stage-4 input mismatch. No inference started.'
}
Push-Location -LiteralPath $RepoPath
try {
    if (-not (Test-Path -LiteralPath '.\compose.yaml' -PathType Leaf)) {
        throw 'Set -RepoPath to the sana-alignment repository.'
    }
    $version = (Invoke-RestMethod -Uri ($BaseUrl.TrimEnd('/') + '/openapi.json') -TimeoutSec 10).info.version
    if ($version -ne '0.5.14') { throw "Expected app 0.5.14, received $version. No inference started." }
    Write-Host "App: $version; processing_mode=$Mode; normal HTTP endpoint; one request."
    if ($CheckOnly) { return }
    $runId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
    $runDir = Join-Path $PSScriptRoot (Join-Path 'results' $runId)
    New-Item -ItemType Directory -Path $runDir | Out-Null
    if ($Greeting) {
        $request = [pscustomobject]@{ input_message = 'Hello'; language = 'en' }
    } else {
        $request = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    $request | Add-Member -NotePropertyName processing_mode -NotePropertyValue $Mode -Force
    $requestPath = Join-Path $runDir 'request.json'
    $responsePath = Join-Path $runDir 'response.json'
    $headersPath = Join-Path $runDir 'headers.txt'
    [IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 40), $utf8)
    $curlArgs = @('--silent','--show-error','--connect-timeout','5','--max-time','620',
        ($BaseUrl.TrimEnd('/') + '/v1/align'), '-H','Content-Type: application/json',
        '--data-binary',"@$requestPath",'--dump-header',$headersPath,'--output',$responsePath,
        '--write-out','%{http_code}')
    if ($ApiToken) { $curlArgs += @('-H', ('Authorization: Bearer ' + $ApiToken)) }
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $httpStatus = (& curl.exe @curlArgs) -join ''
    $curlExit = $LASTEXITCODE
    $watch.Stop()
    $headers = if (Test-Path -LiteralPath $headersPath) { Get-Content -LiteralPath $headersPath -Raw } else { '' }
    $requestId = $null
    $traceStatus = $null
    if ($headers -match '(?im)^x-sana-request-id:\s*([0-9a-f-]{36})\s*$') { $requestId = $Matches[1] }
    if ($headers -match '(?im)^x-sana-trace-status:\s*(\S+)\s*$') { $traceStatus = $Matches[1] }
    $response = $null
    try { $response = Get-Content -LiteralPath $responsePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
    $summary = [ordered]@{
        application_version = $version; processing_mode = $Mode
        source_sha256 = $(if ($Greeting) { $null } else { $sourceHash })
        sent_request_sha256 = (Get-FileHash -LiteralPath $requestPath -Algorithm SHA256).Hash.ToLower()
        http_status = $httpStatus; curl_exit = $curlExit
        elapsed_seconds = [math]::Round($watch.Elapsed.TotalSeconds,3)
        request_id = $requestId; trace_status = $traceStatus
        status = $response.status; error = $response.detail
        server_trace_copied = $false
    }
    if ($requestId -and $traceStatus -in @('saved','saved_with_omissions')) {
        # Request ID is validated before path construction; never inject it into Python source.
        $traceReader = @'
import json,sys,uuid
from pathlib import Path
from app.provider import Settings
packet=json.load(sys.stdin)
request_id=str(uuid.UUID(packet['request_id']))
p=Path(Settings.from_env().trace_dir)/('trace-'+request_id+'.json')
record=json.loads(p.read_text(encoding='utf-8'))
if record.get('request_id')!=request_id:
    raise SystemExit('Trace ID mismatch')
print(json.dumps(record,ensure_ascii=False,indent=2))
'@
        $packet = @{ request_id = $requestId } | ConvertTo-Json -Compress
        $previousEncoding = [Console]::OutputEncoding
        try {
            [Console]::OutputEncoding = $utf8
            $traceOutput = @($packet | docker compose exec -T -w /app sana python -c $traceReader)
            $traceExit = $LASTEXITCODE
        } finally {
            [Console]::OutputEncoding = $previousEncoding
        }
        if ($traceExit -eq 0) {
            [IO.File]::WriteAllText((Join-Path $runDir 'trace.json'), ($traceOutput -join "`n"), $utf8)
            $summary.server_trace_copied = $true
        } else { Write-Warning 'Server trace could not be copied. The API request will not be repeated.' }
    }
    [IO.File]::WriteAllText((Join-Path $runDir 'summary.json'), ($summary | ConvertTo-Json -Depth 20), $utf8)
    Write-Host "Saved: $runDir"
    $summary | ConvertTo-Json -Depth 20
    if ($curlExit -ne 0 -or $httpStatus -ne '200') {
        Write-Warning 'One HTTP attempt completed with an error. Inspect response.json and trace.json; no automatic rerun.'
    }
} finally {
    Pop-Location
}
