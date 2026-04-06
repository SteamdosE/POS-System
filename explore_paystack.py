#!/usr/bin/env python
"""Test and explore the Paystack SDK directly."""

from paystack import Transaction, Configuration
import json

# Create a Transaction instance
print("=" * 60)
print("PAYSTACK SDK EXPLORATION")
print("=" * 60)

# Test 1: Transaction initialization
print("\n1. Creating Transaction instance...")
t = Transaction()
print(f"   Transaction created: {t}")
print(f"   API client: {t.api_client}")
print(f"   Configuration: {t.api_client.configuration}")
print(f"   API key initial state: {t.api_client.configuration.api_key}")

# Test 2: Setting Bearer token
print("\n2. Setting Bearer token...")
if t.api_client.configuration.api_key is None:
    t.api_client.configuration.api_key = {}
    print("   Initialized api_key as empty dict")

t.api_client.configuration.api_key['Bearer'] = 'sk_test_384873d018d144def2cd5e7c7f2549866f4d37f9'
print(f"   API key after setting: {t.api_client.configuration.api_key}")

# Test 3: Check initialize method signature
print("\n3. Transaction.initialize method...")
import inspect
sig = inspect.signature(t.initialize)
print(f"   Signature: initialize{sig}")

# Test 4: Try initialize call
print("\n4. Testing initialize call (without actually sending)...")
try:
    # Don't actually call it, just show what parameters it expects
    print("   Would call: t.initialize(email='test@example.com', amount=100000, ...)")
except Exception as e:
    print(f"   Error: {e}")

# Test 5: Check verify method
print("\n5. Transaction.verify method...")
sig_verify = inspect.signature(t.verify)
print(f"   Signature: verify{sig_verify}")

print("\n" + "=" * 60)
print("SUMMARY: SDK is ready to use")
print("=" * 60)
