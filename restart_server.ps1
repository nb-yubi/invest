# restart_server.ps1 — Restart server INVEST (dọn tiến trình cũ, chạy lại ở chế độ nền)
# Dùng: nhấp phải file này -> Run with PowerShell, hoặc chạy trong PowerShell: .\restart_server.ps1

$python = "D:\00.NB\INVEST\WPy64-3.13.12.0\python\python.exe"
$thuMuc = "D:\00.NB\INVEST"

Write-Host "1) Dang tat cac tien trinh invest_web.py cu..."
Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
    Where-Object { $_.CommandLine -like "*invest_web*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 2

Write-Host "2) Khoi dong lai server..."
Start-Process -FilePath $python -ArgumentList "invest_web.py" `
    -WorkingDirectory $thuMuc -WindowStyle Hidden
Start-Sleep -Seconds 3

try {
    $code = (Invoke-WebRequest -Uri http://127.0.0.1:5000 -UseBasicParsing -TimeoutSec 10).StatusCode
    Write-Host "OK - server dang chay (HTTP $code). Mo http://127.0.0.1:5000 tren trinh duyet." -ForegroundColor Green
} catch {
    Write-Host "LOI - server khong phan hoi. Hay kiem tra log." -ForegroundColor Red
}
Write-Host "Nhan phim bat ky de dong cua so..."
$null = Read-Host
