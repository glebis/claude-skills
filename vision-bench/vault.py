"""Auto-decrypt secrets.enc.yaml via SOPS + age, fall back to environment variables."""
import os
import subprocess
from pathlib import Path

SECRETS_FILE = Path(__file__).parent / "secrets.enc.yaml"
_cache: dict = {}


def _load_sops() -> dict:
    if not SECRETS_FILE.exists():
        return {}
    age_key = Path.home() / ".config/sops/age/keys.txt"
    env = os.environ.copy()
    if age_key.exists():
        env["SOPS_AGE_KEY_FILE"] = str(age_key)
    try:
        result = subprocess.run(
            ["sops", "--decrypt", "--output-type", "yaml", str(SECRETS_FILE)],
            capture_output=True, text=True, env=env, timeout=10
        )
        if result.returncode == 0:
            import yaml
            return yaml.safe_load(result.stdout) or {}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return {}


def get(key: str) -> str | None:
    """Return secret: SOPS file first, then environment variable."""
    global _cache
    if not _cache:
        _cache = _load_sops()
    return _cache.get(key) or os.environ.get(key)


def require(key: str) -> str:
    val = get(key)
    if not val:
        raise RuntimeError(
            f"Missing secret '{key}'. Add it to secrets.enc.yaml or set ${key} in your environment."
        )
    return val
