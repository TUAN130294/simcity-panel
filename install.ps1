# =====================================================================
#  SimCity Control Panel - bo cai dat 1 lenh
#
#  Cach dung: mo PowerShell roi dan dong duoi day:
#    irm https://raw.githubusercontent.com/TUAN130294/simcity-panel/main/install.ps1 | iex
#
#  Script nay: cai Python (neu thieu) -> tai panel -> tao shortcut Desktop -> mo len.
#  Chay lai lenh tren = cap nhat ban moi (giu nguyen cai dat cu).
#  (Thong bao khong dau tieng Viet de khong bi vo chu tren cua so lenh cu.)
# =====================================================================
$ErrorActionPreference = 'Stop'

$RepoUser = 'TUAN130294'
$RepoName = 'simcity-panel'
$Branch   = 'main'
$Dest     = Join-Path $env:LOCALAPPDATA 'SimCityPanel'
$ZipUrl   = "https://github.com/$RepoUser/$RepoName/archive/refs/heads/$Branch.zip"

function Say($msg, $color = 'Gray') { Write-Host "  $msg" -ForegroundColor $color }
Write-Host ""
Write-Host "  ===== SimCity Control Panel - Cai dat =====" -ForegroundColor Yellow
Write-Host ""

# ---------- 1. Tim Python, thieu thi cai bang winget ----------
function Find-Python {
    foreach ($cmd in @('py', 'python')) {
        $exe = (Get-Command $cmd -ErrorAction SilentlyContinue)
        if ($exe) {
            try {
                $ver = & $exe.Source -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null
                # Windows co 'python' gia (App Execution Alias) -> tra chuoi rong
                if ($ver -match '^3\.(9|1[0-9])') { return $exe.Source }
            } catch {}
        }
    }
    $found = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
             Sort-Object FullName -Descending | Select-Object -First 1
    if ($found) { return $found.FullName }
    $found = Get-ChildItem "C:\Python3*\python.exe" -ErrorAction SilentlyContinue |
             Sort-Object FullName -Descending | Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

$Py = Find-Python
if (-not $Py) {
    Say "Chua co Python. Dang cai tu dong (mat 1-2 phut)..." 'Yellow'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Say "May khong co 'winget' de cai tu dong." 'Red'
        Say "Hay cai Python thu cong tai https://www.python.org/downloads/ (nho tick 'Add to PATH') roi chay lai lenh nay." 'Red'
        return
    }
    winget install -e --id Python.Python.3.12 --scope user --silent `
        --accept-package-agreements --accept-source-agreements | Out-Null
    $Py = Find-Python
    if (-not $Py) {
        Say "Cai Python xong nhung chua tim thay. Hay DONG cua so nay, mo lai PowerShell va chay lai lenh cai dat." 'Red'
        return
    }
}
Say "Python: $Py" 'Green'

# ---------- 2. Tai panel ve ----------
Say "Dang tai panel tu GitHub..."
$tmpZip = Join-Path $env:TEMP "simcity-panel-$(Get-Random).zip"
$tmpDir = Join-Path $env:TEMP "simcity-panel-$(Get-Random)"
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $ZipUrl -OutFile $tmpZip -UseBasicParsing
} catch {
    Say "Khong tai duoc. Kiem tra mang, hoac repo chua duoc cong khai." 'Red'
    Say "URL: $ZipUrl" 'Red'
    return
}
Expand-Archive -Path $tmpZip -DestinationPath $tmpDir -Force
$src = (Get-ChildItem $tmpDir -Directory | Select-Object -First 1).FullName

# Giu lai cai dat cu khi cap nhat (settings.json chua IP/mat khau VM cua nguoi dung)
$oldSettings = Join-Path $Dest 'settings.json'
$keep = $null
if (Test-Path $oldSettings) {
    $keep = Get-Content $oldSettings -Raw -Encoding UTF8
    Say "Giu lai cai dat ket noi cu." 'Green'
}

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item "$src\*" $Dest -Recurse -Force
if ($keep) { Set-Content -Path $oldSettings -Value $keep -Encoding UTF8 -NoNewline }
Remove-Item $tmpZip, $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
Say "Da cai vao: $Dest" 'Green'

# ---------- 3. Cai thu vien Python can thiet ----------
Say "Dang cai thu vien (Flask, paramiko)..."
& $Py -m pip install --quiet --upgrade pip 2>$null | Out-Null
& $Py -m pip install --quiet -r (Join-Path $Dest 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Say "Cai thu vien that bai. Xem thong bao loi ben tren." 'Red'; return }
Say "Xong thu vien." 'Green'

# ---------- 4. Tao shortcut ngoai Desktop ----------
# Chon ban chay AN de bam shortcut khong hien cua so den:
#   python.exe -> pythonw.exe  |  py.exe (bo khoi chay) -> pyw.exe
$pyDir = Split-Path $Py
$pythonw = $Py
foreach ($cand in @('pythonw.exe', 'pyw.exe')) {
    $p = Join-Path $pyDir $cand
    if (Test-Path $p) { $pythonw = $p; break }
}
$lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'SimCity Panel.lnk'
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath       = $pythonw
$sc.Arguments        = '"' + (Join-Path $Dest 'launcher.pyw') + '"'
$sc.WorkingDirectory = $Dest
$sc.Description      = 'Mo bang dieu khien bot SimCity (VLTK)'
$icon = Join-Path $Dest 'static\favicon.ico'
if (Test-Path $icon) { $sc.IconLocation = $icon } else { $sc.IconLocation = "$pythonw,0" }
$sc.Save()
Say "Da tao shortcut: $lnk" 'Green'

# ---------- 5. Chay luon ----------
Write-Host ""
Write-Host "  ===== CAI DAT XONG =====" -ForegroundColor Yellow
Say "Dang mo panel tai http://127.0.0.1:5666 ..." 'Cyan'
Say "Lan sau chi can bam shortcut 'SimCity Panel' ngoai man hinh." 'Cyan'
Write-Host ""
Start-Process $pythonw -ArgumentList ('"' + (Join-Path $Dest 'launcher.pyw') + '"') -WorkingDirectory $Dest
