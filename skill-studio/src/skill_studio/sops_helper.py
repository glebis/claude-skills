from __future__ import annotations
import subprocess
from pathlib import Path


def encrypt_dotenv(path: Path) -> None:
    """Encrypt a file in place using sops. Uses defaults (.sops.yaml creation rules).

    Runs with cwd = path.parent so sops can find the nearest .sops.yaml by walking
    up from there (rather than from wherever the skill was invoked).
    """
    result = subprocess.run(
        ["sops", "--encrypt", "--in-place", path.name],
        cwd=str(path.parent),
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"sops encrypt failed (exit {result.returncode}):\n"
            f"STDERR:\n{result.stderr}\n"
            f"STDOUT:\n{result.stdout}"
        )


def decrypt_dotenv(path: Path) -> dict[str, str]:
    """Decrypt a sops-encrypted file and parse as dotenv."""
    result = subprocess.run(
        ["sops", "--decrypt", path.name],
        cwd=str(path.parent),
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"sops decrypt failed (exit {result.returncode}):\n"
            f"STDERR:\n{result.stderr}"
        )
    env: dict[str, str] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env
