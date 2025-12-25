# PowerShell script to test the Voice Caller API

Write-Host "Testing Voice Caller API..." -ForegroundColor Green

# 1. Check health
Write-Host "`n1. Checking /health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "Health check: OK" -ForegroundColor Green
    Write-Host ($health | ConvertTo-Json)
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Make a test call
Write-Host "`n2. Making test call..." -ForegroundColor Yellow
try {
    $headers = @{
        "Content-Type" = "application/json"
        "X-API-Key" = "test-key-123"
    }

    $body = @{
        phone = "+79991234567"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8000/call" -Method Post -Headers $headers -Body $body

    Write-Host "Call initiated successfully!" -ForegroundColor Green
    Write-Host "Call ID: $($response.call_id)" -ForegroundColor Cyan
    Write-Host "Status: $($response.status)" -ForegroundColor Cyan

    Write-Host "`nWait 30-60 seconds for the call to complete, then check:" -ForegroundColor Yellow
    Write-Host "  - Docker logs: docker-compose logs -f callerapi" -ForegroundColor Gray
    Write-Host "  - Results: cat mock_sheets_data/calls.csv" -ForegroundColor Gray

} catch {
    Write-Host "Call failed: $_" -ForegroundColor Red
    Write-Host $_.Exception.Response.StatusCode -ForegroundColor Red
    exit 1
}
