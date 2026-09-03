from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.dependencies import require_admin
from app.services.github_storage import upload_image_to_github

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user: dict = Depends(require_admin),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="نوع الملف غير مدعوم. يُسمح فقط بـ: jpg, png, webp, gif",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="حجم الملف يتجاوز 5 ميغابايت",
        )

    try:
        image_url = upload_image_to_github(file_bytes, file.filename or "image.jpg")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"فشل رفع الصورة إلى GitHub: {str(e)}",
        )

    return {"image_url": image_url}
