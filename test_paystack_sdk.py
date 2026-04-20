#!/usr/bin/env python
"""Test Paystack SDK configuration."""
import os
import sys

from dotenv import load_dotenv
from paystack.configuration import Configuration
from paystack import Transaction

load_dotenv()

print("Testing SDK configuration...")
print()

# Create configuration
config = Configuration()
print(f"Default Configuration api_key: {config.api_key}")
print()

# Try setting Bearer token
secret_key = (os.getenv("PAYSTACK_SECRET_KEY") or "").strip()
if not secret_key:
	print("PAYSTACK_SECRET_KEY is missing in environment")
	sys.exit(1)

config.api_key['Bearer'] = secret_key
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

