@echo off
REM Create self-signed certificate using PowerShell (no OpenSSL needed)

echo ========================================
echo   Creating SSL Certificate (PowerShell)
echo ========================================
echo.

powershell -Command "& { ^
    $cert = New-SelfSignedCertificate ^
        -DnsName 'localhost','192.168.1.42' ^
        -CertStoreLocation 'Cert:\CurrentUser\My' ^
        -NotAfter (Get-Date).AddYears(1); ^
    $pwd = ConvertTo-SecureString -String 'password' -Force -AsPlainText; ^
    $path = 'cert.pfx'; ^
    Export-PfxCertificate -Cert $cert -FilePath $path -Password $pwd; ^
    Write-Host 'Certificate exported to cert.pfx'; ^
}"

echo.
echo ========================================
echo   Certificate Created!
echo ========================================
echo.
echo File created: cert.pfx
echo.
echo To start server with HTTPS:
echo   uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile cert.pfx --ssl-certfile cert.pfx
echo.
echo OR convert to PEM format:
echo   openssl pkcs12 -in cert.pfx -out key.pem -nodes -nocerts
echo   openssl pkcs12 -in cert.pfx -out cert.pem -nodes -nokeys
echo   (password: password)
echo.
pause
