# 엑셀 변경분을 data/에 반영 후 GitHub(aum-analysis)에 푸시 → Streamlit Cloud 자동 재배포
param(
    [switch]$Watch,
    [int]$WatchIntervalSec = 300
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$LogDir = Join-Path $Root "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir "sync_deploy.log"

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Host $line
}

function Sync-ExcelToData {
    $dataDir = Join-Path $Root "data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir | Out-Null
    }

    $copied = @()
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
            $copied += $_.Name
        }
    }
    return $copied
}

function Publish-GitHub {
    if (-not (Test-Path (Join-Path $Root ".git"))) {
        throw "Git 저장소가 없습니다. 프로젝트 폴더에서 git init 후 remote를 설정해 주세요."
    }

    $remoteUrl = git remote get-url origin 2>$null
    if (-not $remoteUrl) {
        throw "git remote 'origin'이 없습니다. 예: git remote add origin https://github.com/kriskang02-max/aum-analysis.git"
    }

    $branch = (git branch --show-current).Trim()
    if (-not $branch) {
        $branch = "main"
    }

    git add -A
    $status = git status --porcelain
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-Log "Git 변경 없음 — 푸시 생략"
        return $false
    }

    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $msg = "chore: sync excel data and deploy ($stamp)"
    git commit -m $msg | Out-Host
    git push origin $branch | Out-Host
    Write-Log "GitHub 푸시 완료 ($remoteUrl → $branch)"
    Write-Log "Streamlit Cloud가 연결되어 있으면 1~3분 내 사이트에 반영됩니다."
    return $true
}

function Invoke-SyncDeployOnce {
    Write-Log "=== 동기화·배포 시작 ==="
    $copied = Sync-ExcelToData
    if ($copied.Count -gt 0) {
        Write-Log ("data/ 복사: {0}" -f ($copied -join ", "))
    }
    else {
        Write-Log "루트 엑셀 → data/ 복사할 변경 없음"
    }

    $pushed = Publish-GitHub
    if (-not $pushed -and $copied.Count -eq 0) {
        Write-Log "반영할 변경이 없습니다."
    }
    Write-Log "=== 완료 ==="
}

if ($Watch) {
    Write-Log "감시 모드 시작 (루트/*.xlsx, data/*.xlsx, $WatchIntervalSec 초 간격). 종료: Ctrl+C"
    while ($true) {
        try {
            Invoke-SyncDeployOnce
        }
        catch {
            Write-Log ("오류: {0}" -f $_.Exception.Message)
        }
        Start-Sleep -Seconds $WatchIntervalSec
    }
}
else {
    Invoke-SyncDeployOnce
}
