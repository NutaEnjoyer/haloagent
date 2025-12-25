#!/usr/bin/env python3
"""
Quick Test Script for AI Calling System
Works on Windows, Linux, and Mac
"""

import sys
import requests
from typing import Optional

# Colors for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text: str, color: str = Colors.RESET):
    """Print colored text to console."""
    print(f"{color}{text}{Colors.RESET}")

def check_backend_health() -> bool:
    """Check if backend is running."""
    print_colored("Step 1: Checking backend health...", Colors.YELLOW)

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_colored("✅ Backend is running!", Colors.GREEN)
            print_colored(f"   Status: {data.get('status')}", Colors.GRAY)
            print_colored(f"   Active calls: {data.get('active_calls')}", Colors.GRAY)
            print()
            return True
        else:
            print_colored("❌ Backend returned error status", Colors.RED)
            return False

    except requests.exceptions.ConnectionError:
        print_colored("❌ Backend is NOT running!", Colors.RED)
        print_colored("   Please start it with:", Colors.RED)
        print_colored("   python -m uvicorn app.main:app --reload", Colors.YELLOW)
        print()
        return False
    except Exception as e:
        print_colored(f"❌ Error: {e}", Colors.RED)
        return False

def get_phone_number() -> str:
    """Get phone number from user input."""
    print_colored("Step 2: Enter test phone number", Colors.YELLOW)

    try:
        phone = input("Phone number (format: +79019433546, press Enter for default): ").strip()

        if not phone:
            phone = "+79019433546"
            print_colored(f"   Using default: {phone}", Colors.GRAY)

        print()
        return phone

    except KeyboardInterrupt:
        print()
        print_colored("Test cancelled", Colors.YELLOW)
        sys.exit(0)

def make_test_call(phone: str) -> Optional[dict]:
    """Initiate a test call."""
    print_colored("Step 3: Initiating call...", Colors.YELLOW)

    try:
        response = requests.post(
            "http://localhost:8000/calls",
            json={"phone": phone},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_colored("✅ Call initiated successfully!", Colors.GREEN)
            print()
            print_colored("Call Details:", Colors.CYAN)
            print_colored(f"  Call ID: {data.get('call_id')}", Colors.GRAY)
            print_colored(f"  Phone: {data.get('phone')}", Colors.GRAY)
            print_colored(f"  Status: {data.get('status')}", Colors.GRAY)
            print()
            return data
        else:
            print_colored(f"❌ Failed to initiate call! Status: {response.status_code}", Colors.RED)
            print_colored(f"   Response: {response.text}", Colors.RED)
            return None

    except Exception as e:
        print_colored(f"❌ Error making call: {e}", Colors.RED)
        return None

def print_expected_flow():
    """Print what should happen during the test."""
    print_colored("=" * 60, Colors.CYAN)
    print_colored("📱 Check your phone now!", Colors.GREEN + Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    print()
    print_colored("What should happen:", Colors.YELLOW)
    print_colored("  1. ☎️  Your phone rings", Colors.GRAY)
    print_colored("  2. 🎤 You hear: 'Здравствуйте! Я голосовой ассистент...'", Colors.GRAY)
    print_colored("  3. 🗣️  Say something (e.g., 'Хочу узнать о ваших услугах')", Colors.GRAY)
    print_colored("  4. ⏱️  Wait ~3-5 seconds for processing", Colors.GRAY)
    print_colored("  5. 🤖 Hear AI response", Colors.GRAY)
    print_colored("  6. 🔄 Continue conversation!", Colors.GRAY)
    print()
    print_colored("Expected backend logs:", Colors.YELLOW)
    print_colored("  - [Voximplant] Initiating call", Colors.GRAY)
    print_colored("  - [Voximplant Webhook] Connected", Colors.GRAY)
    print_colored("  - [Voximplant Audio] Processing audio", Colors.GRAY)
    print_colored("  - STT completed", Colors.GRAY)
    print_colored("  - [Voximplant Audio] User said: ...", Colors.GRAY)
    print_colored("  - GPT completed", Colors.GRAY)
    print_colored("  - [Voximplant Audio] AI response: ...", Colors.GRAY)
    print()
    print_colored("📊 Watch your backend terminal for detailed logs!", Colors.YELLOW)
    print()

def main():
    """Main test flow."""
    print_colored("=" * 60, Colors.CYAN)
    print_colored("🧪 AI Call Test Script", Colors.CYAN + Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    print()

    # Step 1: Check backend
    if not check_backend_health():
        sys.exit(1)

    # Step 2: Get phone number
    phone = get_phone_number()

    # Step 3: Make call
    result = make_test_call(phone)

    if result:
        # Print expected flow
        print_expected_flow()

        # Success
        print_colored("=" * 60, Colors.GREEN)
        print_colored("Test initiated successfully! ✅", Colors.GREEN + Colors.BOLD)
        print_colored("=" * 60, Colors.GREEN)
    else:
        # Failure
        print_colored("Test failed! ❌", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_colored("Test cancelled by user", Colors.YELLOW)
        sys.exit(0)
