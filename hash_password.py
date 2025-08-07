#!/usr/bin/env python3
"""
Simple password hashing utility for Drumlog
"""

import hashlib
import getpass

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    print("🔐 Drumlog Password Hash Generator")
    print("=" * 40)
    
    # Option 1: Direct input
    password = input("Enter password to hash: ")
    if password:
        hashed = hash_password(password)
        print(f"\n✅ Hashed password: {hashed}")
        print(f"📝 Add to users.py: \"username\": \"{hashed}\"")
    
    print("\n" + "=" * 40)
    
    # Option 2: Interactive mode
    while True:
        username = input("\nEnter username (or 'quit' to exit): ")
        if username.lower() == 'quit':
            break
            
        password = getpass.getpass(f"Enter password for {username}: ")
        if password:
            hashed = hash_password(password)
            print(f"✅ {username}: {hashed}")
            print(f"📝 Add to users.py: \"{username}\": \"{hashed}\"")
    
    print("\n👋 Goodbye!")
