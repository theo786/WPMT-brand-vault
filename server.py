"""WPMT Brand Vault — 로컬 파일 서버 (Google Drive 대체)"""
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

SAVE_DIR = Path.home() / "GoogleDrive" / "WPMT-Brand-Vault"
META_FILE = SAVE_DIR / ".metadata.json"

app = FastAPI()

def load_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text())
        except Exception:
            pass
    return {}

def save_meta(meta: dict):
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

def meta_to_file_obj(file_id: str, m: dict) -> dict:
    return {
        "id": file_id,
        "name": m["name"],
        "mimeType": m["mimeType"],
        "thumbnailLink": f"/api/files/{file_id}/media",
        "webViewLink": f"/api/files/{file_id}/media",
        "createdTime": m["createdTime"],
    }

@app.on_event("startup")
def startup():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    ext = Path(file.filename).suffix
    save_path = SAVE_DIR / f"{file_id}{ext}"
    content = await file.read()
    save_path.write_bytes(content)

    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    meta = load_meta()
    meta[file_id] = {
        "name": file.filename,
        "mimeType": mime,
        "ext": ext,
        "createdTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
    }
    save_meta(meta)
    return meta_to_file_obj(file_id, meta[file_id])

@app.get("/api/files")
def list_files():
    meta = load_meta()
    files = [meta_to_file_obj(fid, m) for fid, m in meta.items()
             if (SAVE_DIR / f"{fid}{m['ext']}").exists()]
    files.sort(key=lambda x: x["createdTime"], reverse=True)
    return {"files": files}

@app.delete("/api/files/{file_id}")
def delete_file(file_id: str):
    meta = load_meta()
    if file_id not in meta:
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    ext = meta[file_id]["ext"]
    path = SAVE_DIR / f"{file_id}{ext}"
    if path.exists():
        path.unlink()
    del meta[file_id]
    save_meta(meta)
    return {"ok": True}

@app.get("/api/files/{file_id}/media")
def serve_file(file_id: str):
    meta = load_meta()
    if file_id not in meta:
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    m = meta[file_id]
    path = SAVE_DIR / f"{file_id}{m['ext']}"
    if not path.exists():
        raise HTTPException(404, "파일이 없습니다.")
    return FileResponse(path, media_type=m["mimeType"])

@app.get("/api/ping")
def ping():
    return {"ok": True}

# 정적 파일 맨 마지막에
app.mount("/", StaticFiles(directory=".", html=True), name="static")
