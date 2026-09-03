import base64
import uuid
import httpx
from app.core.config import get_settings


settings = get_settings()


def _get_github_headers() -> dict:
    return {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_upload_url(filename: str) -> str:
    return (
        f"https://api.github.com/repos/"
        f"{settings.github_repo_owner}/{settings.github_repo_name}"
        f"/contents/products/{filename}"
    )


def _get_raw_url(filename: str) -> str:
    return (
        f"https://raw.githubusercontent.com/"
        f"{settings.github_repo_owner}/{settings.github_repo_name}"
        f"/{settings.github_branch}/products/{filename}"
    )


def upload_image_to_github(file_bytes: bytes, original_filename: str) -> str:
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "jpg"
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    content_b64 = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "message": f"Add product image: {unique_name}",
        "content": content_b64,
        "branch": settings.github_branch,
    }

    with httpx.Client(timeout=30) as client:
        response = client.put(
            _get_upload_url(unique_name),
            json=payload,
            headers=_get_github_headers(),
        )
        response.raise_for_status()

    return _get_raw_url(unique_name)


def delete_image_from_github(filename: str) -> bool:
    api_url = _get_upload_url(filename)

    with httpx.Client(timeout=30) as client:
        get_resp = client.get(api_url, headers=_get_github_headers())
        if get_resp.status_code != 200:
            return False
        sha = get_resp.json().get("sha")

        payload = {
            "message": f"Delete product image: {filename}",
            "sha": sha,
            "branch": settings.github_branch,
        }
        del_resp = client.delete(api_url, json=payload, headers=_get_github_headers())
        return del_resp.status_code == 200
