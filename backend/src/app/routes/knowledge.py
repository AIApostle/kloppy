"""Workspace knowledge and document-source routes."""

from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pypdf import PdfReader

from ..schemas.knowledge import KnowledgeSource, KnowledgeSourceCreate
from ..services.brand_knowledge import create_source, delete_source, list_sources
from ..services.user_settings import SettingsAuthenticationError, SettingsStoreError

router = APIRouter(prefix="/knowledge/sources", tags=["knowledge"])
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def _token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required.")
    return authorization[7:].strip()


def _raise(error: Exception) -> None:
    if isinstance(error, SettingsAuthenticationError):
        raise HTTPException(status_code=401, detail=str(error)) from error
    if isinstance(error, SettingsStoreError):
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("", response_model=list[KnowledgeSource])
def get_sources(authorization: str | None = Header(default=None)) -> list[KnowledgeSource]:
    try:
        return [KnowledgeSource(**item) for item in list_sources(_token(authorization))]
    except (SettingsAuthenticationError, SettingsStoreError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.post("", response_model=KnowledgeSource, status_code=201)
def add_brand_text(payload: KnowledgeSourceCreate, authorization: str | None = Header(default=None)) -> KnowledgeSource:
    try:
        row = create_source(_token(authorization), {**payload.model_dump(), "title": payload.title.strip()})
        return KnowledgeSource(**row)
    except (SettingsAuthenticationError, SettingsStoreError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.post("/document", response_model=KnowledgeSource, status_code=201)
async def upload_document(
    authorization: str | None = Header(default=None),
    file: UploadFile = File(...),
) -> KnowledgeSource:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".docx"}:
        raise HTTPException(status_code=415, detail="Upload a TXT, Markdown, PDF, or DOCX document.")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Documents must be 8 MB or smaller.")
    try:
        if suffix == ".pdf":
            content = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
        elif suffix == ".docx":
            content = "\n".join(paragraph.text for paragraph in Document(BytesIO(raw)).paragraphs)
        else:
            content = raw.decode("utf-8-sig")
    except Exception as error:
        raise HTTPException(status_code=422, detail="Kloppy could not read this document. Check that the file is valid and contains text.") from error
    content = content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="This document contains no extractable text.")
    if len(content) > 100_000:
        raise HTTPException(status_code=413, detail="Extracted text is over the 100,000 character limit.")
    try:
        row = create_source(
            _token(authorization),
            {"title": (file.filename or "Uploaded document")[:200], "content": content,
             "source_type": "document", "file_name": (file.filename or "document")[:255]},
        )
        return KnowledgeSource(**row)
    except (SettingsAuthenticationError, SettingsStoreError) as error:
        _raise(error)
        raise AssertionError("unreachable")


@router.delete("/{source_id}", status_code=204)
def remove_source(source_id: str, authorization: str | None = Header(default=None)) -> None:
    try:
        delete_source(_token(authorization), source_id)
    except (SettingsAuthenticationError, SettingsStoreError) as error:
        _raise(error)
