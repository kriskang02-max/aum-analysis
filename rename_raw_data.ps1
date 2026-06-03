param(
    [string]$Date = ""
)

# FREESIS download -> gongmo/samo/ilim_YYMMDD.xlsx

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ""
Write-Host "=== Raw data 파일명 변경 ===" -ForegroundColor Cyan
Write-Host "폴더: $Root"
Write-Host ""
Write-Host "원본 파일 (이 폴더에 두세요):"
Write-Host "  회사별설정규모      -> 공모_YYMMDD.xlsx"
Write-Host "  회사별설정규모 (1)  -> 사모_YYMMDD.xlsx"
Write-Host "  회사별설정규모 (2)  -> 일임_YYMMDD.xlsx"
Write-Host ""

$dateInput = if ($Date) { $Date.Trim() } else { Read-Host "기준일 입력 (YYMMDD, 예: 260522)" }
$dateInput = ($dateInput -replace "\s", "")

if ($dateInput -notmatch "^\d{6}$") {
    Write-Host "날짜 형식 오류: 6자리 숫자(YYMMDD)로 입력하세요." -ForegroundColor Red
    exit 1
}

$mm = [int]$dateInput.Substring(2, 2)
$dd = [int]$dateInput.Substring(4, 2)
if ($mm -lt 1 -or $mm -gt 12 -or $dd -lt 1 -or $dd -gt 31) {
    Write-Host "날짜 값이 올바르지 않습니다." -ForegroundColor Red
    exit 1
}

$Mappings = @(
    @{ SourceBase = "회사별설정규모";      Target = "공모_$dateInput.xlsx" },
    @{ SourceBase = "회사별설정규모 (1)";  Target = "사모_$dateInput.xlsx" },
    @{ SourceBase = "회사별설정규모 (2)";  Target = "일임_$dateInput.xlsx" }
)

$Extensions = @(".xlsx", ".xls", ".xlsm")

function Find-SourceFile {
    param([string]$BaseName)
    foreach ($ext in $Extensions) {
        $path = Join-Path $Root ($BaseName + $ext)
        if (Test-Path -LiteralPath $path) {
            return $path
        }
    }
    return $null
}

$ok = 0
$fail = 0

foreach ($map in $Mappings) {
    $src = Find-SourceFile -BaseName $map.SourceBase
    $dst = Join-Path $Root $map.Target

    if (-not $src) {
        Write-Host "[건너뜀] 파일 없음: $($map.SourceBase)" -ForegroundColor Yellow
        $fail++
        continue
    }

    if (Test-Path -LiteralPath $dst) {
        $ans = Read-Host "대상 파일이 이미 있습니다: $($map.Target). 덮어쓸까요? (Y/N)"
        if ($ans -notmatch "^[Yy]") {
            Write-Host "[건너뜀] $($map.Target)" -ForegroundColor Yellow
            continue
        }
        Remove-Item -LiteralPath $dst -Force
    }

    Rename-Item -LiteralPath $src -NewName $map.Target
    Write-Host "[완료] $(Split-Path -Leaf $src) -> $($map.Target)" -ForegroundColor Green
    $ok++
}

Write-Host ""
if ($ok -eq 0) {
    Write-Host "변경된 파일이 없습니다. 다운로드 파일을 이 폴더에 넣고 다시 실행하세요." -ForegroundColor Red
    exit 1
}

Write-Host "완료: $ok 개 파일 이름 변경"
if ($fail -gt 0) {
    Write-Host "찾지 못한 원본: $fail 개" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "다음 단계: sync_deploy.bat 실행 -> data/ 복사 및 배포" -ForegroundColor Cyan
exit 0
