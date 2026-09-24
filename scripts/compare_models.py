#!/usr/bin/env python3
"""
Model comparison on the SAME splits (datasets/yolo_surface, 7 classes):
  Task A classification: YOLO11n-cls (existing best.pt) vs EfficientNet-B0 vs ResNet18 (timm, frozen backbone + head, 3 epochs)
  Task B anomaly: feature-kNN (timm EfficientNet avgpool features, normal train vs damaged) -> AUROC
    compares to RailSense (0.89 lit) / PaDiM (0.945) / PatchCore (0.99) claims

CPU-friendly: torch.set_num_threads, batch 32, workers 4, imgsz 224.
Saves: experiments/results/model_compare.json + model_compare.md

Usage:
  python scripts/compare_models.py --epochs 3
  python scripts/compare_models.py --skip-train   # eval only
"""
import argparse, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "experiments" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# ---------- Task A: classification ----------
def eval_yolo():
    from ultralytics import YOLO
    w = ROOT / "experiments" / "results" / "best_surface_cls.pt"
    if not w.exists():
        w = ROOT / "runs" / "yolo" / "surface_classify" / "weights" / "best.pt"
    if not w.exists():
        log("YOLO weights missing — skip")
        return None
    yolo = YOLO(str(w))
    out = {}
    for split in ["val", "test"]:
        m = yolo.val(data=str(ROOT / "datasets" / "yolo_surface"), split=split, verbose=False)
        out[split] = {"top1": round(float(m.top1), 4), "top5": round(float(m.top5), 4)}
    log(f"YOLO11n-cls: {out}")
    return {"model": "yolo11n-cls (3.1M, trained 10ep)", "params": "1.5M", **{f"{k}": v for k, v in out.items()}}

def build_loaders():
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    root = ROOT / "datasets" / "yolo_surface"
    tr = datasets.ImageFolder(root / "train", transform=tf)
    va = datasets.ImageFolder(root / "val", transform=tf)
    te = datasets.ImageFolder(root / "test", transform=tf)
    common = dict(batch_size=32, num_workers=4)
    return (DataLoader(tr, shuffle=True, **common),
            DataLoader(va, shuffle=False, **common),
            DataLoader(te, shuffle=False, **common),
            tr.classes)

def train_timm_model(name, epochs, train_loader, val_loader, num_classes):
    import torch, timm, torch.nn as nn
    torch.set_num_threads(8)
    device = "cpu"
    model = timm.create_model(name, pretrained=True, num_classes=num_classes)
    # freeze backbone, train head only (linear probe — fast, fair quick baseline)
    for p in model.parameters():
        p.requires_grad = False
    if hasattr(model, "get_classifier"):
        classifier = model.get_classifier()
    else:
        classifier = model.head
    for p in classifier.parameters():
        p.requires_grad = True
    model.to(device)
    opt = torch.optim.Adam(classifier.parameters(), lr=1e-3)
    crit = nn.CrossEntropyLoss()
    for ep in range(epochs):
        model.train()
        t0 = time.time()
        running, n = 0.0, 0
        for x, y in train_loader:
            opt.zero_grad()
            out = model(x)
            loss = crit(out, y)
            loss.backward()
            opt.step()
            running += loss.item() * x.size(0); n += x.size(0)
        log(f"{name} epoch {ep+1}/{epochs}: loss {running/n:.4f} ({time.time()-t0:.0f}s)")
    return model

def eval_torch_model(model, loader):
    import torch
    torch.set_num_threads(8)
    model.eval()
    correct1 = correct5 = total = 0
    with torch.no_grad():
        for x, y in loader:
            out = model(x)
            _, top5 = out.topk(5, dim=1)
            correct1 += (top5[:, 0] == y).sum().item()
            correct5 += (top5 == y.unsqueeze(1)).any(dim=1).sum().item()
            total += y.size(0)
    return {"top1": round(correct1 / total, 4), "top5": round(correct5 / total, 4), "n": total}

def compare_classification(epochs, skip_train):
    out = {"yolo": eval_yolo()}
    if not skip_train:
        train_loader, val_loader, test_loader, classes = build_loaders()
        log(f"Classes: {classes} (train {len(train_loader.dataset)} val {len(val_loader.dataset)} test {len(test_loader.dataset)})")
        for name, label in [("efficientnet_b0", "efficientnet_b0 (5.3M, linear probe)"),
                            ("resnet18", "resnet18 (11.8M, linear probe)")]:
            model = train_timm_model(name, epochs, train_loader, val_loader, len(classes))
            out[name] = {"model": label,
                         "val": eval_torch_model(model, val_loader),
                         "test": eval_torch_model(model, test_loader)}
            log(f"{name}: val {out[name]['val']} test {out[name]['test']}")
    return out

# ---------- Task B: anomaly via patch-level feature kNN (mini-PatchCore, no anomalib) ----------
def feature_knn_anomaly():
    """Proper mini-PatchCore: efficientnet_b0 penultimate feature map (7x7x1280) -> patch memory bank
    from 80% of normal images; score = max patch distance to nearest normal patch.
    AUROC over 20% normal test + all damaged. Per docs/architecture/anomaly.md:56 method."""
    import torch, timm, numpy as np
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader, Subset
    from sklearn.metrics import roc_auc_score
    torch.set_num_threads(8)
    model = timm.create_model("efficientnet_b0", pretrained=True, num_classes=0, features_only=False)
    model.eval()
    # hook the penultimate feature map (global_context / final_act before head) -> 7x7 grid
    feats_map = {}
    def hook(m, i, o): feats_map["x"] = o
    # efficientnet_b0: model.global_context or the conv before global_pool produces 7x7x(1280)
    target_layer = model.conv_head  # 7x7x1280 (before BN+act via head)
    h = target_layer.register_forward_hook(hook)
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    def patch_feats(folder, subset=None, file_filter=None):
        """folder with images directly (leaf) — custom file list dataset; file_filter(fn(path)->bool)."""
        from torch.utils.data import Dataset
        files = sorted([p for p in Path(folder).iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"]])
        if file_filter:
            files = [p for p in files if file_filter(p)]
        class FileDS(Dataset):
            def __len__(self): return len(files)
            def __getitem__(self, i):
                from PIL import Image
                img = Image.open(files[i]).convert("RGB")
                return tf(img), 0
        ds = FileDS()
        if subset is not None:
            ds = Subset(ds, subset)
        dl = DataLoader(ds, batch_size=16, num_workers=4)
        all_patches = []
        with torch.no_grad():
            for x, _y in dl:
                model(x)
                fm = feats_map["x"]  # [B,1280,7,7]
                p = fm.permute(0, 2, 3, 1).reshape(-1, fm.shape[1])  # [B*49,1280]
                all_patches.append(p)
        return torch.cat(all_patches), None
    base = ROOT / "datasets" / "railsense"
    # normal: 80% memory / 20% test (seeded) — crossties normal leaf
    n = len(list((base / "crossties" / "normal").glob("*.jpg")))
    g = np.random.RandomState(1337)
    idx = g.permutation(n)
    n_mem = int(n * 0.8)
    mem_idx, norm_test_idx = idx[:n_mem], idx[n_mem:]
    log(f"normal: {n} -> memory {n_mem}, normal-test {len(norm_test_idx)}")
    mem_patches, _ = patch_feats(base / "crossties" / "normal", mem_idx.tolist())
    norm_test_patches, _ = patch_feats(base / "crossties" / "normal", norm_test_idx.tolist())
    # damaged: all components
    anom_patches = []
    for comp in ["crossties", "fasteners", "fishplates"]:
        d = base / comp / "damaged"
        if d.exists():
            p, _ = patch_feats(d)
            anom_patches.append(p)
    anom_patches = torch.cat(anom_patches)
    log(f"patch memory {len(mem_patches)} (7x7x{n_mem} imgs), anom {len(anom_patches)}, norm-test {len(norm_test_patches)}")
    # memory bank subsample (coreset-lite): cap at 20k patches
    if len(mem_patches) > 20000:
        sel = np.random.RandomState(0).choice(len(mem_patches), 20000, replace=False)
        mem_patches = mem_patches[sel]
    mem_n = mem_patches / mem_patches.norm(dim=1, keepdim=True).clamp_min(1e-8)
    def image_scores(patches):
        s = []
        for i in range(0, len(patches), 4096):
            chunk = patches[i:i+4096]
            cn = chunk / chunk.norm(dim=1, keepdim=True).clamp_min(1e-8)
            d = 1 - cn @ mem_n.T
            s.append(d.max(dim=1).values)
        s = torch.cat(s)  # per-patch max distance
        # image score = mean of top-1% patch distances (per original image ordering: reshape back)
        return s
    anom_img_patches = anom_patches
    # per-image: patches came flattened per batch in order -> group by 49
    def per_image(patch_scores, k_pct=0.01):
        n_imgs = len(patch_scores) // 49
        s = patch_scores[:n_imgs * 49].reshape(n_imgs, 49)
        topk = max(1, int(49 * k_pct))
        return s.topk(topk, dim=1).values.mean(dim=1).numpy()
    anom_scores = per_image(image_scores(anom_img_patches))
    norm_scores = per_image(image_scores(norm_test_patches))
    y_true = [1] * len(anom_scores) + [0] * len(norm_scores)
    y_score = list(anom_scores) + list(norm_scores)
    auroc = round(float(roc_auc_score(y_true, y_score)), 4)
    log(f"patch-kNN mini-PatchCore AUROC: {auroc} (n_anom {len(anom_scores)}, n_norm {len(norm_scores)})")
    return {"model": "patch-kNN (mini-PatchCore: efficientnet_b0 conv_head 7x7x1280, coreset 20k, top-1% mean, generic ImageNet features)",
            "auroc": auroc,
            "n_memory_imgs": int(n_mem), "n_anomaly": int(len(anom_scores)), "n_normal_test": int(len(norm_scores)),
            "lit_compare": {"railsense_ae_domain_trained": 0.89, "padim": 0.945, "patchcore": 0.99}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--skip-train", action="store_true")
    args = ap.parse_args()
    result = {"timestamp": time.strftime("%Y-%m-%d %H:%M"), "task": "compare models on yolo_surface splits + railsense anomaly"}
    try:
        result["classification"] = compare_classification(args.epochs, args.skip_train)
    except Exception as e:
        log(f"classification error: {e}")
        result["classification"] = {"error": str(e)}
    try:
        result["anomaly"] = feature_knn_anomaly()
    except Exception as e:
        log(f"anomaly error: {e}")
        result["anomaly"] = {"error": str(e)}
    (RESULTS / "model_compare.json").write_text(json.dumps(result, indent=2))
    # markdown
    lines = [f"# Model Comparison — {result['timestamp']}", "",
             "## Classification (surface_faults 7 classes, same splits)"]
    cls = result.get("classification", {})
    if "yolo" in cls and cls["yolo"]:
        y = cls["yolo"]
        lines.append(f"- **YOLO11n-cls** (1.5M, trained 10ep): val top1 {y['val']['top1']} / test top1 {y['test']['top1']}")
    for k in ["efficientnet_b0", "resnet18"]:
        if k in cls and "val" in cls[k]:
            m = cls[k]
            lines.append(f"- **{m['model']}**: val top1 {m['val']['top1']} / test top1 {m['test']['top1']}")
    lines += ["", "## Anomaly (railsense normal vs damaged)"]
    an = result.get("anomaly", {})
    if "auroc" in an:
        lines.append(f"- **{an['model']}**: AUROC {an['auroc']} (memory {an['n_memory']}, anom {an['n_anomaly']}, norm {an['n_normal_test']})")
        lines.append(f"- Literature: RailSense AE 0.89 / PaDiM 0.945 / PatchCore 0.99 (docs/architecture/anomaly.md:56)")
    (RESULTS / "model_compare.md").write_text("\n".join(lines) + "\n")
    log(f"Saved {RESULTS/'model_compare.json'} + model_compare.md")

if __name__ == "__main__":
    main()
