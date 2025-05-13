#!/usr/bin/env python3
"""
Setup script to create necessary directories for the Sunmax Renewables Management System.
These directories are excluded from Git via .gitignore but are required for the application to function.
"""

import os
import sys

# List of directories to create
DIRECTORIES = [
    'invoices',
    'quotations',
    'customers',
    'services',
    'payments',
    'documents',
    'uploads',
    'temp',
    'db/backups'
]

def create_directories():
    """Create all necessary directories if they don't exist."""
    print("Creating necessary directories for Sunmax Renewables Management System...")
    
    for directory in DIRECTORIES:
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✓ Created directory: {directory}")
            else:
                print(f"✓ Directory already exists: {directory}")
        except Exception as e:
            print(f"✗ Error creating directory {directory}: {e}", file=sys.stderr)
            return False
    
    print("\nAll directories created successfully!")
    print("\nNote: These directories are excluded from Git via .gitignore.")
    print("If you're deploying to a new environment, run this script to set up the required directories.")
    
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
