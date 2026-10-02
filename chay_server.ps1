# chay_server.ps1 — Tắt hết tiến trình server cũ, khởi động lại server INVEST
# Dùng: nhấp phải file này > "Run with PowerShell", hoặc gõ: .\chay_server.ps1
$python = "D:\INVEST\WPy64-3.13.12.0\python\python.exe"
$thuMuc = "D:\INVEST"

Write-Host "1) Dung cac tien trinh server cu..." -ForegroundColor Yellow
Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
    Where-Object { $_.CommandLine -like "*invest_web*" } |
    ForEach-Object {
        Write-Host "   Dung PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force
    }
Start-Sleep -Seconds 2

Write-Host "2) Khoi dong server moi..." -ForegroundColor Yellow
Start-Process -FilePath $python -ArgumentList "invest_web.py" -WorkingDirectory $thuMuc -WindowStyle Hidden

Write-Host "3) Kiem tra..." -ForegroundColor Yellow
Start-Sleep -Seconds 4
try {
    $code = (Invoke-WebRequest -Uri http://127.0.0.1:5000 -UseBasicParsing -TimeoutSec 10).StatusCode
    Write-Host "OK - server dang chay (HTTP $code)." -ForegroundColor Green
    Write-Host "Mo trinh duyet: http://127.0.0.1:5000" -ForegroundColor Green
} catch {
    Write-Host "LOI - server khong phan hoi. Xem log." -ForegroundColor Red
}
