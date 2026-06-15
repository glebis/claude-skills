# License selection

Help the user choose, then write the LICENSE with `scripts/fetch_license.py`.
Default for this author: **Apache-2.0** (see profile `defaults.license`).

| SPDX id | Type | Use when | Notes |
|---|---|---|---|
| `Apache-2.0` | Permissive | Default. Want permissive + explicit patent grant. | Pair with `NOTICE`. Needs a `## License` note in README. |
| `MIT` | Permissive | Simplest, shortest, max adoption. | No patent grant. Bundled offline. |
| `BSD-3-Clause` | Permissive | Like MIT + no-endorsement clause. | Bundled offline. |
| `MPL-2.0` | Weak copyleft | Want file-level copyleft but allow proprietary combos. | |
| `GPL-3.0-or-later` | Strong copyleft | Derivatives must stay open. | |
| `AGPL-3.0-or-later` | Strong copyleft + network | Close the SaaS loophole. | |
| `Unlicense` / `CC0-1.0` | Public domain | Renounce all rights. | Not for code needing patent peace. |

Guidance:
- **Permissive (Apache/MIT/BSD)** maximises adoption; **Apache-2.0** adds patent
  protection and is this author's default.
- **Copyleft (GPL/AGPL/MPL)** keeps derivatives open; note GPL/AGPL are
  *incompatible* with this author's usual permissive posture — confirm intent.
- Dual-licensing and relicensing are painful later — confirm the choice now.
- SPDX ids: <https://spdx.org/licenses/>. The script fetches any id from the
  SPDX license-list-data repo when not bundled.

## Writing the LICENSE

```sh
python scripts/fetch_license.py <SPDX-ID> --author "<name>" --year <year>
```

For **Apache-2.0** also create `NOTICE` from `assets/templates/NOTICE.txt`, and
set `license = "Apache-2.0"` + `license-files` in package metadata.
