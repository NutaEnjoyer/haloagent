# Quick Test Script for AI Calling System
# PowerShell script for Windows

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "🧪 AI Call Test Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if backend is running
Write-Host "Step 1: Checking backend health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Backend is running!" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
    Write-Host "   Active calls: $($response.active_calls)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Backend is NOT running!" -ForegroundColor Red
    Write-Host "   Please start it with: python -m uvicorn app.main:app --reload" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Step 2: Ask for phone number
Write-Host "Step 2: Enter test phone number" -ForegroundColor Yellow
$phone = Read-Host "Phone number (format: +79019433546)"

if ($phone -eq "") {
    $phone = "+79019433546"
    Write-Host "   Using default: $phone" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Make the call
Write-Host "Step 3: Initiating call..." -ForegroundColor Yellow

$body = @{
    phone = $phone
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/calls" -Method Post -Body $body -ContentType "application/json"

    Write-Host "✅ Call initiated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Call Details:" -ForegroundColor Cyan
    Write-Host "  Call ID: $($response.call_id)" -ForegroundColor Gray
    Write-Host "  Phone: $($response.phone)" -ForegroundColor Gray
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host "📱 Check your phone now!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "What should happen:" -ForegroundColor Yellow
    Write-Host "  1. ☎️  Your phone rings" -ForegroundColor Gray
    Write-Host "  2. 🎤 You hear: 'Здравствуйте! Я голосовой ассистент...'" -ForegroundColor Gray
    Write-Host "  3. 🗣️  Say something (e.g., 'Хочу узнать о ваших услугах')" -ForegroundColor Gray
    Write-Host "  4. ⏱️  Wait ~3-5 seconds for processing" -ForegroundColor Gray
    Write-Host "  5. 🤖 Hear AI response" -ForegroundColor Gray
    Write-Host "  6. 🔄 Continue conversation!" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Watch backend logs for details!" -ForegroundColor Yellow

} catch {
    Write-Host "❌ Failed to initiate call!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    exit 1
}
