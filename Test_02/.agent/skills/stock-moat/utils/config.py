"""
Configuration loader for stock-moat utilities
Loads environment variables from .env file
"""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file"""
    # Find project root (contains .env file)
    current = Path(__file__).resolve()
    project_root = None

    # Search up to 5 levels
    for _ in range(5):
        current = current.parent
        env_file = current / '.env'
        if env_file.exists():
            project_root = current
            break

    if project_root:
        env_file = project_root / '.env'
        # Simple .env parser (no external dependencies)
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # .env file takes precedence over system environment
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")


def get_dart_api_key() -> str:
    """Get DART API key from environment"""
    load_env()
    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        raise ValueError(
            "DART_API_KEY not found in environment variables.\n"
            "Please set it in .env file at project root."
        )
    return api_key


# Auto-load on import
load_env()
