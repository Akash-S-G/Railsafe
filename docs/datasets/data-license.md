# Data Licenses & Provenance (Verified 2026-09-15)

> All entries verified via live fetch of GitHub LICENSE files, Mendeley Data page, ScienceDB, Zenodo, and Nature page on 2026-09-15. Access dates locked.

## 1. Registry (Locked)

| Dataset | Source URL | Access Date | Version / Commit | License | Redistribution | Commercial Use | Attribution | Notes |
|---|---|---|---|---|---|---|---|---|
| RailSense Railway Component | https://github.com/kashtennyson/RailSense + https://www.kaggle.com/datasets/kashtennyson/railway-component-dataset + `dataset-metadata.json` | 2026-09-15 | main branch, 51 commits | **MIT** (LICENSE file) | Yes (MIT) but **images are proxy-staged** — redistribute code, not necessarily images if Kaggle terms differ; verify Kaggle dataset page before publishing images | Yes (MIT) | Yes | Controlled proxy per README; legacy classifier on `legacy-version` branch |
| Railway Track Surface Faults | https://data.mendeley.com/datasets/8hxtgyyxrw/2 DOI `10.17632/8hxtgyyxrw.2` | 2026-09-15 | Version 2 (2022-01-06) | **CC BY 4.0** (Mendeley page) | Yes with attribution | Yes | Yes | 7 classes, 120 FPS EKEN-H9R provenance |
| RFDD | https://github.com/NIM-NMDC/RFDD + https://doi.org/10.57760/sciencedb.msdc.00071 (CSTR 14923.11.sciencedb.msdc.00071) | 2026-09-15 | v1 published 2025-12-26 14:10 GMT+8, 8.24 GB, 1 file | **MIT** (GH badge) + ScienceDB terms | Code MIT; dataset via ScienceDB (check ScienceDB license before mirroring) — **use ScienceDB download, not GH raw** | Per GH MIT for code; dataset per ScienceDB | Yes | 1350 imgs 2048×2021, HDF5+PNG, weights on Baidu AI Studio (requires Baidu login) |
| Rail-5k | https://zenodo.org/records/4872619 (v1) → https://zenodo.org/records/4872772 (current) DOI `10.5281/zenodo.4872619` | 2026-09-15 | v1 2021-05-30, 5,470 views, 0 downloads (restricted) | **Restricted — email application only** ; arXiv states **BY-NC-ND 4.0** for assets | **No** (restricted gate) | No (NC) | Yes | Through email application only — apply to Shanghai Key Lab; do not block v1 |
| Rail-DB | https://github.com/Sampson-Lee/Rail-Detection | 2026-09-15 | main, 26 commits, 96★ | **MIT** (LICENSE) | Yes (MIT) | Yes | Yes | 7,432 pairs, form download, pretrained Drive link |
| Subgrade Defects | https://www.nature.com/articles/s41597-024-03112-7 + figshare `10.6084/m9.figshare.24086016` | 2026-09-15 | Sci Data 11:293 (2024-03-14), 4,246 accesses | **Open Access, CC BY** (Nature page) + figshare terms | Yes with attribution | Yes | Yes | 661 records, not images; bias toward studied lines per Usage Notes |
| Custom longitudinal | Phase 10 collection | — | — | Internal / partner agreement (to be defined before collection) | Per agreement | Per agreement | — | Must define before any photography |

## 2. Verification Evidence

- **RailSense:** Fetch confirms MIT, 51 commits, README documents proxy staging, `requirements.txt` + `requirements-silicon.txt`, `main.py train/evaluate/predict/both`.
- **Surface Faults:** Mendeley page explicitly shows CC BY 4.0, DOI 10.17632/8hxtgyyxrw.2, 6 Jan 2022 v2.
- **RFDD:** GH README badge = MIT; scidb.cn page confirms DOI, 8.24 GB, 2025-12-26, 6 consistency principles Hierarchy vs older "Texture & Occlusion" wording — lock to **Geometry, Optics, Boundary, Noise, Texture, Hierarchy**.
- **Rail-5k:** Zenodo page shows "Dataset Restricted" + "Through email application only"; arXiv 2106.14366 § license = BY-NC-ND 4.0.
- **Rail-DB:** GH LICENSE = MIT; README download = Google Form email.
- **Subgrade:** Nature page = Open access; figshare DOI resolves; paper confirms 661 records, 239 locations.

## 3. Handling Rules (Locked)

- **Never commit raw image data** to git — store `datasets/download_*.sh` with curl/kaggle + checksums + `.gitignore` for `datasets/*`.
- **Never redistribute Rail-5k images** without explicit grant (restricted).
- **RFDD:** Download from ScienceDB DOI, not GH; host weights via Baidu link requires separate auth.
- **Cite DOIs** in report: 10.17632/8hxtgyyxrw.2, 10.57760/sciencedb.msdc.00071, 10.5281/zenodo.4872619, 10.6084/m9.figshare.24086016.

## 4. Citation Placeholders (Locked)

```bibtex
@dataset{railsense2024,
  title  = {Railway Component Dataset},
  author = {Tennyson, Kashten et al.},
  url    = {https://github.com/kashtennyson/RailSense},
  note   = {MIT, proxy-controlled, 4 components normal/damaged}
}
@article{surfacefaults2024,
  title   = {Railway track surface faults dataset},
  journal = {Data in Brief},
  doi     = {10.1016/j.dib.2024.110050},
  note    = {Mendeley 10.17632/8hxtgyyxrw.2, CC BY 4.0, 5153 images, 7 classes}
}
@dataset{rfdd2025,
  title = {The Railway Fastener Defect Dataset},
  doi   = {10.57760/sciencedb.msdc.00071},
  note  = {ScienceDB CSTR 14923.11.sciencedb.msdc.00071, MIT code, 1350 imgs 2048x2021}
}
@dataset{rail5k2021,
  title = {Rail-5k: a Real-World Dataset for Rail Surface Defects Detection},
  doi   = {10.5281/zenodo.4872619},
  note  = {Restricted, email application, BY-NC-ND 4.0, 5000 imgs 1100 annotated}
}
@inproceedings{raildb2022,
  title     = {Rail Detection: An Efficient Row-based Network and a New Benchmark},
  booktitle = {ACM MM 2022},
  url       = {https://github.com/Sampson-Lee/Rail-Detection},
  note      = {MIT, 7432 pairs, 9 scenes}
}
@article{subgrade2024,
  title   = {A Georeferenced Dataset for Mapping and Assessing Subgrade Defects ...},
  journal = {Scientific Data},
  doi     = {10.1038/s41597-024-03112-7},
  note    = {figshare 10.6084/m9.figshare.24086016, CC BY, 661 records}
}
```

## 5. Next Actions

- [ ] Run `kaggle datasets download kashtennyson/railway-component-dataset` + verify Kaggle terms match MIT
- [ ] Download RFDD from ScienceDB DOI (not GH) + verify 8.24 GB checksum
- [ ] Submit Rail-5k email application (do not wait for it)
- [ ] Fill Rail-DB Google Form + save Drive model checksum
- [ ] Create `datasets/README.md` with download scripts + citations above
