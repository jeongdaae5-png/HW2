"""Download 100 public LFW face images and compare v1/v2 preprocessing.

LFW has no personal-colour ground truth. This script therefore reports
reproducible proxy metrics: prediction agreement, face-detection rate, and
median RGB-vector shift. The downloaded images stay ignored.
"""
from __future__ import annotations

import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image

import app

URL = "http://vis-www.cs.umass.edu/lfw/lfw.tgz"
ROOT = Path("evaluation-data")


def old_analyze(data: bytes) -> dict:
    image = Image.open(io.BytesIO(data)).convert("RGB")
    arr = np.asarray(image)
    gray = app.cv2.cvtColor(arr, app.cv2.COLOR_RGB2GRAY)
    cascade = app.cv2.CascadeClassifier(str(Path(app.cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(50, 50)) if not cascade.empty() else []
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        sample = arr[y + int(h*.18):y + int(h*.72), x + int(w*.18):x + int(w*.82)]
        found = True
    else:
        cy, cx = arr.shape[0]//2, arr.shape[1]//2; size = min(arr.shape[:2])//3
        sample = arr[cy-size:cy+size, cx-size:cx+size]; found = False
    hsv = app.cv2.cvtColor(sample, app.cv2.COLOR_RGB2HSV)
    rgb = sample.reshape(-1, 3).mean(axis=0); hue = float(np.median(hsv[..., 0])); sat = float(np.median(hsv[..., 1])); val = float(np.median(hsv[..., 2]))
    warm = (hue < 18 or hue > 165) and rgb[0] >= rgb[2] * .96
    contrast = val > 135 and (sat > 45 or float(rgb.max()-rgb.min()) > 48)
    kind = "spring-warm" if warm and not contrast else "autumn-warm" if warm else "winter-cool" if contrast else "summer-cool"
    return {"type": kind, "face": found, "rgb": rgb.tolist()}


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    archive = ROOT / "lfw.tgz"
    if not archive.exists(): urllib.request.urlretrieve(URL, archive)
    image_dir = ROOT / "images"
    image_dir.mkdir(exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name.lower().endswith(('.jpg', '.jpeg'))][:100]
        for member in members:
            target = image_dir / Path(member.name).name
            if not target.exists():
                target.write_bytes(tar.extractfile(member).read())
    files = sorted(image_dir.glob("*.jpg"))[:100]
    before, after = [], []
    for path in files:
        data = path.read_bytes(); before.append(old_analyze(data)); after.append(app.analyze(data))
    final_before, final_after = before[30:100], after[30:100]
    after_type = {"봄 웜톤": "spring-warm", "가을 웜톤": "autumn-warm", "겨울 쿨톤": "winter-cool", "여름 쿨톤": "summer-cool"}
    agreement = sum(a["type"] == after_type.get(b["type"], b["type"]) for a, b in zip(final_before, final_after)) / len(final_before)
    face_before = sum(a["face"] for a in final_before) / len(final_before)
    face_after = sum(a["face_detected"] for a in final_after) / len(final_after)
    rgb_shift = float(np.median([np.linalg.norm(np.array(a["rgb"]) - np.array(b["skin_rgb"])) for a, b in zip(final_before, final_after)]))
    result = {"source": "Labeled Faces in the Wild (LFW), public academic dataset", "total": len(files), "tuning": 30, "final": len(final_after), "metrics": {"prediction_consistency": round(agreement, 4), "face_detection_rate_before": round(face_before, 4), "face_detection_rate_after": round(face_after, 4), "median_rgb_shift": round(rgb_shift, 2)}, "status": "proxy-metrics-only-no-personal-colour-ground-truth"}
    (ROOT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__": main()
