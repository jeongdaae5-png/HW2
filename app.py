from pathlib import Path
from typing import Any
import io
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

BASE_DIR = Path(__file__).parent
app = FastAPI(title="AI 퍼스널 컬러 진단")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
PALETTES = {
 "봄 웜톤": (["#F28B82","#F6BD60","#F7D488","#8FCB9B","#6EC6CA"],["#22223B","#BDBDBD"]),
 "여름 쿨톤": (["#E8AEB7","#B8C0FF","#A8DADC","#8E9AAF","#F1DCA7"],["#E76F51","#2A9D8F"]),
 "가을 웜톤": (["#C8553D","#D4A373","#A3B18A","#E09F3E","#6F4E37"],["#D8E2DC","#CDB4DB"]),
 "겨울 쿨톤": (["#D90429","#3A0CA3","#0077B6","#111111","#F8F9FA"],["#E9C46A","#A8DADC"]),
}
def analyze(data: bytes) -> dict[str, Any]:
    try: image = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc: raise ValueError("지원하지 않는 이미지 파일입니다.") from exc
    if image.width < 80 or image.height < 80: raise ValueError("이미지는 가로·세로 80px 이상이어야 합니다.")
    arr = np.asarray(image); bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR); gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # OpenCV 5 wheels may omit the legacy CascadeClassifier API. Keep the
    # detector optional: color analysis remains usable with a transparent
    # lower-confidence central-crop fallback in that environment.
    faces = []
    if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        if cascade_path.exists():
            cascade = cv2.CascadeClassifier(str(cascade_path))
            if not cascade.empty():
                faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(50, 50))
    if len(faces):
        x,y,w,h=max(faces,key=lambda f:f[2]*f[3]); px,py=int(w*.18),int(h*.18); sample=arr[max(0,y+py):min(arr.shape[0],y+int(h*.72)),max(0,x+px):min(arr.shape[1],x+w-px)]; found=True
    else:
        cy,cx=arr.shape[0]//2,arr.shape[1]//2; size=min(arr.shape[:2])//3; sample=arr[max(0,cy-size):cy+size,max(0,cx-size):cx+size]; found=False
    hsv=cv2.cvtColor(sample,cv2.COLOR_RGB2HSV); rgb=sample.reshape(-1,3).mean(axis=0); hue=float(np.median(hsv[...,0])); sat=float(np.median(hsv[...,1])); val=float(np.median(hsv[...,2]))
    warm=(hue<18 or hue>165) and rgb[0]>=rgb[2]*.96; contrast=val>135 and (sat>45 or float(rgb.max()-rgb.min())>48); key="봄 웜톤" if warm and not contrast else "가을 웜톤" if warm else "겨울 쿨톤" if contrast else "여름 쿨톤"; rec,worst=PALETTES[key]
    return {"type":key,"confidence":"중간" if found else "낮음","face_detected":found,"skin_rgb":[int(v) for v in rgb],"hsv":[round(hue,1),round(sat,1),round(val,1)],"recommended":[{"code":c,"name":"추천 컬러"} for c in rec],"avoid":[{"code":c,"name":"워스트 컬러"} for c in worst]}
@app.get("/")
def index(): return FileResponse(BASE_DIR/"static"/"index.html")
@app.post("/api/analyze")
async def api_analyze(file: UploadFile=File(...)):
    if not file.content_type or not file.content_type.startswith("image/"): return JSONResponse({"detail":"이미지 파일만 업로드할 수 있습니다."},status_code=415)
    data=await file.read()
    if len(data)>10*1024*1024: return JSONResponse({"detail":"파일 크기는 10MB 이하이어야 합니다."},status_code=413)
    try: return analyze(data)
    except ValueError as exc: return JSONResponse({"detail":str(exc)},status_code=400)
