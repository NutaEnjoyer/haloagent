# Restart Docker container with fixes

Write-Host "Stopping container..." -ForegroundColor Yellow
docker-compose down

Write-Host "`nRebuilding and starting container..." -ForegroundColor Yellow
docker-compose up --build -d

Write-Host "`nWaiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`nChecking health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "✓ Container is healthy!" -ForegroundColor Green
} catch {
    Write-Host "✗ Container not ready yet, check logs: docker-compose logs -f" -ForegroundColor Red
}

Write-Host "`nReady to test! Run: .\test_call.ps1" -ForegroundColor Cyan
