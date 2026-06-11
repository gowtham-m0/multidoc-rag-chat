from __future__ import annotations
from pathlib import Path
from typing import Iterable, List
from fastapi import UploadFile
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, Docx2txtLoader, PyPDFLoader
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from multi_doc_chat.exceptions.custom_exception import DocumentPortalException


SUPPORTED_EXTENSIONS  = {".pdf", ".docx", ".txt"}

def load_documents(paths: Iterable[Path]) -> List[Document]:
    """Load docs using appropriate loader based on extension."""
    
    docs: List[Document] = []
    try:
        for p in paths:
            ext = p.suffix.lower()
            if ext == ".pdf":
                loader = PyPDFLoader(str(p))
            elif ext == ".docx":
                loader = Docx2txtLoader(str(p))
            elif ext == ".txt":
                loader = TextLoader(str(p))
            else:
                log.warning("Unsupported file type skipped", filename=str(p), extension=ext)
                continue
            docs.extend(loader.load())
        log.info("Unsupported file types skipped", num_skipped=len(paths) - len(docs), total_files=len(paths))
        return docs
    except Exception as e:
        log.error("Error loading documents", error=str(e))
        raise DocumentPortalException(f"Failed to load documents: {str(e)}") from e
    

class FastApiFileAdapter:
    """Adapt FastAPI UploadFile to a simple object with .name and .getbuffer()."""
    def __init__(self,uf:UploadFile):
        self._uf = uf
        self.name = uf.filename or "file"
        
    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()