<#
.SYNOPSIS
  Offline demonstration in three short stages, each with its own transcript.

.DESCRIPTION
  Turn Wi-Fi / Ethernet OFF yourself first (this script never changes network settings), then run the stages one after another:

    powershell -ExecutionPolicy Bypass -File demo\offline-demo.ps1 -Stage 1    # ingest a source + search           (~3 min)
    powershell -ExecutionPolicy Bypass -File demo\offline-demo.ps1 -Stage 2    # the four ask-mode tests            (~10 min)
    powershell -ExecutionPolicy Bypass -File demo\offline-demo.ps1 -Stage 3    # chat + search + boundary checks    (~10 min)

  Every stage first proves the machine is offline (it must FAIL to reach the internet), restarts the local model server and the CLI, and
  writes a redacted transcript to evidence\offline-demo\. Stages are separate so that an interruption only loses the stage that was running.
  Use -AllowOnline only to rehearse; a rehearsal transcript is not offline evidence.
#>
param(
    [Parameter(Mandatory = $true)][ValidateSet(1, 2, 3)][int]$Stage,
    [switch]$AllowOnline
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
$wiki = Join-Path $root ".venv\Scripts\wiki.exe"
$python = Join-Path $root ".venv\Scripts\python.exe"
$ollama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
$env:PYTHONIOENCODING = "utf-8"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $root "evidence\offline-demo"
New-Item -ItemType Directory -Force $outDir | Out-Null
$transcript = Join-Path $outDir "stage$Stage-$stamp.txt"
Start-Transcript -Path $transcript | Out-Null

function Step($title) { Write-Host ""; Write-Host "=== $title ===" -ForegroundColor Cyan }

Step "Stage ${Stage}: device and time"
Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$os = Get-CimInstance Win32_OperatingSystem
"OS: $($os.Caption) $($os.Version) | CPU: $((Get-CimInstance Win32_Processor).Name) | RAM: {0:N1} GB total, {1:N1} GB free" -f ($os.TotalVisibleMemorySize/1MB), ($os.FreePhysicalMemory/1MB)

Step "Proof that the internet is disconnected (these checks must FAIL)"
$online = $false
try { $r = Test-NetConnection -ComputerName 1.1.1.1 -Port 443 -WarningAction SilentlyContinue; if ($r.TcpTestSucceeded) { $online = $true }; "TCP 1.1.1.1:443 reachable: $($r.TcpTestSucceeded)" } catch { "TCP 1.1.1.1:443: error ($($_.Exception.Message))" }
try { $d = Resolve-DnsName example.com -ErrorAction Stop; $online = $true; "DNS example.com resolved: $($d[0].IPAddress)" } catch { "DNS example.com: could not resolve (offline)" }
try { $null = Invoke-WebRequest -Uri "https://example.com" -TimeoutSec 5 -UseBasicParsing; $online = $true; "HTTPS example.com: reachable" } catch { "HTTPS example.com: unreachable (offline)" }
if ($online -and -not $AllowOnline) {
    Write-Host "The internet is still reachable. Disconnect Wi-Fi/Ethernet and run this stage again." -ForegroundColor Red
    Stop-Transcript | Out-Null
    Remove-Item $transcript -ErrorAction SilentlyContinue
    exit 2
}
if ($online) { Write-Host "REHEARSAL: still online, so this transcript is NOT offline evidence." -ForegroundColor Yellow } else { Write-Host "OFFLINE CONFIRMED" -ForegroundColor Green }

Step "Restart the local model server and the CLI"
Get-Process -Name "ollama*", "llama-server" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process -FilePath $ollama -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 6
& $ollama list
& $wiki --version

if ($Stage -eq 1) {
    Step "wiki --help"
    & $wiki --help

    Step "Ingest a source (in a scratch copy of the project, so the real wiki is untouched)"
    $scratch = Join-Path $env:TEMP "wiki-offline-demo-$stamp"
    New-Item -ItemType Directory -Force (Join-Path $scratch "vault\raw") | Out-Null
    Copy-Item -Recurse (Join-Path $root "prompts") (Join-Path $scratch "prompts")
    Copy-Item (Join-Path $root "vault\raw\Sunk Cost Reasoning.docx") (Join-Path $scratch "vault\raw\")
    $plan = "[[source]]`nfile = `"Sunk Cost Reasoning.docx`"`ndescription = `"Example in the Wild 1`"`norigin = `"My own Word document`"`n`n" +
            "[[concept]]`ntitle = `"Sunk Costs`"`ntopic = `"Economics`"`nquery = `"sunk cost past investment`"`nsources = [`"Sunk Cost Reasoning.docx`"]`nlimit = 4`n"
    [IO.File]::WriteAllText((Join-Path $scratch "wiki-plan.toml"), $plan, (New-Object System.Text.UTF8Encoding($false)))  # no BOM
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $wiki --root $scratch ingest | Out-Host
    "ingest wall time: {0:N1} s" -f $sw.Elapsed.TotalSeconds
    Get-Content (Join-Path $scratch "vault\wiki\Economics\Sunk Costs.md")
    "--- ingest again: nothing should be rewritten ---"
    & $wiki --root $scratch ingest | Out-Host
    Remove-Item -Recurse -Force $scratch

    Step "Search (no model)"
    & $wiki search "price discrimination group pricing" --limit 3 | Out-Host
}

if ($Stage -eq 2) {
    Step "The four ask-mode tests (cards saved under evidence\ask-tests\offline-$stamp)"
    & $python (Join-Path $root "evals\run_evals.py") --label "offline-$stamp" | Out-Host
}

if ($Stage -eq 3) {
    Step "Chat, search and boundary checks (saved under evidence\mode-checks\offline-$stamp)"
    & $python (Join-Path $root "evals\run_mode_checks.py") --label "offline-$stamp" | Out-Host

    Step "A short scripted chat through the real CLI"
    & $wiki chat --script (Join-Path $root "demo\chat-script.txt") | Out-Host

    Step "Memory in use by the model"
    & $ollama ps
    Get-Process llama-server -ErrorAction SilentlyContinue | Select-Object ProcessName, @{n="WorkingSetGB";e={[math]::Round($_.WorkingSet64/1GB,2)}}, @{n="PrivateGB";e={[math]::Round($_.PrivateMemorySize64/1GB,2)}}
    "Available RAM (GB): {0:N2}" -f ((Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue / 1024)
}

Write-Host ""
Write-Host "Stage $Stage done. Transcript: $transcript" -ForegroundColor Green
Stop-Transcript | Out-Null

# The transcript header records the Windows user name and computer name: redact them before this file is shared.
$text = Get-Content $transcript -Raw
foreach ($pair in @(@($env:USERPROFILE, "<USERPROFILE>"), @($env:USERNAME, "<user>"), @($env:COMPUTERNAME, "<computer>"))) {
    if ($pair[0]) { $text = $text.Replace($pair[0], $pair[1]) }
}
Set-Content -Path $transcript -Value $text -Encoding utf8
