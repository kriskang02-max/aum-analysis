# Excel sync -> data/ -> git push (Streamlit Cloud)
param(
    [switch]$Watch,
    [int]$WatchIntervalSec = 300
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$KoFile = Join-Path $Root "sync_deploy.ko.ps1"
if (-not (Test-Path $KoFile)) {
    throw "Missing sync_deploy.ko.ps1"
}
. $KoFile
$M = $script:AumDeployMsg

try {
    chcp 65001 | Out-Null
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

$LogDir = Join-Path $Root "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "sync_deploy.log"
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
$script:SessionLog = New-Object System.Collections.Generic.List[string]

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    [System.IO.File]::AppendAllText($LogFile, $line + [Environment]::NewLine, $Utf8NoBom)
    $script:SessionLog.Add($line)
}

function Show-SessionLog {
    $n = [Math]::Max($script:SessionLog.Count, 1)
    Write-Host ""
    Write-Host $M.ResultHdr
    if (Test-Path $LogFile) {
        Get-Content -LiteralPath $LogFile -Encoding UTF8 -Tail ($n + 1) | ForEach-Object {
            [Console]::Out.WriteLine($_)
        }
    }
    Write-Host $M.ResultFoot
    Write-Host $M.LogPath
}

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & git @GitArgs 2>&1
    $ErrorActionPreference = $prev
    if ($null -ne $output) {
        foreach ($o in @($output)) {
            if ("$o".Trim()) {
                Write-Host $o
            }
        }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "git failed: $($GitArgs -join ' ') (exit $LASTEXITCODE)"
    }
}

function Sync-ExcelToData {
    $dataDir = Join-Path $Root "data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir | Out-Null
    }

    $copied = [System.Collections.Generic.List[string]]::new()
    Get-ChildItem -Path $Root -Filter "*.xlsx" -File | ForEach-Object {
        $dest = Join-Path $dataDir $_.Name
        $needsCopy = $false
        if (-not (Test-Path $dest)) {
            $needsCopy = $true
        }
        else {
            $srcItem = Get-Item $_.FullName
            $dstItem = Get-Item $dest
            if (
                $dstItem.LastWriteTimeUtc -lt $srcItem.LastWriteTimeUtc -or
                $dstItem.Length -ne $srcItem.Length
            ) {
                $needsCopy = $true
            }
        }
        if ($needsCopy) {
            Copy-Item $_.FullName $dest -Force
            $copied.Add($_.Name)
        }
    }
    return $copied
}

function Get-GitChangedFiles {
    $lines = @(git status --porcelain 2>$null)
    if ($lines.Count -eq 0) {
        return @()
    }
    $files = [System.Collections.Generic.List[string]]::new()
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.Length -lt 4) {
            continue
        }
        $path = $line.Substring(3).Trim()
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Substring(1, $path.Length - 2)
        }
        $files.Add($path)
    }
    return $files
}

function Publish-GitHub {
    if (-not (Test-Path (Join-Path $Root ".git"))) {
        throw "Not a git repository."
    }

    $remoteUrl = git remote get-url origin 2>$null
    if (-not $remoteUrl) {
        throw "git remote 'origin' not configured."
    }

    $branch = (git branch --show-current 2>$null)
    if ([string]::IsNullOrWhiteSpace($branch)) {
        $branch = "main"
    }
    else {
        $branch = $branch.Trim()
    }

    Invoke-Git add -A
    $changed = Get-GitChangedFiles
    if ($changed.Count -eq 0) {
        return @{ Pushed = $false; Files = @() }
    }

    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $msg = "chore: sync excel data and deploy ($stamp)"
    Invoke-Git commit -m $msg
    Invoke-Git push origin $branch
    Write-Log ($M.PushDone -f $remoteUrl, $branch)
    Write-Log $M.Streamlit
    return @{ Pushed = $true; Files = $changed }
}

function Invoke-SyncDeployOnce {
    $script:SessionLog.Clear()
    Write-Log $M.Start

    $copied = Sync-ExcelToData
    if ($copied.Count -gt 0) {
        Write-Log ($M.ExcelNew -f $copied.Count)
        foreach ($name in $copied) {
            Write-Log "  - $name"
        }
    }
    else {
        Write-Log $M.NoExcel
    }

    $result = Publish-GitHub
    if ($result.Pushed) {
        Write-Log ($M.GitUpload -f $result.Files.Count)
        foreach ($path in $result.Files) {
            Write-Log "  - $path"
        }
    }
    else {
        Write-Log $M.NoGit
    }

    if (-not $result.Pushed -and $copied.Count -eq 0) {
        Write-Log $M.SummaryNone
    }
    elseif ($result.Pushed) {
        Write-Log $M.SummaryDone
    }
    else {
        Write-Log $M.SummaryGit
    }

    Write-Log $M.Done
    Show-SessionLog
}

if ($Watch) {
    Write-Log "Watch mode ($WatchIntervalSec sec). Ctrl+C to stop."
    Show-SessionLog
    while ($true) {
        try {
            Invoke-SyncDeployOnce
        }
        catch {
            Write-Log ("Error: {0}" -f $_.Exception.Message)
            Show-SessionLog
        }
        Start-Sleep -Seconds $WatchIntervalSec
    }
}
else {
    try {
        Invoke-SyncDeployOnce
    }
    catch {
        Write-Log ("Error: {0}" -f $_.Exception.Message)
        Show-SessionLog
        exit 1
    }
}
