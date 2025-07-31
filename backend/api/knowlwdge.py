from backend.core.state import doc_manager, indexer
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

@router.post("/upload")
async def upload_files(file: UploadFile = File(...)):
    doc_manager.save_uploaded_file(file)
    indexer.rebuild(doc_manager)
    return JSONResponse(content={"filename": file.filename, "message": "File uploaded and indexed successfully."})

@router.get("/list")
async def list_documents():
    docs = doc_manager.list_documents()
    return JSONResponse(content={"documents": docs})
