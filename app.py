from pathlib import Path
from typing import Any
import io
import os
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

BASE_DIR = Path(__file__).parent
app = FastAPI(title="AI 퍼스널 컬러 진단")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v2")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
PALETTES = {
 "봄 웜톤": (["#F28B82","#F6BD60","#F7D488","#8FCB9B","#6EC6CA"],["#22223B","#BDBDBD"]),
 "여름 쿨톤": (["#E8AEB7","#B8C0FF","#A8DADC","#8E9AAF","#F1DCA7"],["#E76F51","#2A9D8F"]),
 "가을 웜톤": (["#C8553D","#D4A373","#A3B18A","#E09F3E","#6F4E37"],["#D8E2DC","#CDB4DB"]),
 "겨울 쿨톤": (["#D90429","#3A0CA3","#0077B6","#111111","#F8F9FA"],["#E9C46A","#A8DADC"]),
}
def _face_sample(arr: np.ndarray, gray: np.ndarray) -> tuple[np.ndarray, bool]:
    """Return a conservative skin candidate region and whether a face was found."""
    faces = []
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    if cascade_path.exists():
        cascade = cv2.CascadeClassifier(str(cascade_path))
        if not cascade.empty():
            # Equalize luminance before detection so backlit images remain detectable.
            detection_gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
            faces = cascade.detectMultiScale(detection_gray, 1.08, 5, minSize=(50, 50))
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        # Cheeks/forehead are less affected by eyes, lips and hair than the full box.
        left, right = x + int(w * .16), x + int(w * .84)
        top, bottom = y + int(h * .25), y + int(h * .72)
        return arr[max(0, top):min(arr.shape[0], bottom), max(0, left):min(arr.shape[1], right)], True
    cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
    size = max(min(arr.shape[:2]) // 4, 20)
    return arr[max(0, cy-size):cy+size, max(0, cx-size):cx+size], False


def _correct_and_extract(sample: np.ndarray) -> tuple[np.ndarray, float, float, float]:
    """Apply gray-world correction and reject non-skin pixels using HSV/YCrCb."""
    pixels = sample.reshape(-1, 3).astype(np.float32)
    gains = pixels.mean(axis=0).mean() / np.maximum(pixels.mean(axis=0), 1.0)
    corrected = np.clip(sample.astype(np.float32) * gains, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(corrected, cv2.COLOR_RGB2HSV)
    ycrcb = cv2.cvtColor(corrected, cv2.COLOR_RGB2YCrCb)
    # Broad skin bounds, then robust medians prevent a few red/brown pixels dominating.
    mask = ((hsv[..., 0] <= 25) | (hsv[..., 0] >= 165)) & (hsv[..., 1] >= 18) & (hsv[..., 1] <= 190)
    mask &= (ycrcb[..., 1] >= 130) & (ycrcb[..., 1] <= 185) & (ycrcb[..., 2] >= 75) & (ycrcb[..., 2] <= 145)
    selected = corrected[mask]
    if selected.shape[0] < max(20, corrected.shape[0] * corrected.shape[1] // 100):
        selected = corrected.reshape(-1, 3)
    rgb = np.median(selected, axis=0)
    selected_hsv = cv2.cvtColor(selected.reshape(-1, 1, 3), cv2.COLOR_RGB2HSV).reshape(-1, 3)
    return selected, float(np.median(selected_hsv[:, 0])), float(np.median(selected_hsv[:, 1])), float(np.median(selected_hsv[:, 2]))


def analyze(data: bytes) -> dict[str, Any]:
    try: image = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc: raise ValueError("지원하지 않는 이미지 파일입니다.") from exc
    if image.width < 80 or image.height < 80: raise ValueError("이미지는 가로·세로 80px 이상이어야 합니다.")
    arr = np.asarray(image); gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    sample, found = _face_sample(arr, gray)
    selected, hue, sat, val = _correct_and_extract(sample)
    rgb = np.median(selected, axis=0)
    warm = (hue < 24 or hue > 165) and rgb[0] >= rgb[2] * .98
    contrast = val > 138 and (sat > 42 or float(rgb.max() - rgb.min()) > 45)
    key = "봄 웜톤" if warm and not contrast else "가을 웜톤" if warm else "겨울 쿨톤" if contrast else "여름 쿨톤"
    rec, worst = PALETTES[key]
    return {"model_version": MODEL_VERSION, "type": key, "confidence": "중간" if found else "낮음", "face_detected": found, "skin_rgb": [int(v) for v in rgb], "hsv": [round(hue, 1), round(sat, 1), round(val, 1)], "preprocessing": "face-roi+gray-world+skin-mask", "recommended": [{"code": c, "name": "추천 컬러"} for c in rec], "avoid": [{"code": c, "name": "워스트 컬러"} for c in worst]}
@app.get("/")
def index(): return FileResponse(BASE_DIR/"static"/"index.html")
@app.post("/api/analyze")
async def api_analyze(file: UploadFile=File(...)):
    if not file.content_type or not file.content_type.startswith("image/"): return JSONResponse({"detail":"이미지 파일만 업로드할 수 있습니다."},status_code=415)
    data=await file.read()
    if len(data)>10*1024*1024: return JSONResponse({"detail":"파일 크기는 10MB 이하이어야 합니다."},status_code=413)
    try: return analyze(data)
    except ValueError as exc: return JSONResponse({"detail":str(exc)},status_code=400)
