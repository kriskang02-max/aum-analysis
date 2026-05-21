# 엑셀 변경분을 data/에 반영 후 GitHub(aum-analysis)에 푸시
param(
    [switch]$Watch,
    [int]$WatchIntervalSec = 300
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

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
    Write-Host ""
    Write-Host "---------- 실행 결과 ----------"
    foreach ($line in $script:SessionLog) {
        Write-Host $line
    }
    Write-Host "------------------------------"
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
        throw "git $($GitArgs -join ' ') 실패 (종료 코드 $LASTEXITCODE)"
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
        throw "Git 저장소가 없습니다."
    }

    $remoteUrl = git remote get-url origin 2>$null
    if (-not $remoteUrl) {
        throw "git remote 'origin'이 없습니다."
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
    Write-Log "GitHub 푸시 완료: $remoteUrl (브랜치 $branch)"
    Write-Log "Streamlit Cloud 연결 시 1~3분 내 사이트에 반영됩니다."
    return @{ Pushed = $true; Files = $changed }
}

function Invoke-SyncDeployOnce {
    $script:SessionLog.Clear()
    Write-Log "=== 동기화·배포 시작 ==="

    $copied = Sync-ExcelToData
    if ($copied.Count -gt 0) {
        Write-Log "새로 data/에 반영한 엑셀 ($($copied.Count)개):"
        foreach ($name in $copied) {
            Write-Log "  · $name"
        }
    }
    else {
        Write-Log "새로 반영할 엑셀 없음 (프로젝트 루트 → data/ 변경 없음)"
    }

    $result = Publish-GitHub
    if ($result.Pushed) {
        Write-Log "GitHub에 업로드한 파일 ($($result.Files.Count)개):"
        foreach ($path in $result.Files) {
            Write-Log "  · $path"
        }
    }
    else {
        Write-Log "GitHub에 올릴 새 파일·변경 없음 (푸시 생략)"
    }

    if (-not $result.Pushed -and $copied.Count -eq 0) {
        Write-Log "요약: 업로드할 내용이 없습니다."
    }
    elseif ($result.Pushed) {
        Write-Log "요약: 배포 완료."
    }
    else {
        Write-Log "요약: Git에 반영할 변경이 없습니다."
    }

    Write-Log "=== 완료 ==="
    Show-SessionLog
}

if ($Watch) {
    Write-Log "감시 모드 ($WatchIntervalSec 초). 종료: Ctrl+C"
    Show-SessionLog
    while ($true) {
        try {
            Invoke-SyncDeployOnce
        }
        catch {
            Write-Log ("오류: {0}" -f $_.Exception.Message)
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
        Write-Log ("오류: {0}" -f $_.Exception.Message)
        Show-SessionLog
        exit 1
    }
}
