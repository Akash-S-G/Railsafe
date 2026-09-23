"""Temporal association — GATED (requires Dataset G). Stub for v1."""
# Aij = wg*Gij + wv*Vij + ws*Sij
# G=spatial (GPS/chainage), V=visual (DINOv2/ResNet cosine), S=geometric
# Hungarian assignment — evaluate Precision/Recall/F1/ID switches in Exp7 (gated)
def associate(detections, assets, weights=(0.5, 0.35, 0.15)):
    raise NotImplementedError("GATED — requires Dataset G (asset_id + timestamp + repeated observations)")
