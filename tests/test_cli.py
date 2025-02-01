import subprocess
import sys


def test_help():
    """Simple test checking the 'help' output from the CLI."""
    cmd = [sys.executable, "-m", "ak.cli", "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Usage: " in res.stdout
