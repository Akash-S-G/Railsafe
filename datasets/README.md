# Datasets — Download Guide (Locked 2026-09-15, Final)

> **v1 uses only public downloads.** Rail-5k (restricted BY-NC-ND 4.0, email gate) and Rail-DB form-gated are **excluded from v1**.

## Quick Start (public only)

```bash
# 1) RailSense — Kaggle (requires ~/.kaggle/kaggle.json)
bash datasets/download_railsense.sh

# 2) Surface Faults — Mendeley CC BY 4.0 (direct browser download or API)
bash datasets/download_surface_faults.sh

# 3) RFDD — ScienceDB DOI (free account, 8.24 GB)
bash datasets/download_rfdd.sh

# 4) Rail-DB — optional, form-gated (skip for v1 if not needed)
bash datasets/download_raildb.sh   # then fill Google Form

# Verify
ls -lh datasets/
```

## Status

| Dataset | Script | Access | License | v1? |
|---|---|---|---|---|
| RailSense | `download_railsense.sh` | Kaggle API (`kashtennyson/railway-component-dataset`) + GH fallback | MIT | ✅ Primary |
| Surface Faults | `download_surface_faults.sh` | Mendeley `10.17632/8hxtgyyxrw.2` direct ZIP | CC BY 4.0 | ✅ Primary |
| RFDD | `download_rfdd.sh` | ScienceDB `10.57760/sciencedb.msdc.00071` 8.24 GB | MIT (code) | ✅ Primary |
| Rail-DB | `download_raildb.sh` | Google Form → email link, 7,432 pairs | MIT | ○ Optional |
| Rail-5k | — | Zenodo `10.5281/zenodo.4872619` **RESTRICTED email gate** | BY-NC-ND 4.0 | ❌ Skip v1 |
| Subgrade | — | figshare `10.6084/m9.figshare.24086016` + Nature page | CC BY | ○ Context only |
| Custom longitudinal | — | To be collected (Phase 10, **gated for v1**) | Internal | ⏸ Future Work |

## After Download

```bash
# Check expected layouts
ls datasets/railsense/          # crossties/ fasteners/ fishplates/ tracks/ each normal/ damaged/
ls datasets/track_surface_faults/
ls datasets/rfdd/               # HDF5 (train/val) + PNG (test) + RFDD-code/
ls datasets/raildb/             # optional

# Next: Phase 2 normalization
# python ml/dataset_tools/convert_to_manifest.py  (to be implemented)
```

## Licenses & Citations

See `docs/datasets/data-license.md` for full registry and BibTeX. Key DOIs:

- `10.17632/8hxtgyyxrw.2` (Surface)
- `10.57760/sciencedb.msdc.00071` (RFDD)
- `10.5281/zenodo.4872619` (Rail-5k, restricted)
- `10.6084/m9.figshare.24086016` (Subgrade)
- `10.3390/s26030906` (Sensors survey)
- `10.1038/s41597-024-03112-7` (Subgrade paper)

## .gitignore

Raw images are **never committed**. Manifests (`datasets/manifest.jsonl`) are committed; raw data is ignored.

```
datasets/railsense/
datasets/track_surface_faults/
datasets/rfdd/*.h5
datasets/rfdd/*.png
datasets/raildb/
```
