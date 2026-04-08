#!/usr/bin/env python
"""Test Paystack SDK configuration."""
from paystack.configuration import Configuration
from paystack import Transaction

print("Testing SDK configuration...")
print()

# Create configuration
config = Configuration()
print(f"Default Configuration api_key: {config.api_key}")
print()

# Try setting Bearer token
config.api_key['Bearer'] = 'sk_test_example'
print(f"After setting Bearer: {config.api_key}")
print()

# Try creating Transaction with config
print("Creating Transaction instance...")
t = Transaction()
print(f"Transaction api_client: {t.api_client}")
print(f"Transaction api_client.configuration: {t.api_client.configuration}")
print()

# Try calling initialize
print("Testing Transaction.initialize call signature:")
import inspect
sig = inspect.signature(t.initialize)
print(f"  initialize{sig}")

