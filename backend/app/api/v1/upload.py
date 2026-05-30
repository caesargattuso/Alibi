from fastapi import APIRouter, Depends, UploadFile, File

from app.api.deps import get_current_user
from app.models.models import User
from app.services.file_service import file_service

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
    result = await file_service.upload_image(file)
    return {"code": 200, "data": result}


@router.post("/audio")
async def upload_audio(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
    result = await file_service.upload_audio(file)
    return {"code": 200, "data": result}
