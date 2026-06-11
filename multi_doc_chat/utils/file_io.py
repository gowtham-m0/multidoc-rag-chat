from __future__ import annotations
import re
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Iterable, List
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from multi_doc_chat.exceptions.custom_exception import DocumentPortalException

SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.md', '.html', '.json', '.csv', '.xlsx', '.pptx', '.xml', '.yaml', '.yml', '.log', '.tex', '.rtf', '.odt', '.ods', '.odp'}


def save_uploaded_files(uploaded_files: Iterable, target_dir: Path) -> List[Path]:
    
    """
        Save uploaded files (Streamlit-like) and return local paths.
    """
    
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        saved: List[Path] = []
        
        for uf in uploaded_files:
            name = getattr(uf, "name", "file")
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                log.warning("Unsupported file type skipped", filename=name, extension=ext)
                continue
            
            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(name).stem).lower()
            fname = f"{safe_name}_{uuid.uuid4().hex[:6]}{ext}"
            fname = f"{uuid.uuid4().hex[:8]}{ext}"
            out = target_dir / fname
            with open(out, "wb") as f:
                if hasattr(uf, "read"):
                    f.write(uf.read())
                else:
                    f.write(uf.getbuffer())
            saved.append(out)
            log.info("File saved", filename=name, saved_path=str(out))
        return saved
    except Exception as e:
        log.error("Error saving uploaded files", error=str(e))
        raise DocumentPortalException(f"Failed to save uploaded files: {str(e)}") from e