from fastapi import APIRouter, File, UploadFile

from app import settings

from ...common.upload import secure_save
from ...errors import ApiError

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)) -> dict:  # noqa: B008
    data = await file.read()
    ok, res = secure_save(settings.get_upload_dir(), data)
    if not ok:
        title, status, detail = {
            "too_big": ("Invalid upload", 400, "File too large"),
            "bad_type": ("Invalid upload", 400, "Unsupported file type"),
            "path_traversal": ("Invalid upload", 400, "Invalid path"),
            "symlink_parent": ("Invalid upload", 400, "Invalid storage path"),
        }.get(res, ("Bad Request", 400, "Bad request"))
        raise ApiError(status, title, detail)
    return {"stored_as": res}
