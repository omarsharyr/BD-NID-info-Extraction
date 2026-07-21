"""NID extraction endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import get_extraction_service
from app.models.responses import ExtractionResponse

router = APIRouter(prefix="/api/v1/nid", tags=["nid"])


@router.post("/extract", response_model=ExtractionResponse)
async def extract_nid(
    front_image: UploadFile | None = File(default=None),
    back_image: UploadFile | None = File(default=None),
    extraction_service=Depends(get_extraction_service),
) -> ExtractionResponse:
    return await extraction_service.extract(front_image, back_image)
