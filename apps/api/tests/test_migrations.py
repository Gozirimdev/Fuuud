"""Check the deployment migration chain independently of the SQLite API fixtures."""

import os
import subprocess
import sys
from pathlib import Path


def test_postgresql_migrations_compile():
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "DATABASE_URL": "postgresql+psycopg://test:test@localhost/test"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "CREATE TABLE users" in result.stdout
    assert "ADD COLUMN session_version" in result.stdout
    assert "CREATE TABLE account_emails" in result.stdout
