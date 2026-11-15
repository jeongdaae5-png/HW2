param(
  [string]$BaseUrl = 'http://127.0.0.1:8000',
  [string]$LogPath = 'artifacts\monitor.jsonl',
  [int]$DurationSeconds = 90
)
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dir = Split-Path -Parent $LogPath
if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($LogPath, $false, $utf8NoBom)
$writer.AutoFlush = $true
$fixture = Join-Path $env:TEMP 'tonepick-fixed-test.ppm'
$header = [Text.Encoding]::ASCII.GetBytes("P6`n80 80`n255`n")
$body = New-Object byte[] (80 * 80 * 3)
for ($i = 0; $i -lt $body.Length; $i += 3) { $body[$i] = 196; $body[$i+1] = 145; $body[$i+2] = 125 }
[IO.File]::WriteAllBytes($fixture, $header + $body)
$started = [DateTimeOffset]::UtcNow
while (([DateTimeOffset]::UtcNow - $started).TotalSeconds -lt $DurationSeconds) {
  $start = [DateTimeOffset]::UtcNow
  $status = 0; $analysis = $false; $version = 'unavailable'; $errorText = ''
  try {
    $result = & curl.exe -sS --max-time 8 -w "`n%{http_code}" -F "file=@$fixture;type=image/x-portable-pixmap" "$BaseUrl/api/analyze" 2>&1
    $lines = @($result); $status = [int]$lines[-1]; $json = ($lines[0..($lines.Count-2)] -join "`n")
    if ($status -eq 200) { $obj = $json | ConvertFrom-Json; $analysis = [bool]$obj.type; $version = [string]$obj.model_version }
  } catch { $errorText = $_.Exception.Message }
  $end = [DateTimeOffset]::UtcNow
  $record = [PSCustomObject]@{ start=$start.ToString('o'); end=$end.ToString('o'); response_ms=[math]::Round(($end-$start).TotalMilliseconds, 1); status=$status; analysis_ok=$analysis; version=$version; error=$errorText } | ConvertTo-Json -Compress
  $writer.WriteLine($record)
  Start-Sleep -Seconds 1
}
$writer.Dispose()
Remove-Item -Force $fixture -ErrorAction SilentlyContinue
