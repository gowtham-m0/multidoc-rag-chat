from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from dotenv import load_dotenv

from multi_doc_chat.utils.document_ops import FastApiFileAdapter

load_dotenv()


from multi_doc_chat.model.models import ChatRequest, ChatResponse, UploadResponse
from multi_doc_chat.src.document_ingestion.data_ingestion import ChatIngestor
from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG
from langchain_core.messages import HumanMessage, AIMessage
from multi_doc_chat.exceptions.custom_exception import DocumentPortalException

app = FastAPI(title="MultiDocChat", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
app.mount("/static",StaticFiles(directory=static_dir),name="static")
templates = Jinja2Templates(directory=templates_dir)

SESSIONS: Dict[str, List[dict]]  = {}

@app.get("/health")
def health() -> Dict[str,str]:
    return {"status" : "ok"}

@app.get("/",response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_model=UploadResponse)
async def upload_file(files: List[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    try:
        
        wrapped_files = [FastApiFileAdapter(f) for f in files]
        
        ingestor = ChatIngestor(use_session_dirs=True)
        session_id = ingestor.session_id
        
        ingestor.build_text_retriever(uploaded_files = wrapped_files)
        
        SESSIONS[session_id]  = []
        
        return UploadResponse(session_id=session_id, indexed=True, message="Indexing Completed")
    
    except DocumentPortalException as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(req:ChatRequest) -> ChatResponse:
    session_id = req.session_id
    message = req.message.strip()
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=400, detail="Invalid or expired session ID.")
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        
        rag = ConversationalRAG(session_id=session_id)
        index_path = f"faiss_index/{session_id}"
        rag.load_retriever_from_faiss(index_path=index_path)
        
        simple = SESSIONS.get(session_id,[])
        lc_hisotry = []
        for m in simple:
            role = m.get("role")
            content = m.get("content","")
            if role == "user":
                lc_hisotry.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_hisotry.append(AIMessage(content=content))
            
        answer = rag.invoke(message, lc_hisotry)
        
        simple.append({"role":"user","content":message})
        simple.append({"role":"assistant","content":answer})
        SESSIONS[session_id] = simple
        
        return ChatResponse(message=answer)

    except DocumentPortalException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
