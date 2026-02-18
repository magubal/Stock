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


def get_oracle_config() -> dict:
    """Oracle 접속정보 반환. 키 없으면 None 값 포함 dict 반환 (에러 안 던짐)"""
    load_env()
    return {
        'dsn': os.getenv('ORACLE_DSN'),
        'user': os.getenv('ORACLE_USER'),
        'password': os.getenv('ORACLE_PASSWORD'),
    }


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    current = Path(__file__).resolve()
    for _ in range(5):
        current = current.parent
        if (current / '.env').exists():
            return current
    # Fallback to repository root based on this file location
    return Path(__file__).resolve().parents[4]


def get_growth_thresholds_path() -> str:
    """config/growth_thresholds.json 경로 반환"""
    return str(get_project_root() / "config" / "growth_thresholds.json")


# Auto-load on import
load_env()
