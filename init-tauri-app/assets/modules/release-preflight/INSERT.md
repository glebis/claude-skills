# Insert: Release + preflight

1. Copy `preflight.sh`, `release.sh` → `scripts/` (chmod +x both).
2. Copy `ci.yml`, `release.yml` → `.github/workflows/`.
3. Substitute `<name>` throughout.
4. Verify: `bash -n scripts/preflight.sh scripts/release.sh && bash scripts/preflight.sh hook`.
